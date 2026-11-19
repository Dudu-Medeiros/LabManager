from flask import Blueprint, request, jsonify
from app.services.senha_service import SenhaService

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