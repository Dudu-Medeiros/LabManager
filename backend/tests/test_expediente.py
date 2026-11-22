from datetime import datetime
from app.services.senha_service import FUSO_BR, apos_expediente, esta_no_expediente


def test_expediente_bloqueia_antes_das_07h(monkeypatch):
    monkeypatch.setenv("VALIDAR_EXPEDIENTE", "true")
    monkeypatch.setenv("EXPEDIENTE_INICIO", "7")
    monkeypatch.setenv("EXPEDIENTE_FIM", "17")

    horario = datetime(2026, 11, 22, 6, 59, tzinfo=FUSO_BR)
    assert esta_no_expediente(horario) is False
    assert apos_expediente(horario) is False


def test_expediente_permite_entre_07h_e_16h59(monkeypatch):
    monkeypatch.setenv("VALIDAR_EXPEDIENTE", "true")
    monkeypatch.setenv("EXPEDIENTE_INICIO", "7")
    monkeypatch.setenv("EXPEDIENTE_FIM", "17")

    abertura = datetime(2026, 11, 22, 7, 0, tzinfo=FUSO_BR)
    ultimo_minuto = datetime(2026, 11, 22, 16, 59, tzinfo=FUSO_BR)

    assert esta_no_expediente(abertura) is True
    assert esta_no_expediente(ultimo_minuto) is True
    assert apos_expediente(ultimo_minuto) is False


def test_expediente_bloqueia_e_marca_encerrado_a_partir_das_17h(monkeypatch):
    monkeypatch.setenv("VALIDAR_EXPEDIENTE", "true")
    monkeypatch.setenv("EXPEDIENTE_INICIO", "7")
    monkeypatch.setenv("EXPEDIENTE_FIM", "17")

    fechamento = datetime(2026, 11, 22, 17, 0, tzinfo=FUSO_BR)
    noite = datetime(2026, 11, 22, 20, 30, tzinfo=FUSO_BR)

    assert esta_no_expediente(fechamento) is False
    assert apos_expediente(fechamento) is True
    assert esta_no_expediente(noite) is False
    assert apos_expediente(noite) is True


def test_expediente_desativado_permite_qualquer_horario(monkeypatch):
    monkeypatch.setenv("VALIDAR_EXPEDIENTE", "false")

    madrugada = datetime(2026, 11, 22, 2, 0, tzinfo=FUSO_BR)
    assert esta_no_expediente(madrugada) is True
    assert apos_expediente(madrugada) is False