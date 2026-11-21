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
        """Retorna a última senha do dia que foi chamada pela primeira vez.

        Só conta o estado CHAMADA: uma rechamada (CHAMADA_NOVAMENTE) é o mesmo
        paciente e não deve alterar o ciclo de alternância das filas.
        """
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
        """Retorna a senha mais antiga (ordem de emissão) do tipo que está aguardando."""
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
        """Move a senha de AGUARDANDO para CHAMADA usando lock otimista.

        O UPDATE só acontece se a versão e o estado ainda forem os que foram
        lidos. Se outro atendente chamou a mesma senha antes, nenhuma linha é
        alterada e o método devolve False para que o serviço escolha a próxima.
        """
        valores = {
            "estado_atual": "CHAMADA",
            "usuario_id": usuario_id,
            "versao": senha.versao + 1
        }
        if guiche is not None:
            valores["guiche"] = guiche

        resultado = db.session.execute(
            update(Senha)
            .where(
                Senha.id == senha.id,
                Senha.versao == senha.versao,
                Senha.estado_atual == "AGUARDANDO"
            )
            .values(**valores)
        )

        if resultado.rowcount == 0:
            db.session.rollback()
            return False

        db.session.add(HistoricoEstado(
            senha_id=senha.id,
            estado="CHAMADA",
            usuario_id=usuario_id
        ))
        db.session.commit()
        return True

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
    def atualizar_estado_com_historico(senha, novo_estado, usuario_id, guiche=None):
        senha.estado_atual = novo_estado
        senha.usuario_id = usuario_id
        senha.versao += 1

        if guiche is not None:
            senha.guiche = guiche

        registro_historico = HistoricoEstado(
            senha_id=senha.id,
            estado=novo_estado,
            usuario_id=usuario_id
        )
        db.session.add(registro_historico)
        db.session.commit()
        return senha