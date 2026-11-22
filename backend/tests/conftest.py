import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.usuario import Usuario
from config import Config


def _config(uri):
    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = uri
        JWT_SECRET_KEY = "chave-de-teste-com-tamanho-suficiente-para-hmac"
    return TestConfig


def _popular_usuarios():
    senha_hash = generate_password_hash("password123")
    db.session.add_all([
        Usuario(nome="Atendente", email="atendente@labflow.com", senha_hash=senha_hash, perfil="ATENDENTE"),
        Usuario(nome="Atendente 2", email="atendente2@labflow.com", senha_hash=senha_hash, perfil="ATENDENTE"),
        Usuario(nome="Gestor", email="gestor@labflow.com", senha_hash=senha_hash, perfil="GESTOR"),
    ])
    db.session.commit()


@pytest.fixture()
def app():
    app = create_app(_config("sqlite://"))
    with app.app_context():
        db.create_all()
        _popular_usuarios()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def app_arquivo(tmp_path):
    """App com SQLite em arquivo, necessário para testar várias conexões ao mesmo tempo."""
    app = create_app(_config(f"sqlite:///{tmp_path / 'teste.db'}"))
    with app.app_context():
        db.create_all()
        _popular_usuarios()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client, email):
    resposta = client.post("/api/auth/login", json={"email": email, "senha": "password123"})
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.get_json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return _login(client, "atendente@labflow.com")


@pytest.fixture()
def auth2(client):
    return _login(client, "atendente2@labflow.com")


@pytest.fixture()
def auth_gestor(client):
    return _login(client, "gestor@labflow.com")


@pytest.fixture()
def emitir_aguardando(client, auth):
    """Emite uma senha do tipo informado e já a coloca na fila (estado AGUARDANDO)."""
    def _emitir(tipo):
        senha = client.post("/api/senhas/emitir", json={"tipo": tipo}).get_json()
        resposta = client.patch(f"/api/senhas/{senha['id']}/estado", json={"estado": "AGUARDANDO"}, headers=auth)
        assert resposta.status_code == 200
        return senha
    return _emitir
