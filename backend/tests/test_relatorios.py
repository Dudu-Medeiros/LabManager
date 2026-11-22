from datetime import datetime, timedelta, timezone

import pytest

from app import db
from app.models.historico import HistoricoEstado

FUSO_BR = timezone(timedelta(hours=-3))

FLUXO_ATENDIDA = ["AGUARDANDO", "CHAMADA", "EM_ATENDIMENTO", "ATENDIDA"]
FLUXO_NAO_COMPARECEU = ["AGUARDANDO", "CHAMADA", "CHAMADA_NOVAMENTE", "NAO_COMPARECEU"]


def hoje_br():
    return datetime.now(FUSO_BR).date()


def mover(client, headers, senha, estados):
    for estado in estados:
        resposta = client.patch(f"/api/senhas/{senha['id']}/estado", json={"estado": estado}, headers=headers)
        assert resposta.status_code == 200


def definir_hora(senha_id, estado, quando_utc):
    registro = HistoricoEstado.query.filter_by(senha_id=senha_id, estado=estado).first()
    registro.data_hora = quando_utc
    db.session.commit()


@pytest.fixture()
def cenario(client, auth, auth2):
    """Dia com 5 senhas: SP1 atendida, SP2 não compareceu, SE1 aguardando,
    SG1 atendida (pelo atendente 2) e SG2 só emitida."""
    def emitir(tipo):
        return client.post("/api/senhas/emitir", json={"tipo": tipo}).get_json()

    dados = {"SP1": emitir("SP"), "SP2": emitir("SP"), "SE1": emitir("SE"), "SG1": emitir("SG"), "SG2": emitir("SG")}
    mover(client, auth, dados["SP1"], FLUXO_ATENDIDA)
    mover(client, auth, dados["SP2"], FLUXO_NAO_COMPARECEU)
    mover(client, auth, dados["SE1"], ["AGUARDANDO"])
    mover(client, auth2, dados["SG1"], FLUXO_ATENDIDA)
    return dados


# --- acesso -----------------------------------------------------------------

@pytest.mark.parametrize("url", ["/api/relatorios/diario", "/api/relatorios/mensal", "/api/relatorios/auditoria"])
def test_somente_gestor_acessa_os_relatorios(client, auth, auth_gestor, url):
    assert client.get(url).status_code == 401
    assert client.get(url, headers=auth).status_code == 403
    assert client.get(url, headers=auth_gestor).status_code == 200


# --- quantitativos ----------------------------------------------------------

def test_relatorio_diario_conta_por_tipo_e_situacao(client, auth_gestor, cenario):
    corpo = client.get("/api/relatorios/diario", headers=auth_gestor).get_json()

    assert corpo["periodo"] == {"tipo": "diario", "data": hoje_br().isoformat()}
    assert corpo["por_tipo"]["SP"] == {"emitidas": 2, "atendidas": 1, "nao_compareceu": 1, "nao_finalizadas": 0}
    assert corpo["por_tipo"]["SE"] == {"emitidas": 1, "atendidas": 0, "nao_compareceu": 0, "nao_finalizadas": 1}
    assert corpo["por_tipo"]["SG"] == {"emitidas": 2, "atendidas": 1, "nao_compareceu": 0, "nao_finalizadas": 1}
    assert corpo["totais"] == {"emitidas": 5, "atendidas": 2, "nao_compareceu": 1, "nao_finalizadas": 2}


def test_relatorio_diario_de_outro_dia_vem_zerado(client, auth_gestor, cenario):
    corpo = client.get("/api/relatorios/diario?data=2020-01-01", headers=auth_gestor).get_json()

    assert corpo["periodo"]["data"] == "2020-01-01"
    assert corpo["totais"] == {"emitidas": 0, "atendidas": 0, "nao_compareceu": 0, "nao_finalizadas": 0}


def test_relatorio_mensal_soma_o_mes_e_detalha_por_dia(client, auth_gestor, cenario):
    mes = hoje_br().strftime("%Y-%m")
    corpo = client.get(f"/api/relatorios/mensal?mes={mes}", headers=auth_gestor).get_json()

    assert corpo["periodo"] == {"tipo": "mensal", "mes": mes}
    assert corpo["totais"] == {"emitidas": 5, "atendidas": 2, "nao_compareceu": 1, "nao_finalizadas": 2}
    assert corpo["por_dia"] == [
        {"data": hoje_br().isoformat(), "emitidas": 5, "atendidas": 2, "nao_compareceu": 1, "nao_finalizadas": 2}
    ]


