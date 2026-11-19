from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository

class AuthService:
    @staticmethod
    def login(email, senha):
        if not email or not senha:
            return None, "Email e senha são obrigatórios."

        usuario = UsuarioRepository.buscar_por_email(email)
        if not usuario or not check_password_hash(usuario.senha_hash, senha):
            return None, "Credenciais inválidas."

        # identity precisa ser string nas versoes atuais do Flask-JWT-Extended
        token = create_access_token(
            identity=str(usuario.id),
            additional_claims={
                "perfil": usuario.perfil,
                "nome": usuario.nome
            }
        )

        return {
            "access_token": token,
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "perfil": usuario.perfil
            }
        }, None

    @staticmethod
    def criar_usuario(nome, email, senha, perfil):
        perfis_validos = ["ATENDENTE", "GESTOR"]
        perfil_upper = perfil.upper() if perfil else ""

        if not nome or not email or not senha or perfil_upper not in perfis_validos:
            return None, "Dados inválidos. Informe nome, email, senha e perfil (ATENDENTE ou GESTOR)."

        if UsuarioRepository.buscar_por_email(email):
            return None, "Já existe um usuário cadastrado com este email."

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=generate_password_hash(senha),
            perfil=perfil_upper
        )
        UsuarioRepository.criar(novo_usuario)

        return {
            "id": novo_usuario.id,
            "nome": novo_usuario.nome,
            "email": novo_usuario.email,
            "perfil": novo_usuario.perfil
        }, None

    @staticmethod
    def listar_usuarios():
        usuarios = UsuarioRepository.listar_todos()
        return [
            {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "perfil": u.perfil
            }
            for u in usuarios
        ]