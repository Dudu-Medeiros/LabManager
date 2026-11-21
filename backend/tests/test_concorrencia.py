import threading

from app import db
from app.models.historico import HistoricoEstado
from app.models.senha import Senha
from app.repositories.senha_repository import SenhaRepository
from app.services import senha_service


def contar_historico(senha_id, estado):
    return HistoricoEstado.query.filter_by(senha_id=senha_id, estado=estado).count()


# --- simulação determinística: duas escritas que se cruzam ------------------

def test_transicao_com_versao_desatualizada_e_rejeitada(client, auth, emitir_aguardando, monkeypatch):
    """Atendente B lê a senha, o atendente A grava primeiro, e a gravação de B é rejeitada."""
    senha = emitir_aguardando("SP")
    original = senha_service.validar_transicao
    chamadas = []

    def com_concorrente(estado_atual, novo_estado):
        resultado = original(estado_atual, novo_estado)
        chamadas.append(estado_atual)
        if len(chamadas) == 1:
            # Entre a leitura e a gravação de B, o atendente A (id 2) chama a mesma senha.
            versao_atual = db.session.get(Senha, senha["id"]).versao
            assert SenhaRepository.atualizar_estado_com_historico(
                senha["id"], versao_atual, "AGUARDANDO", "CHAMADA", usuario_id=2
            ) is True
        return resultado

    monkeypatch.setattr(senha_service, "validar_transicao", com_concorrente)

    resposta = client.patch(f"/api/senhas/{senha['id']}/estado", json={"estado": "CHAMADA"}, headers=auth)

    assert resposta.status_code == 409
    assert "outro atendente" in resposta.get_json()["erro"]

    atual = db.session.get(Senha, senha["id"])
    assert atual.usuario_id == 2          # quem gravou primeiro permanece
    assert atual.versao == 3              # 1 (emitida) + 1 (aguardando) + 1 (só uma chamada)
    assert contar_historico(senha["id"], "CHAMADA") == 1


def test_gravacao_rejeitada_nao_deixa_historico_nem_altera_a_senha(app, client, auth, emitir_aguardando):
    senha = emitir_aguardando("SG")
    versao_lida = db.session.get(Senha, senha["id"]).versao

    assert SenhaRepository.atualizar_estado_com_historico(
        senha["id"], versao_lida, "AGUARDANDO", "CHAMADA", usuario_id=2
    ) is True

    # Mesma versão lida de novo: quem chega depois é rejeitado e nada é gravado.
    assert SenhaRepository.atualizar_estado_com_historico(
        senha["id"], versao_lida, "AGUARDANDO", "CHAMADA", usuario_id=1, guiche="09"
    ) is False

    atual = db.session.get(Senha, senha["id"])
    assert atual.usuario_id == 2
    assert atual.guiche is None
    assert contar_historico(senha["id"], "CHAMADA") == 1


def test_fluxo_normal_de_transicoes_continua_funcionando(client, auth, emitir_aguardando):
    senha = emitir_aguardando("SE")

    for estado in ["CHAMADA", "CHAMADA_NOVAMENTE", "EM_ATENDIMENTO", "ATENDIDA"]:
        resposta = client.patch(f"/api/senhas/{senha['id']}/estado", json={"estado": estado}, headers=auth)
        assert resposta.status_code == 200
        assert resposta.get_json()["estado_atual"] == estado

    final = client.get(f"/api/senhas/{senha['id']}", headers=auth).get_json()
    assert final["versao"] == 6
    assert [h["estado"] for h in final["historico"]] == [
        "EMITIDA", "AGUARDANDO", "CHAMADA", "CHAMADA_NOVAMENTE", "EM_ATENDIMENTO", "ATENDIDA"
    ]


# --- simulação com threads: chamadas realmente simultâneas ------------------

def disparar_em_paralelo(app, quantidade, funcao):
    """Executa `funcao(cliente)` em várias threads, todas liberadas ao mesmo tempo."""
    largada = threading.Barrier(quantidade)
    resultados = [None] * quantidade

    def trabalho(indice):
        cliente = app.test_client()
        largada.wait()
        resultados[indice] = funcao(cliente)

    threads = [threading.Thread(target=trabalho, args=(i,)) for i in range(quantidade)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert all(r is not None for r in resultados), "alguma thread não terminou"
    return resultados


def login(cliente, email):
    resposta = cliente.post("/api/auth/login", json={"email": email, "senha": "password123"})
    return {"Authorization": f"Bearer {resposta.get_json()['access_token']}"}


def preparar_fila(cliente, headers, tipos):
    ids = []
    for tipo in tipos:
        senha = cliente.post("/api/senhas/emitir", json={"tipo": tipo}).get_json()
        resposta = cliente.patch(f"/api/senhas/{senha['id']}/estado", json={"estado": "AGUARDANDO"}, headers=headers)
        assert resposta.status_code == 200
        ids.append(senha["id"])
    return ids


def test_chamadas_simultaneas_da_mesma_senha_so_uma_vence(app_arquivo):
    cliente = app_arquivo.test_client()
    headers = login(cliente, "atendente@labflow.com")
    (senha_id,) = preparar_fila(cliente, headers, ["SP"])

    respostas = disparar_em_paralelo(
        app_arquivo, 8,
        lambda c: c.post("/api/senhas/chamar-proximo", json={}, headers=headers)
    )

    status = sorted(r.status_code for r in respostas)
    assert status.count(200) == 1
    assert all(s in (404, 409) for s in status if s != 200)

    db.session.remove()
    assert contar_historico(senha_id, "CHAMADA") == 1
    assert db.session.get(Senha, senha_id).estado_atual == "CHAMADA"


def test_chamadas_simultaneas_nunca_repetem_a_mesma_senha(app_arquivo):
    cliente = app_arquivo.test_client()
    headers = login(cliente, "atendente@labflow.com")
    ids = preparar_fila(cliente, headers, ["SG", "SG", "SG"])

    respostas = disparar_em_paralelo(
        app_arquivo, 8,
        lambda c: c.post("/api/senhas/chamar-proximo", json={}, headers=headers)
    )

    sucessos = [r.get_json()["id"] for r in respostas if r.status_code == 200]
    assert sorted(sucessos) == sorted(ids)   # 3 chamadas, cada senha exatamente uma vez
    assert len(respostas) - len(sucessos) == 5
    assert all(r.status_code in (404, 409) for r in respostas if r.status_code != 200)

    db.session.remove()
    for senha_id in ids:
        assert contar_historico(senha_id, "CHAMADA") == 1


def test_transicoes_simultaneas_na_mesma_senha_so_uma_vence(app_arquivo):
    cliente = app_arquivo.test_client()
    headers = login(cliente, "atendente@labflow.com")
    (senha_id,) = preparar_fila(cliente, headers, ["SE"])

    respostas = disparar_em_paralelo(
        app_arquivo, 8,
        lambda c: c.patch(f"/api/senhas/{senha_id}/estado", json={"estado": "CHAMADA"}, headers=headers)
    )

    status = [r.status_code for r in respostas]
    assert status.count(200) == 1
    assert all(s in (409, 422) for s in status if s != 200)   # 409 = perdeu a disputa, 422 = já estava CHAMADA

    db.session.remove()
    assert contar_historico(senha_id, "CHAMADA") == 1
    assert db.session.get(Senha, senha_id).versao == 3
