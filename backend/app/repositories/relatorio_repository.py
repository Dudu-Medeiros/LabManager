from sqlalchemy import func, select
from app import db
from app.models.senha import Senha
from app.models.historico import HistoricoEstado
from app.models.usuario import Usuario


class RelatorioRepository:
    @staticmethod
    def listar_senhas_por_prefixo(prefixo):
        consulta = (
            select(Senha.numero, Senha.tipo, Senha.estado_atual)
            .where(Senha.numero.like(f"{prefixo}%"))
        )
        return db.session.execute(consulta).all()

    @staticmethod
    def listar_detalhes_senhas_por_prefixo(prefixo):
        consulta = (
            select(
                Senha.id,
                Senha.numero,
                Senha.tipo,
                Senha.estado_atual,
                Senha.data_emissao,
                Senha.guiche,
                Senha.usuario_id,
                Usuario.nome.label("usuario_nome")
            )
            .select_from(Senha)
            .outerjoin(Usuario, Usuario.id == Senha.usuario_id)
            .where(Senha.numero.like(f"{prefixo}%"))
            .order_by(Senha.id.asc())
        )
        return db.session.execute(consulta).all()

    @staticmethod
    def listar_marcos_por_prefixo(prefixo, estados):
        consulta = (
            select(HistoricoEstado.senha_id, Senha.tipo, HistoricoEstado.estado, HistoricoEstado.data_hora)
            .join(Senha, Senha.id == HistoricoEstado.senha_id)
            .where(Senha.numero.like(f"{prefixo}%"), HistoricoEstado.estado.in_(estados))
            .order_by(HistoricoEstado.id)
        )
        return db.session.execute(consulta).all()

    @staticmethod
    def buscar_auditoria(inicio_utc, fim_utc, usuario_id=None, estado=None, numero=None, limite=50, deslocamento=0):
        filtros = [
            HistoricoEstado.data_hora >= inicio_utc,
            HistoricoEstado.data_hora < fim_utc
        ]
        if usuario_id is not None:
            filtros.append(HistoricoEstado.usuario_id == usuario_id)
        if estado:
            filtros.append(HistoricoEstado.estado == estado)
        if numero:
            filtros.append(Senha.numero == numero)

        base = (
            select(
                HistoricoEstado.id,
                HistoricoEstado.senha_id,
                Senha.numero.label("senha_numero"),
                Senha.tipo.label("senha_tipo"),
                Senha.guiche.label("guiche"),
                HistoricoEstado.estado,
                HistoricoEstado.data_hora,
                HistoricoEstado.usuario_id,
                Usuario.nome.label("usuario_nome")
            )
            .select_from(HistoricoEstado)
            .join(Senha, Senha.id == HistoricoEstado.senha_id)
            .outerjoin(Usuario, Usuario.id == HistoricoEstado.usuario_id)
            .where(*filtros)
        )

        total = db.session.execute(select(func.count()).select_from(base.subquery())).scalar_one()
        linhas = db.session.execute(
            base.order_by(HistoricoEstado.data_hora.desc(), HistoricoEstado.id.desc())
            .limit(limite)
            .offset(deslocamento)
        ).all()
        return linhas, total