def test_relatorio_mensal_sem_parametro_usa_o_mes_atual(client, auth_gestor, cenario):
    corpo = client.get("/api/relatorios/mensal", headers=auth_gestor).get_json()

    assert corpo["periodo"]["mes"] == hoje_br().strftime("%Y-%m")
    assert corpo["totais"]["emitidas"] == 5


def test_relatorio_mensal_de_outro_mes_vem_zerado(client, auth_gestor, cenario):
    corpo = client.get("/api/relatorios/mensal?mes=2020-01", headers=auth_gestor).get_json()

    assert corpo["totais"]["emitidas"] == 0
    assert corpo["por_dia"] == []


# --- tempo médio (TM) -------------------------------------------------------

def test_tempo_medio_de_atendimento_e_de_espera(client, auth_gestor, cenario):
    base = datetime(2026, 11, 21, 12, 0, 0)
    sp1, sp2, sg1 = cenario["SP1"]["id"], cenario["SP2"]["id"], cenario["SG1"]["id"]

    # SP1: espera 120 s, atendimento 600 s (10 min)
    definir_hora(sp1, "AGUARDANDO", base)
    definir_hora(sp1, "CHAMADA", base + timedelta(seconds=120))
    definir_hora(sp1, "EM_ATENDIMENTO", base + timedelta(seconds=180))
    definir_hora(sp1, "ATENDIDA", base + timedelta(seconds=780))
    # SG1: espera 60 s, atendimento 300 s (5 min)
    definir_hora(sg1, "AGUARDANDO", base)
    definir_hora(sg1, "CHAMADA", base + timedelta(seconds=60))
    definir_hora(sg1, "EM_ATENDIMENTO", base + timedelta(seconds=90))
    definir_hora(sg1, "ATENDIDA", base + timedelta(seconds=390))
    # SP2 foi chamada e não compareceu: tem espera (240 s), mas não tem atendimento.
    definir_hora(sp2, "AGUARDANDO", base)
    definir_hora(sp2, "CHAMADA", base + timedelta(seconds=240))

    tm = client.get("/api/relatorios/diario", headers=auth_gestor).get_json()["tempo_medio"]

    # Atendimento: só as senhas que chegaram a ser atendidas (SP1 e SG1).
    assert tm["SP"]["atendimento"] == {"amostras": 1, "segundos": 600.0, "minutos": 10.0}
    assert tm["SG"]["atendimento"] == {"amostras": 1, "segundos": 300.0, "minutos": 5.0}
    assert tm["geral"]["atendimento"] == {"amostras": 2, "segundos": 450.0, "minutos": 7.5}
    # Espera: toda senha que foi chamada (SP1 120 s, SP2 240 s, SG1 60 s).
    assert tm["SP"]["espera"] == {"amostras": 2, "segundos": 180.0, "minutos": 3.0}
    assert tm["SG"]["espera"] == {"amostras": 1, "segundos": 60.0, "minutos": 1.0}
    assert tm["geral"]["espera"] == {"amostras": 3, "segundos": 140.0, "minutos": 2.33}


def test_tempo_medio_sem_atendimentos_concluidos_vem_vazio(client, auth_gestor, cenario):
    tm = client.get("/api/relatorios/diario", headers=auth_gestor).get_json()["tempo_medio"]

    # SE1 só entrou na fila: não tem duração de atendimento nem de espera.
    assert tm["SE"]["atendimento"] == {"amostras": 0, "segundos": None, "minutos": None}
    assert tm["SE"]["espera"] == {"amostras": 0, "segundos": None, "minutos": None}


def test_tempo_medio_do_mensal_usa_so_o_mes_pedido(client, auth_gestor, cenario):
    tm = client.get("/api/relatorios/mensal?mes=2020-01", headers=auth_gestor).get_json()["tempo_medio"]

    assert tm["geral"]["atendimento"]["amostras"] == 0


# --- auditoria (histórico de ações) -----------------------------------------

def test_auditoria_lista_todas_as_acoes_do_dia_da_mais_recente_para_a_mais_antiga(client, auth_gestor, cenario):
    corpo = client.get("/api/relatorios/auditoria", headers=auth_gestor).get_json()

    # SP1 5 + SP2 5 + SE1 2 + SG1 5 + SG2 1 registros de histórico
    assert corpo["total"] == 18
    assert corpo["periodo"] == {"tipo": "diario", "data": hoje_br().isoformat()}
    horarios = [r["data_hora"] for r in corpo["registros"]]
    assert horarios == sorted(horarios, reverse=True)

    registro = corpo["registros"][0]
    assert set(registro) == {
        "id", "senha_id", "senha_numero", "senha_tipo", "guiche",
        "estado", "data_hora", "usuario_id", "usuario_nome"
    }
    assert registro["data_hora"].endswith("-03:00")


