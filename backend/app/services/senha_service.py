from datetime import datetime, timezone, timedelta
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
    def emitir_senha(tipo, paciente_id=None, entrar_fila=False):
        tipo_normalizado = tipo.strip().upper() if isinstance(tipo, str) else ""

        if tipo_normalizado not in TIPOS_VALIDOS:
            return None, "Tipo de senha inválido. Use SP (Prioritária), SE (Exames) ou SG (Geral)."

        data_hoje = datetime.now(FUSO_BR).strftime("%y%m%d")
        prefixo = f"{data_hoje}-{tipo_normalizado}"

        ultima_senha = SenhaRepository.buscar_ultima_por_prefixo(prefixo)
        if ultima_senha:
            ultimo_sequencial = int(ultima_senha.numero.replace(prefixo, ""))
            proximo_sequencial = ultimo_sequencial + 1
        else:
            proximo_sequencial = 1

        numero_formatado = f"{prefixo}{proximo_sequencial:02d}"
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
        prefixo_data = datetime.now(FUSO_BR).strftime("%y%m%d") + "-"

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
        prefixo_data = datetime.now(FUSO_BR).strftime("%y%m%d") + "-"
        eventos = SenhaRepository.listar_ultimas_chamadas_do_dia(prefixo_data, limite=6)
        aguardando = SenhaRepository.listar_aguardando_do_dia(prefixo_data)

        chamadas = [
            {
                "evento_id": historico.id,
                "senha_id": senha.id,
                "numero": senha.numero,
                "tipo": senha.tipo,
                "guiche": senha.guiche or "-",
                "estado_evento": historico.estado,
                "estado_atual": senha.estado_atual,
                "data_hora": historico.data_hora.isoformat()
            }
            for historico, senha in eventos
        ]

        resumo = {"SP": 0, "SE": 0, "SG": 0, "total": len(aguardando)}
        for senha in aguardando:
            if senha.tipo in resumo:
                resumo[senha.tipo] += 1

        return {
            "chamada_atual": chamadas[0] if chamadas else None,
            "ultimas_chamadas": chamadas,
            "aguardando": resumo
        }

    @staticmethod
    def obter_fila_atendimento():
        prefixo_data = datetime.now(FUSO_BR).strftime("%y%m%d") + "-"
        aguardando = SenhaRepository.listar_aguardando_do_dia(prefixo_data)
        em_andamento = SenhaRepository.listar_em_andamento_do_dia(prefixo_data)

        return {
            "aguardando": [SenhaService._serializar(s) for s in aguardando],
            "em_andamento": [SenhaService._serializar(s, incluir_historico=True) for s in em_andamento]
        }