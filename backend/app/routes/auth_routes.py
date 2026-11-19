from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.auth_service import AuthService
from app.decorators import perfil_requerido

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    dados = request.get_json() or {}
    resultado, erro = AuthService.login(dados.get("email"), dados.get("senha"))

    if erro:
        return jsonify({"erro": erro}), 401

    return jsonify(resultado), 200

@auth_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    usuario_id = get_jwt_identity()
    claims = get_jwt()
    return jsonify({
        "id": int(usuario_id),
        "nome": claims.get("nome"),
        "perfil": claims.get("perfil")
    }), 200

@auth_bp.route("/usuarios", methods=["GET"])
@perfil_requerido("GESTOR")
def listar_usuarios():
    usuarios = AuthService.listar_usuarios()
    return jsonify(usuarios), 200

@auth_bp.route("/usuarios", methods=["POST"])
@perfil_requerido("GESTOR")
def criar_usuario():
    dados = request.get_json() or {}
    usuario, erro = AuthService.criar_usuario(
        nome=dados.get("nome"),
        email=dados.get("email"),
        senha=dados.get("senha"),
        perfil=dados.get("perfil")
    )

    if erro:
        return jsonify({"erro": erro}), 400

    return jsonify(usuario), 201