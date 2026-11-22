from flask import Blueprint, request, jsonify
from app.services.relatorio_service import RelatorioService
from app.decorators import perfil_requerido

relatorio_bp = Blueprint("relatorios", __name__, url_prefix="/api/relatorios")


def _responder(resultado):
    dados, erro, status = resultado
    if erro:
        return jsonify({"erro": erro}), status
    return jsonify(dados), status


@relatorio_bp.route("/diario", methods=["GET"])
@perfil_requerido("GESTOR")
def relatorio_diario():
    return _responder(RelatorioService.diario(request.args.get("data")))


@relatorio_bp.route("/mensal", methods=["GET"])
@perfil_requerido("GESTOR")
def relatorio_mensal():
    return _responder(RelatorioService.mensal(request.args.get("mes")))


@relatorio_bp.route("/auditoria", methods=["GET"])
@perfil_requerido("GESTOR")
def auditoria():
    return _responder(RelatorioService.auditoria(
        data=request.args.get("data"),
        mes=request.args.get("mes"),
        usuario_id=request.args.get("usuario_id"),
        estado=request.args.get("estado"),
        numero=request.args.get("numero"),
        pagina=request.args.get("pagina"),
        por_pagina=request.args.get("por_pagina"),
    ))
