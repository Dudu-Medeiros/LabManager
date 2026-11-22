import random
from datetime import datetime, time, timedelta, timezone
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models.fila import Fila
from app.models.historico import HistoricoEstado
from app.models.senha import Senha
from app.models.usuario import Usuario
from app.repositories.senha_repository import SenhaRepository
from app.services.senha_service import FUSO_BR

UTC = timezone.utc
GUICHES = ["G01", "G02", "G03", "G04"]


def _para_utc(dt_br):
    return dt_br.astimezone(UTC).replace(tzinfo=None)


def _duracao_tm_segundos(tipo):
    if tipo == "SP":
        return int(random.uniform(10, 20) * 60)
    if tipo == "SG":
        return int(random.uniform(2, 8) * 60)
    return 60 if random.random() < 0.95 else 300


def _garantir_usuarios():
    padrao = [
        ("Gestor LabManager", "gestor@labflow.com", "password123", "GESTOR"),
        ("Atendente de Teste", "atendente@labflow.com", "password123", "ATENDENTE"),
        ("Atendente 02", "atendente2@labflow.com", "password123", "ATENDENTE"),
    ]
    for nome, email, senha, perfil in padrao:
        if not Usuario.query.filter_by(email=email).first():
            db.session.add(Usuario(
                nome=nome,
                email=email,
                senha_hash=generate_password_hash(senha),
                perfil=perfil
            ))
    db.session.commit()
    return Usuario.query.filter_by(perfil="ATENDENTE").all()


def _proximo_numero(dia_str, tipo):
    prefixo = f"{dia_str}-{tipo}"
    ultima = SenhaRepository.buscar_ultima_por_prefixo(prefixo)
    if ultima:
        seq = int(ultima.numero.replace(prefixo, "")) + 1
    else:
        seq = 1
    return f"{prefixo}{seq:03d}"


def simular_dia(data_ref, atendentes, quantidade=20):
    dia_str = data_ref.strftime("%y%m%d")
    filas = {f.sigla: f.id for f in Fila.query.all()}
    tipos_pool = ["SP", "SE", "SG"]
    pesos = [0.30, 0.30, 0.40]

    descartes_alvo = max(1, round(quantidade * 0.05))
    indices_descarte = set(random.sample(range(quantidade), descartes_alvo))

    base_br = datetime.combine(data_ref, time(8, 0), tzinfo=FUSO_BR)

    for idx in range(quantidade):
        tipo = random.choices(tipos_pool, weights=pesos, k=1)[0]
        numero = _proximo_numero(dia_str, tipo)
        atendente = random.choice(atendentes)
        guiche = random.choice(GUICHES)

        t_emissao = base_br + timedelta(minutes=idx * 18 + random.randint(0, 6))
        t_espera = t_emissao + timedelta(seconds=15)
        t_chamada = t_espera + timedelta(minutes=random.randint(1, 7))

        nao_compareceu = idx in indices_descarte
        teve_rechamada = nao_compareceu or random.random() < 0.20

        estado_final = "NAO_COMPARECEU" if nao_compareceu else "ATENDIDA"
        senha = Senha(
            numero=numero,
            tipo=tipo,
            estado_atual=estado_final,
            data_emissao=_para_utc(t_emissao),
            guiche=guiche,
            usuario_id=atendente.id,
            fila_id=filas.get(tipo),
            versao=5 if nao_compareceu else (6 if teve_rechamada else 5)
        )
        db.session.add(senha)
        db.session.flush()

        eventos = [
            ("EMITIDA", t_emissao, None),
            ("AGUARDANDO", t_espera, None),
            ("CHAMADA", t_chamada, atendente.id),
        ]

        t_atual = t_chamada
        if teve_rechamada:
            t_atual = t_atual + timedelta(seconds=random.randint(45, 90))
            eventos.append(("CHAMADA_NOVAMENTE", t_atual, atendente.id))

        if nao_compareceu:
            t_atual = t_atual + timedelta(seconds=random.randint(45, 90))
            eventos.append(("NAO_COMPARECEU", t_atual, atendente.id))
        else:
            t_inicio = t_atual + timedelta(seconds=random.randint(20, 60))
            t_fim = t_inicio + timedelta(seconds=_duracao_tm_segundos(tipo))
            eventos.append(("EM_ATENDIMENTO", t_inicio, atendente.id))
            eventos.append(("ATENDIDA", t_fim, atendente.id))

        for estado, momento, uid in eventos:
            db.session.add(HistoricoEstado(
                senha_id=senha.id,
                estado=estado,
                data_hora=_para_utc(momento),
                usuario_id=uid
            ))

    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        atendentes = _garantir_usuarios()
        hoje = datetime.now(FUSO_BR).date()
        ontem = hoje - timedelta(days=1)

        simular_dia(ontem, atendentes, quantidade=20)
        simular_dia(hoje, atendentes, quantidade=20)
        print(f"Simulação concluída: 20 senhas geradas para {ontem} e 20 para {hoje}.")


if __name__ == "__main__":
    main()