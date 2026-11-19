from app import db
from app.models.usuario import Usuario

class UsuarioRepository:
    @staticmethod
    def buscar_por_email(email):
        return Usuario.query.filter_by(email=email).first()

    @staticmethod
    def buscar_por_id(usuario_id):
        return db.session.get(Usuario, usuario_id)

    @staticmethod
    def listar_todos():
        return Usuario.query.all()

    @staticmethod
    def criar(usuario):
        db.session.add(usuario)
        db.session.commit()
        return usuario