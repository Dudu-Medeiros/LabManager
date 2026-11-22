import os
from datetime import datetime, timezone, timedelta
from flask import current_app, has_app_context
from app.models.senha import Senha
from app.repositories.senha_repository import SenhaRepository
from app.services.maquina_estados import validar_transicao

TIPOS_VALIDOS = {"SP", "SE", "SG"}
FUSO_BR = timezone(timedelta(hours=-3))
MAX_TENTATIVAS_CHAMADA = 5


def ordem_de_busca(ultimo_tipo_chamado):
    if ultimo_tipo_chamado == "SP":
        return ["SE", "SG", "SP"]
    return ["SP", "SE", "SG"]


def obter_config_expediente():
    inicio = int(os.getenv("EXPEDIENTE_INICIO", "7"))
    fim = int(os.getenv("EXPEDIENTE_FIM", "17"))

    if has_app_context():
        if "EXPEDIENTE_INICIO" in current_app.config:
            inicio = int(current_app.config["EXPEDIENTE_INICIO"])
        if "EXPEDIENTE_FIM" in current_app.config:
            fim = int(current_app.config["EXPEDIENTE_FIM"])
        if "VALIDAR_EXPEDIENTE" in current_app.config:
            validar = bool(current_app.config["VALIDAR_EXPEDIENTE"])
            return inicio, fim, validar
        if current_app.config.get("TESTING"):
            return inicio, fim, False

    validar_env = os.getenv("VALIDAR_EXPEDIENTE", "true").strip().lower()
    validar = validar_env in {"1", "true", "sim", "yes"}
    return inicio, fim, validar


def esta_no_expediente(agora=None):
    inicio, fim, validar = obter_config_expediente()
    if not validar:
        return True
    referencia = agora or datetime.now(FUSO_BR)
    return inicio <= referencia.hour < fim


def apos_expediente(agora=None):
    _, fim, validar = obter_config_expediente()
    if not validar:
        return False
    referencia = agora or datetime.now(FUSO_BR)
    return referencia.hour >= fim


