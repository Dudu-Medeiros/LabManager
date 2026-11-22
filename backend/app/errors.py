import logging
import uuid

from flask import jsonify, request
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import HTTPException

from app import db

logger = logging.getLogger(__name__)

# Toda resposta de erro tem o formato:
#   {"erro": "mensagem amigável", "codigo": "CODIGO_ESTAVEL"}
# e, nas falhas do servidor (5xx), também "id_erro": código curto que aparece no log
# junto com os detalhes técnicos. Os detalhes (stack trace, SQL, caminhos) nunca saem na resposta.

MENSAGEM_ERRO_INTERNO = (
    "Ocorreu um erro interno. Tente novamente em instantes. "
    "Se o problema continuar, informe o código de erro ao suporte."
)
MENSAGEM_BANCO_INDISPONIVEL = (
    "O sistema está com dificuldade para acessar os dados no momento. "
    "Tente novamente em instantes. Se o problema continuar, informe o código de erro ao suporte."
)

ERROS_HTTP = {
    400: ("REQUISICAO_INVALIDA", "Requisição inválida. Verifique os dados enviados (o corpo deve ser um JSON válido)."),
    401: ("NAO_AUTENTICADO", "Autenticação necessária. Faça login para continuar."),
    403: ("ACESSO_NEGADO", "Acesso negado. Permissão insuficiente."),
    404: ("NAO_ENCONTRADO", "Recurso não encontrado."),
    405: ("METODO_NAO_PERMITIDO", "Método não permitido para este recurso."),
    413: ("CORPO_MUITO_GRANDE", "Os dados enviados são grandes demais."),
    415: ("FORMATO_NAO_SUPORTADO", "Formato não suportado. Envie os dados em JSON (Content-Type: application/json)."),
    429: ("MUITAS_REQUISICOES", "Muitas requisições. Aguarde um instante e tente novamente."),
}
ERRO_HTTP_GENERICO = ("ERRO_NA_REQUISICAO", "Não foi possível processar a requisição.")

# Cabeçalhos do erro original que continuam úteis para o cliente (ex.: quais métodos são aceitos).
CABECALHOS_PRESERVADOS = ("allow", "retry-after")


def resposta_de_erro(status, codigo, mensagem, id_erro=None):
    corpo = {"erro": mensagem, "codigo": codigo}
    if id_erro:
        corpo["id_erro"] = id_erro
    return jsonify(corpo), status


def _descartar_transacao_pendente():
    """Evita que uma transação quebrada pela falha contamine a próxima requisição."""
    try:
        db.session.rollback()
    except Exception:
        logger.warning("Não foi possível desfazer a transação pendente após a falha.", exc_info=True)


def _registrar_falha_e_responder(excecao, status, codigo, mensagem):
    id_erro = uuid.uuid4().hex[:8]
    logger.error(
        "[id_erro=%s] %s %s -> %s %s",
        id_erro, request.method, request.path, status, codigo,
        exc_info=excecao
    )
    _descartar_transacao_pendente()
    return resposta_de_erro(status, codigo, mensagem, id_erro)


def _tratar_http(excecao):
    status = excecao.code or 500
    if status >= 500:
        return _registrar_falha_e_responder(excecao, status, "ERRO_INTERNO", MENSAGEM_ERRO_INTERNO)

    codigo, mensagem = ERROS_HTTP.get(status, ERRO_HTTP_GENERICO)
    corpo, _ = resposta_de_erro(status, codigo, mensagem)
    for nome, valor in excecao.get_headers():
        if nome.lower() in CABECALHOS_PRESERVADOS:
            corpo.headers[nome] = valor
    return corpo, status


def _tratar_banco_indisponivel(excecao):
    return _registrar_falha_e_responder(excecao, 503, "BANCO_INDISPONIVEL", MENSAGEM_BANCO_INDISPONIVEL)


def _tratar_erro_inesperado(excecao):
    return _registrar_falha_e_responder(excecao, 500, "ERRO_INTERNO", MENSAGEM_ERRO_INTERNO)


def registrar_tratadores_de_erro(app, jwt):
    app.register_error_handler(HTTPException, _tratar_http)
    app.register_error_handler(OperationalError, _tratar_banco_indisponivel)
    app.register_error_handler(Exception, _tratar_erro_inesperado)

    # Erros de autenticação (JWT): mesmo formato, sem repassar o motivo técnico ao cliente.
    @jwt.unauthorized_loader
    def _sem_token(_motivo):
        return resposta_de_erro(401, "NAO_AUTENTICADO", ERROS_HTTP[401][1])

    @jwt.invalid_token_loader
    def _token_invalido(_motivo):
        return resposta_de_erro(401, "TOKEN_INVALIDO", "Token de acesso inválido. Faça login novamente.")

    @jwt.expired_token_loader
    def _token_expirado(_cabecalho, _dados):
        return resposta_de_erro(401, "TOKEN_EXPIRADO", "Sua sessão expirou. Faça login novamente.")
