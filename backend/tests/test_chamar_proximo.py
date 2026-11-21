from types import SimpleNamespace

from app import db
from app.models.historico import HistoricoEstado
from app.models.senha import Senha
from app.repositories.senha_repository import SenhaRepository
from app.services.senha_service import ordem_de_busca

URL = "/api/senhas/chamar-proximo"


def chamar(client, auth, **corpo):
    return client.post(URL, json=corpo, headers=auth)


def tipos_chamados(client, auth, quantidade):
    return [chamar(client, auth).get_json()["tipo"] for _ in range(quantidade)]


# --- regra de alternância -------------------------------------------------

def test_ordem_de_busca_segue_o_ciclo_do_edital():
    assert ordem_de_busca(None) == ["SP", "SE", "SG"]
    assert ordem_de_busca("SP") == ["SE", "SG", "SP"]
    assert ordem_de_busca("SE") == ["SP", "SE", "SG"]
    assert ordem_de_busca("SG") == ["SP", "SE", "SG"]


def test_alterna_sp_com_se_ou_sg(client, auth, emitir_aguardando):
    for tipo in ["SG", "SG", "SE", "SP", "SP"]:
        emitir_aguardando(tipo)

    # SP -> SE -> SP -> SG (SE esgotou) -> SG (SP esgotou)
    assert tipos_chamados(client, auth, 5) == ["SP", "SE", "SP", "SG", "SG"]


def test_se_tem_prioridade_sobre_sg(client, auth, emitir_aguardando):
    emitir_aguardando("SG")
    emitir_aguardando("SE")
    emitir_aguardando("SP")

    assert tipos_chamados(client, auth, 3) == ["SP", "SE", "SG"]


def test_fila_de_sp_vazia_chama_se_e_depois_sg(client, auth, emitir_aguardando):
    for tipo in ["SG", "SG", "SE"]:
        emitir_aguardando(tipo)

    assert tipos_chamados(client, auth, 3) == ["SE", "SG", "SG"]


def test_so_sp_na_fila_chama_sp_em_sequencia(client, auth, emitir_aguardando):
    for _ in range(3):
        emitir_aguardando("SP")

    assert tipos_chamados(client, auth, 3) == ["SP", "SP", "SP"]


def test_dentro_do_mesmo_tipo_respeita_a_ordem_de_emissao(client, auth, emitir_aguardando):
    primeira = emitir_aguardando("SG")
    segunda = emitir_aguardando("SG")

    assert chamar(client, auth).get_json()["numero"] == primeira["numero"]
    assert chamar(client, auth).get_json()["numero"] == segunda["numero"]


def test_sp_que_chega_depois_e_chamada_na_vez_do_ciclo(client, auth, emitir_aguardando):
    emitir_aguardando("SG")
    emitir_aguardando("SG")
    assert tipos_chamados(client, auth, 1) == ["SG"]

    emitir_aguardando("SP")
    assert tipos_chamados(client, auth, 2) == ["SP", "SG"]


def test_rechamada_nao_altera_o_ciclo(client, auth, emitir_aguardando):
    sp1 = emitir_aguardando("SP")
    emitir_aguardando("SE")
    emitir_aguardando("SP")
    emitir_aguardando("SG")

    assert tipos_chamados(client, auth, 2) == ["SP", "SE"]

    # Rechamar a SP1 é o mesmo paciente: a última chamada nova continua sendo a SE.
    resposta = client.patch(f"/api/senhas/{sp1['id']}/estado", json={"estado": "CHAMADA_NOVAMENTE"}, headers=auth)
    assert resposta.status_code == 200

    assert tipos_chamados(client, auth, 1) == ["SP"]


# --- comportamento do endpoint ---------------------------------------------

def test_sem_senhas_aguardando_retorna_404(client, auth):
    resposta = chamar(client, auth)

    assert resposta.status_code == 404
    assert "erro" in resposta.get_json()


def test_senha_apenas_emitida_nao_entra_na_chamada(client, auth):
    client.post("/api/senhas/emitir", json={"tipo": "SP"})

    assert chamar(client, auth).status_code == 404


def test_chamada_atualiza_estado_guiche_versao_e_historico(client, auth, emitir_aguardando):
    senha = emitir_aguardando("SP")

    resposta = chamar(client, auth, guiche="03")
    corpo = resposta.get_json()

    assert resposta.status_code == 200
    assert corpo["id"] == senha["id"]
    assert corpo["estado_atual"] == "CHAMADA"
    assert corpo["guiche"] == "03"
    assert corpo["versao"] == 3  # 1 (emitida) + 1 (aguardando) + 1 (chamada)
    assert [h["estado"] for h in corpo["historico"]] == ["EMITIDA", "AGUARDANDO", "CHAMADA"]


def test_senha_chamada_nao_e_chamada_de_novo(client, auth, emitir_aguardando):
    emitir_aguardando("SG")

    assert chamar(client, auth).status_code == 200
    assert chamar(client, auth).status_code == 404


def test_endpoint_exige_autenticacao(client):
    assert client.post(URL).status_code == 401


def test_gestor_tambem_pode_chamar(client, emitir_aguardando):
    emitir_aguardando("SG")
    resposta = client.post("/api/auth/login", json={"email": "gestor@labflow.com", "senha": "password123"})
    headers = {"Authorization": f"Bearer {resposta.get_json()['access_token']}"}

    assert client.post(URL, headers=headers).status_code == 200


# --- concorrência (lock otimista) ------------------------------------------

def test_atualizacao_com_versao_desatualizada_e_rejeitada(app, client, auth, emitir_aguardando):
    senha = emitir_aguardando("SP")
    versao_lida = db.session.get(Senha, senha["id"]).versao

    # Outro atendente chama a senha primeiro.
    assert chamar(client, auth).status_code == 200

    desatualizada = SimpleNamespace(id=senha["id"], versao=versao_lida)
    assert SenhaRepository.marcar_como_chamada(desatualizada, usuario_id=2) is False

    chamadas = HistoricoEstado.query.filter_by(senha_id=senha["id"], estado="CHAMADA").count()
    assert chamadas == 1


def test_perdeu_a_disputa_chama_a_proxima_da_fila(client, auth, emitir_aguardando, monkeypatch):
    sp = emitir_aguardando("SP")
    sg = emitir_aguardando("SG")

    original = SenhaRepository.marcar_como_chamada
    tentativas = []

    def com_concorrente(senha, usuario_id, guiche=None):
        tentativas.append(senha.id)
        if len(tentativas) == 1:
            # Outro atendente (id 2) chama a mesma senha milissegundos antes.
            assert original(senha, 2, guiche) is True
            return False
        return original(senha, usuario_id, guiche)

    monkeypatch.setattr(SenhaRepository, "marcar_como_chamada", staticmethod(com_concorrente))

    resposta = chamar(client, auth)
    corpo = resposta.get_json()

    assert resposta.status_code == 200
    assert tentativas == [sp["id"], sg["id"]]
    assert corpo["id"] == sg["id"]
    assert db.session.get(Senha, sp["id"]).usuario_id == 2