class SenhaService:
    @staticmethod
    def _serializar(senha, incluir_historico=False):
        dados = {
            "id": senha.id,
            "numero": senha.numero,
            "tipo": senha.tipo,
            "estado_atual": senha.estado_atual,
            "data_emissao": senha.data_emissao.isoformat(),
            "guiche": senha.guiche,
            "versao": senha.versao,
            "usuario_id": senha.usuario_id,
            "fila_id": senha.fila_id,
            "paciente_id": senha.paciente_id
        }

        if incluir_historico:
            dados["historico"] = [
                {
                    "id": h.id,
                    "estado": h.estado,
                    "data_hora": h.data_hora.isoformat(),
                    "usuario_id": h.usuario_id
                }
                for h in senha.historico
            ]

        return dados

    @staticmethod
    def status_expediente(agora=None):
        inicio, fim, validar = obter_config_expediente()
        referencia = agora or datetime.now(FUSO_BR)
        aberto = (inicio <= referencia.hour < fim) if validar else True
        return {
            "aberto": aberto,
            "inicio": f"{inicio:02d}:00",
            "fim": f"{fim:02d}:00",
            "validacao_ativa": validar,
            "hora_atual": referencia.strftime("%H:%M")
        }

    @staticmethod
    def encerrar_expediente(usuario_id=None):
        prefixo_data = datetime.now(FUSO_BR).strftime("%y%m%d") + "-"
        descartadas = SenhaRepository.descartar_pendentes_do_dia(prefixo_data, usuario_id=usuario_id)
        return {
            "descartadas": len(descartadas),
            "senhas_descartadas": descartadas,
            "mensagem": f"{len(descartadas)} senha(s) restante(s) descartada(s) no encerramento do expediente."
        }

    @staticmethod
    def emitir_senha(tipo, paciente_id=None, entrar_fila=False):
        agora = datetime.now(FUSO_BR)
        data_hoje = agora.strftime("%y%m%d")

        if not esta_no_expediente(agora):
            if apos_expediente(agora):
                SenhaRepository.descartar_pendentes_do_dia(f"{data_hoje}-")
            inicio, fim, _ = obter_config_expediente()
            return None, f"Fora do horário de expediente ({inicio:02d}h às {fim:02d}h). Emissão de senhas indisponível."

        tipo_normalizado = tipo.strip().upper() if isinstance(tipo, str) else ""

        if tipo_normalizado not in TIPOS_VALIDOS:
            return None, "Tipo de senha inválido. Use SP (Prioritária), SE (Exames) ou SG (Geral)."

        prefixo = f"{data_hoje}-{tipo_normalizado}"

        ultima_senha = SenhaRepository.buscar_ultima_por_prefixo(prefixo)
        if ultima_senha:
            ultimo_sequencial = int(ultima_senha.numero.replace(prefixo, ""))
            proximo_sequencial = ultimo_sequencial + 1
        else:
            proximo_sequencial = 1

        numero_formatado = f"{prefixo}{proximo_sequencial:03d}"
        fila = SenhaRepository.buscar_fila_por_sigla(tipo_normalizado)

        nova_senha = Senha(
            numero=numero_formatado,
            tipo=tipo_normalizado,
            estado_atual="EMITIDA",
            paciente_id=paciente_id,
            fila_id=fila.id if fila else None
        )

        SenhaRepository.criar_com_historico(nova_senha)

        if entrar_fila:
            SenhaRepository.atualizar_estado_com_historico(
                senha_id=nova_senha.id,
                versao_lida=nova_senha.versao,
                estado_lido="EMITIDA",
                novo_estado="AGUARDANDO",
                usuario_id=None
            )
            nova_senha = SenhaRepository.buscar_por_id(nova_senha.id)

        return SenhaService._serializar(nova_senha), None

    @staticmethod
    def buscar_por_id(senha_id):
        senha = SenhaRepository.buscar_por_id(senha_id)
        if not senha:
            return None, "Senha não encontrada."
        return SenhaService._serializar(senha, incluir_historico=True), None

    @staticmethod
    def chamar_proxima(usuario_id, guiche=None):
        agora = datetime.now(FUSO_BR)
        prefixo_data = agora.strftime("%y%m%d") + "-"

        if not esta_no_expediente(agora):
            if apos_expediente(agora):
                SenhaRepository.descartar_pendentes_do_dia(prefixo_data, usuario_id=usuario_id)
            inicio, fim, _ = obter_config_expediente()
            return None, f"Fora do horário de expediente ({inicio:02d}h às {fim:02d}h). Novas chamadas não são permitidas.", 403

        for _ in range(MAX_TENTATIVAS_CHAMADA):
            ultima_chamada = SenhaRepository.buscar_ultima_chamada_do_dia(prefixo_data)
            ordem = ordem_de_busca(ultima_chamada.tipo if ultima_chamada else None)

            candidata = None
            for tipo in ordem:
                candidata = SenhaRepository.buscar_proxima_aguardando(tipo, prefixo_data)
                if candidata:
                    break

            if not candidata:
                return None, "Não há senhas aguardando atendimento.", 404

            if SenhaRepository.marcar_como_chamada(candidata, usuario_id, guiche):
                senha = SenhaRepository.buscar_por_id(candidata.id)
                return SenhaService._serializar(senha, incluir_historico=True), None, 200

        return None, "Não foi possível chamar a próxima senha. Tente novamente.", 409

    @staticmethod
    def transicionar_estado(senha_id, novo_estado, usuario_id, guiche=None):
        senha = SenhaRepository.buscar_por_id(senha_id)
        if not senha:
            return None, "Senha não encontrada.", 404

        if not novo_estado:
            return None, "Informe o campo 'estado' para realizar a transição.", 400

        versao_lida = senha.versao
        estado_lido = senha.estado_atual

        valido, estado_normalizado, erro = validar_transicao(estado_lido, novo_estado)
        if not valido:
            return None, erro, 422

        gravou = SenhaRepository.atualizar_estado_com_historico(
            senha_id=senha.id,
            versao_lida=versao_lida,
            estado_lido=estado_lido,
            novo_estado=estado_normalizado,
            usuario_id=usuario_id,
            guiche=guiche
        )
        if not gravou:
            return None, "Conflito: a senha foi alterada por outro atendente. Atualize e tente novamente.", 409

        senha_atualizada = SenhaRepository.buscar_por_id(senha.id)
        return SenhaService._serializar(senha_atualizada, incluir_historico=True), None, 200

    @staticmethod
    def obter_painel():
        agora = datetime.now(FUSO_BR)
        prefixo_data = agora.strftime("%y%m%d") + "-"

        if apos_expediente(agora):
            SenhaRepository.descartar_pendentes_do_dia(prefixo_data)

        eventos = SenhaRepository.listar_ultimas_chamadas_do_dia(prefixo_data, limite=30)
        aguardando = SenhaRepository.listar_aguardando_do_dia(prefixo_data)

        chamadas = []
        vistas = set()
        for historico, senha in eventos:
            if senha.id in vistas:
                continue
            vistas.add(senha.id)

            sufixo = senha.numero.split("-")[-1]
            sequencial = sufixo[2:] if len(sufixo) > 2 else sufixo

            chamadas.append({
                "evento_id": historico.id,
                "senha_id": senha.id,
                "numero": senha.numero,
                "tipo": senha.tipo,
                "prioridade": senha.tipo,
                "sequencial": sequencial,
                "guiche": senha.guiche or "-",
                "estado_evento": historico.estado,
                "estado_atual": senha.estado_atual,
                "ultima_chamada": historico.estado == "CHAMADA_NOVAMENTE",
                "data_hora": historico.data_hora.isoformat()
            })

            if len(chamadas) == 6:
                break

        resumo = {"SP": 0, "SE": 0, "SG": 0, "total": len(aguardando)}
        for senha in aguardando:
            if senha.tipo in resumo:
                resumo[senha.tipo] += 1

        return {
            "chamada_atual": chamadas[0] if chamadas else None,
            "ultimas_chamadas": chamadas,
            "aguardando": resumo,
            "expediente": SenhaService.status_expediente(agora)
        }

    @staticmethod
    def obter_fila_atendimento():
        prefixo_data = datetime.now(FUSO_BR).strftime("%y%m%d") + "-"
        aguardando = SenhaRepository.listar_aguardando_do_dia(prefixo_data)
        em_andamento = SenhaRepository.listar_em_andamento_do_dia(prefixo_data)

        return {
            "aguardando": [SenhaService._serializar(s) for s in aguardando],
            "em_andamento": [SenhaService._serializar(s, incluir_historico=True) for s in em_andamento],
            "expediente": SenhaService.status_expediente()
        }