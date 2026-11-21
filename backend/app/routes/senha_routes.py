from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.services.senha_service import SenhaService
from app.decorators import perfil_requerido

senha_bp = Blueprint("senhas", __name__, url_prefix="/api/senhas")

@senha_bp.route("/emitir", methods=["POST"])
def emitir_senha():
    dados = request.get_json() or {}
    senha, erro = SenhaService.emitir_senha(
        tipo=dados.get("tipo"),
        paciente_id=dados.get("paciente_id")
    )

    if erro:
        return jsonify({"erro": erro}), 400

    return jsonify(senha), 201

@senha_bp.route("/chamar-proximo", methods=["POST"])
@perfil_requerido("ATENDENTE", "GESTOR")
def chamar_proximo():
    dados = request.get_json(silent=True) or {}
    usuario_id = int(get_jwt_identity())

    senha, erro, status = SenhaService.chamar_proxima(
        usuario_id=usuario_id,
        guiche=dados.get("guiche")
    )

    if erro:
        return jsonify({"erro": erro}), status

    return jsonify(senha), status

@senha_bp.route("/<int:senha_id>", methods=["GET"])
@perfil_requerido("ATENDENTE", "GESTOR")
def obter_senha(senha_id):
    senha, erro = SenhaService.buscar_por_id(senha_id)
    if erro:
        return jsonify({"erro": erro}), 404
    return jsonify(senha), 200

@senha_bp.route("/<int:senha_id>/estado", methods=["PATCH"])
@perfil_requerido("ATENDENTE", "GESTOR")
def atualizar_estado(senha_id):
    dados = request.get_json() or {}
    usuario_id = int(get_jwt_identity())

    senha, erro, status = SenhaService.transicionar_estado(
        senha_id=senha_id,
        novo_estado=dados.get("estado"),
        usuario_id=usuario_id,
        guiche=dados.get("guiche")
    )

    if erro:
        return jsonify({"erro": erro}), status

    return jsonify(senha), status