def test_auditoria_identifica_quem_fez_cada_acao(client, auth_gestor, cenario):
    corpo = client.get("/api/relatorios/auditoria?usuario_id=2", headers=auth_gestor).get_json()

    assert corpo["total"] == 4   # as 4 transições da SG1, feitas pelo atendente 2
    assert {r["usuario_nome"] for r in corpo["registros"]} == {"Atendente 2"}
    assert {r["senha_numero"] for r in corpo["registros"]} == {cenario["SG1"]["numero"]}

    emissoes = client.get("/api/relatorios/auditoria?estado=emitida", headers=auth_gestor).get_json()
    assert emissoes["total"] == 5   # a emissão no totem não tem usuário
    assert {r["usuario_id"] for r in emissoes["registros"]} == {None}
    assert {r["usuario_nome"] for r in emissoes["registros"]} == {None}


def test_auditoria_filtra_por_estado_e_por_senha(client, auth_gestor, cenario):
    por_estado = client.get("/api/relatorios/auditoria?estado=chamada", headers=auth_gestor).get_json()
    assert por_estado["total"] == 3   # SP1, SP2 e SG1

    numero = cenario["SP1"]["numero"]
    por_senha = client.get(f"/api/relatorios/auditoria?numero={numero}", headers=auth_gestor).get_json()
    assert por_senha["total"] == 5
    assert [r["estado"] for r in reversed(por_senha["registros"])] == ["EMITIDA"] + FLUXO_ATENDIDA


def test_auditoria_pagina_os_resultados(client, auth_gestor, cenario):
    def pagina(n):
        return client.get(f"/api/relatorios/auditoria?por_pagina=5&pagina={n}", headers=auth_gestor).get_json()

    tamanhos = [len(pagina(n)["registros"]) for n in (1, 2, 3, 4, 5)]
    assert tamanhos == [5, 5, 5, 3, 0]
    assert pagina(1)["total"] == 18

    ids = [r["id"] for n in (1, 2, 3, 4) for r in pagina(n)["registros"]]
    assert len(set(ids)) == 18   # nenhum registro repetido entre as páginas

    limitado = client.get("/api/relatorios/auditoria?por_pagina=1000", headers=auth_gestor).get_json()
    assert limitado["por_pagina"] == 200


def test_auditoria_respeita_o_dia_no_horario_de_brasilia(client, auth_gestor, cenario):
    # 02:30 UTC de 16/01 é 23:30 de 15/01 em Brasília; 03:00 UTC de 16/01 já é 16/01 em Brasília.
    definir_hora(cenario["SE1"]["id"], "EMITIDA", datetime(2026, 1, 16, 2, 30, 0))
    definir_hora(cenario["SG2"]["id"], "EMITIDA", datetime(2026, 1, 16, 3, 0, 0))

    dia15 = client.get("/api/relatorios/auditoria?data=2026-01-15", headers=auth_gestor).get_json()
    dia16 = client.get("/api/relatorios/auditoria?data=2026-01-16", headers=auth_gestor).get_json()
    mes = client.get("/api/relatorios/auditoria?mes=2026-01", headers=auth_gestor).get_json()
    hoje = client.get("/api/relatorios/auditoria", headers=auth_gestor).get_json()

    assert [r["senha_numero"] for r in dia15["registros"]] == [cenario["SE1"]["numero"]]
    assert dia15["registros"][0]["data_hora"] == "2026-01-15T23:30:00-03:00"
    assert [r["senha_numero"] for r in dia16["registros"]] == [cenario["SG2"]["numero"]]
    assert mes["total"] == 2
    assert hoje["total"] == 16


# --- parâmetros inválidos ---------------------------------------------------

@pytest.mark.parametrize("url", [
    "/api/relatorios/diario?data=21/11/2026",
    "/api/relatorios/diario?data=2026-02-30",
    "/api/relatorios/mensal?mes=2026-13",
    "/api/relatorios/mensal?mes=novembro",
    "/api/relatorios/auditoria?data=ontem",
    "/api/relatorios/auditoria?data=2026-11-21&mes=2026-11",
    "/api/relatorios/auditoria?estado=INEXISTENTE",
    "/api/relatorios/auditoria?usuario_id=abc",
    "/api/relatorios/auditoria?pagina=0",
    "/api/relatorios/auditoria?por_pagina=abc",
])
def test_parametros_invalidos_retornam_400(client, auth_gestor, url):
    resposta = client.get(url, headers=auth_gestor)

    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()
