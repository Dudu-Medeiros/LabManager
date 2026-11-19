from app import db
from app.models.senha import Senha
from app.models.historico import HistoricoEstado
from app.models.fila import Fila

class SenhaRepository:
    @staticmethod
    def buscar_ultima_por_prefixo(prefixo):
        return (
            Senha.query
            .filter(Senha.numero.like(f"{prefixo}%"))
            .order_by(Senha.id.desc())
            .first()
        )

    @staticmethod
    def buscar_fila_por_sigla(sigla):
        return Fila.query.filter_by(sigla=sigla).first()

    @staticmethod
    def criar_com_historico(senha):
        db.session.add(senha)
        # flush gera o senha.id antes do commit para vincular ao historico
        db.session.flush()

        historico_inicial = HistoricoEstado(
            senha_id=senha.id,
            estado=senha.estado_atual,
            usuario_id=None
        )
        db.session.add(historico_inicial)
        db.session.commit()
        return senha