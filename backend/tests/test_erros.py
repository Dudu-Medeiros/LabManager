import logging
from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import OperationalError

from app import create_app, db
from app.models.usuario import Usuario
from config import Config

DETALHES_QUE_NAO_PODEM_VAZAR = [
    "Traceback", "RuntimeError", "OperationalError", "detalhe-interno-secreto",
    "senha=123", "10.0.0.5", "SELECT 1", ".py", "File \"",
]


def assert_resposta_padronizada(resposta, status, codigo):
    assert resposta.status_code == status
    assert resposta.is_json, "a resposta de erro deve ser JSON, não HTML"
    corpo = resposta.get_json()
    assert corpo["codigo"] == codigo
    assert isinstance(corpo["erro"], str) and corpo["erro"]
    return corpo


def assert_sem_vazamento(resposta):
    texto = resposta.get_data(as_text=True)
    for detalhe in DETALHES_QUE_NAO_PODEM_VAZAR:
        assert detalhe not in texto, f"a resposta expôs '{detalhe}'"


def registrar_rotas_de_falha(app):
    @app.route("/_teste/erro-inesperado")
    def erro_inesperado():
        raise RuntimeError("detalhe-interno-secreto senha=123")

    @app.route("/_teste/banco-fora")
    def banco_fora():
        raise OperationalError("SELECT 1", {}, Exception("conexao recusada em 10.0.0.5"))

    @app.route("/_teste/transacao-quebrada")
    def transacao_quebrada():
        db.session.add(Usuario(nome="Fantasma", email="fantasma@labflow.com", senha_hash="x", perfil="ATENDENTE"))
        db.session.flush()
        raise RuntimeError("falhou no meio da transação")


@pytest.fixture()
def rotas_de_falha(app):
    registrar_rotas_de_falha(app)
    return app


# --- erros comuns da requisição ---------------------------------------------

def test_rota_inexistente_retorna_json_padronizado(client):
    resposta = client.get("/api/nao-existe")

    corpo = assert_resposta_padronizada(resposta, 404, "NAO_ENCONTRADO")
    assert "id_erro" not in corpo   # erro do cliente não é falha do servidor
    assert "<html" not in resposta.get_data(as_text=True).lower()


def test_metodo_nao_permitido_informa_os_metodos_aceitos(client):
    resposta = client.get("/api/senhas/emitir")

    assert_resposta_padronizada(resposta, 405, "METODO_NAO_PERMITIDO")
    assert "POST" in resposta.headers["Allow"]


def test_json_malformado_retorna_400_sem_detalhes_do_parser(client):
    resposta = client.post("/api/senhas/emitir", data="{ruim", content_type="application/json")

    assert_resposta_padronizada(resposta, 400, "REQUISICAO_INVALIDA")
    assert "decode" not in resposta.get_data(as_text=True).lower()


def test_corpo_que_nao_e_json_retorna_415(client):
    resposta = client.post("/api/senhas/emitir", data="oi", content_type="text/plain")

    assert_resposta_padronizada(resposta, 415, "FORMATO_NAO_SUPORTADO")


# --- autenticação -----------------------------------------------------------

def test_sem_token_retorna_401_padronizado(client):
    assert_resposta_padronizada(client.get("/api/relatorios/diario"), 401, "NAO_AUTENTICADO")


def test_token_invalido_retorna_401_padronizado(client):
    resposta = client.get("/api/relatorios/diario", headers={"Authorization": "Bearer isso-nao-e-um-token"})

    assert_resposta_padronizada(resposta, 401, "TOKEN_INVALIDO")
    assert_sem_vazamento(resposta)


def test_token_expirado_retorna_401_padronizado(app, client):
    token = create_access_token(
        identity="1", additional_claims={"perfil": "GESTOR"}, expires_delta=timedelta(seconds=-10)
    )

    resposta = client.get("/api/relatorios/diario", headers={"Authorization": f"Bearer {token}"})

    assert_resposta_padronizada(resposta, 401, "TOKEN_EXPIRADO")


def test_acesso_negado_retorna_403_padronizado(client, auth):
    assert_resposta_padronizada(client.get("/api/relatorios/diario", headers=auth), 403, "ACESSO_NEGADO")


# --- falhas do servidor -----------------------------------------------------

