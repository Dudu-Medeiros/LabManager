from datetime import datetime, timezone, timedelta
from app.models.senha import Senha
from app.repositories.senha_repository import SenhaRepository

TIPOS_VALIDOS = {"SP", "SE", "SG"}
FUSO_BR = timezone(timedelta(hours=-3))

class SenhaService:
    @staticmethod
    def emitir_senha(tipo, paciente_id=None):
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

        return {
            "id": nova_senha.id,
            "numero": nova_senha.numero,
            "tipo": nova_senha.tipo,
            "estado_atual": nova_senha.estado_atual,
            "data_emissao": nova_senha.data_emissao.isoformat(),
            "fila_id": nova_senha.fila_id,
            "paciente_id": nova_senha.paciente_id
        }, None