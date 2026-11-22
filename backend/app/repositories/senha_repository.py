from sqlalchemy import update
from app import db
from app.models.senha import Senha
from app.models.historico import HistoricoEstado
from app.models.fila import Fila


class SenhaRepository:
    @staticmethod
    def buscar_por_id(senha_id):
        return db.session.get(Senha, senha_id)

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
    def buscar_ultima_chamada_do_dia(prefixo_data):
        return (
            Senha.query
            .join(HistoricoEstado, HistoricoEstado.senha_id == Senha.id)
            .filter(
                Senha.numero.like(f"{prefixo_data}%"),
                HistoricoEstado.estado == "CHAMADA"
            )
            .order_by(HistoricoEstado.id.desc())
            .first()
        )

    @staticmethod
    def buscar_proxima_aguardando(tipo, prefixo_data):
        return (
            Senha.query
            .filter(
                Senha.tipo == tipo,
                Senha.estado_atual == "AGUARDANDO",
                Senha.numero.like(f"{prefixo_data}%")
            )
            .order_by(Senha.id.asc())
            .first()
        )

    @staticmethod
    def marcar_como_chamada(senha, usuario_id, guiche=None):
        return SenhaRepository.atualizar_estado_com_historico(
            senha_id=senha.id,
            versao_lida=senha.versao,
            estado_lido="AGUARDANDO",
            novo_estado="CHAMADA",
            usuario_id=usuario_id,
            guiche=guiche
        )

    @staticmethod
    def criar_com_historico(senha):
        db.session.add(senha)
        db.session.flush()

        historico_inicial = HistoricoEstado(
            senha_id=senha.id,
            estado=senha.estado_atual,
            usuario_id=None
        )
        db.session.add(historico_inicial)
        db.session.commit()
        return senha

    @staticmethod
    def atualizar_estado_com_historico(senha_id, versao_lida, estado_lido, novo_estado, usuario_id, guiche=None):
        valores = {
            "estado_atual": novo_estado,
            "usuario_id": usuario_id,
            "versao": versao_lida + 1
        }
        if guiche is not None:
            valores["guiche"] = guiche

        resultado = db.session.execute(
            update(Senha)
            .where(
                Senha.id == senha_id,
                Senha.versao == versao_lida,
                Senha.estado_atual == estado_lido
            )
            .values(**valores)
        )

        if resultado.rowcount == 0:
            db.session.rollback()
            return False

        db.session.add(HistoricoEstado(
            senha_id=senha_id,
            estado=novo_estado,
            usuario_id=usuario_id
        ))
        db.session.commit()
        return True

    @staticmethod
    def listar_aguardando_do_dia(prefixo_data):
        return (
            Senha.query
            .filter(
                Senha.estado_atual == "AGUARDANDO",
                Senha.numero.like(f"{prefixo_data}%")
            )
            .order_by(Senha.id.asc())
            .all()
        )

    @staticmethod
    def listar_em_andamento_do_dia(prefixo_data):
        return (
            Senha.query
            .filter(
                Senha.estado_atual.in_(["CHAMADA", "CHAMADA_NOVAMENTE", "EM_ATENDIMENTO"]),
                Senha.numero.like(f"{prefixo_data}%")
            )
            .order_by(Senha.id.desc())
            .all()
        )

    @staticmethod
    def listar_ultimas_chamadas_do_dia(prefixo_data, limite=6):
        return (
            db.session.query(HistoricoEstado, Senha)
            .join(Senha, HistoricoEstado.senha_id == Senha.id)
            .filter(
                Senha.numero.like(f"{prefixo_data}%"),
                HistoricoEstado.estado.in_(["CHAMADA", "CHAMADA_NOVAMENTE"])
            )
            .order_by(HistoricoEstado.id.desc())
            .limit(limite)
            .all()
        )