def test_erro_inesperado_retorna_500_amigavel_sem_expor_detalhes(client, rotas_de_falha):
    resposta = client.get("/_teste/erro-inesperado")

    corpo = assert_resposta_padronizada(resposta, 500, "ERRO_INTERNO")
    assert corpo["erro"].startswith("Ocorreu um erro interno")
    assert len(corpo["id_erro"]) == 8
    assert_sem_vazamento(resposta)


def test_erro_inesperado_vai_para_o_log_com_stack_trace_e_o_mesmo_id(client, rotas_de_falha, caplog):
    with caplog.at_level(logging.ERROR, logger="app"):
        corpo = client.get("/_teste/erro-inesperado").get_json()

    registro = next(r for r in caplog.records if corpo["id_erro"] in r.getMessage())
    assert registro.levelno == logging.ERROR
    assert registro.exc_info[0] is RuntimeError
    assert "GET /_teste/erro-inesperado" in registro.getMessage()
    assert "detalhe-interno-secreto" in caplog.text   # o detalhe está no log, não na resposta


def test_cada_falha_recebe_um_id_diferente(client, rotas_de_falha):
    ids = {client.get("/_teste/erro-inesperado").get_json()["id_erro"] for _ in range(5)}

    assert len(ids) == 5


def test_banco_fora_do_ar_retorna_503_amigavel(client, rotas_de_falha, caplog):
    with caplog.at_level(logging.ERROR, logger="app"):
        resposta = client.get("/_teste/banco-fora")

    corpo = assert_resposta_padronizada(resposta, 503, "BANCO_INDISPONIVEL")
    assert "dificuldade para acessar os dados" in corpo["erro"]
    assert_sem_vazamento(resposta)
    assert any(corpo["id_erro"] in r.getMessage() for r in caplog.records)


def test_falha_no_meio_da_transacao_desfaz_o_que_estava_pendente(client, rotas_de_falha):
    assert client.get("/_teste/transacao-quebrada").status_code == 500

    assert Usuario.query.filter_by(email="fantasma@labflow.com").first() is None
    # e a API continua funcionando normalmente na requisição seguinte
    resposta = client.post("/api/auth/login", json={"email": "atendente@labflow.com", "senha": "password123"})
    assert resposta.status_code == 200


# --- health check -----------------------------------------------------------

def test_health_check_ok(client):
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.get_json()["status"] == "ok"


def test_health_check_devolve_503_quando_o_banco_nao_responde(client, monkeypatch):
    def banco_fora(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("banco fora"))

    monkeypatch.setattr(db.session, "execute", banco_fora)

    resposta = client.get("/health")

    assert resposta.status_code == 503
    assert resposta.get_json()["status"] == "indisponivel"


# --- log em arquivo ---------------------------------------------------------

def test_log_em_arquivo_registra_a_falha_com_id_e_stack_trace(tmp_path):
    pasta_de_logs = tmp_path / "logs"

    class ConfigComArquivo(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        JWT_SECRET_KEY = "chave-de-teste-com-tamanho-suficiente-para-hmac"
        LOG_TO_FILE = True
        LOG_DIR = str(pasta_de_logs)

    app = create_app(ConfigComArquivo)
    logger = logging.getLogger(app.name)
    try:
        registrar_rotas_de_falha(app)
        corpo = app.test_client().get("/_teste/erro-inesperado").get_json()
        for handler in logger.handlers:
            handler.flush()

        conteudo = (pasta_de_logs / "labmanager.log").read_text(encoding="utf-8")
        assert corpo["id_erro"] in conteudo
        assert "ERROR" in conteudo
        assert "Traceback" in conteudo
        assert "detalhe-interno-secreto" in conteudo
    finally:
        for handler in list(logger.handlers):
            if getattr(handler, "_labmanager_handler", False):
                logger.removeHandler(handler)
                handler.close()


def test_criar_a_app_varias_vezes_nao_duplica_as_mensagens_de_log(tmp_path):
    for _ in range(3):
        app = create_app(type("Cfg", (Config,), {
            "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "LOG_TO_FILE": False,
            "JWT_SECRET_KEY": "chave-de-teste-com-tamanho-suficiente-para-hmac",
        }))

    marcados = [h for h in logging.getLogger(app.name).handlers if getattr(h, "_labmanager_handler", False)]
    assert len(marcados) == 1   # só o console
