TRANSICOES_PERMITIDAS = {
    "EMITIDA": {"AGUARDANDO"},
    "AGUARDANDO": {"CHAMADA"},
    "CHAMADA": {"CHAMADA_NOVAMENTE", "EM_ATENDIMENTO", "NAO_COMPARECEU"},
    "CHAMADA_NOVAMENTE": {"EM_ATENDIMENTO", "NAO_COMPARECEU"},
    "EM_ATENDIMENTO": {"ATENDIDA"},
    "ATENDIDA": set(),
    "NAO_COMPARECEU": set(),
}

def normalizar_estado(estado):
    if not isinstance(estado, str):
        return ""
    return estado.strip().upper().replace("Ã", "A")

def validar_transicao(estado_atual, novo_estado):
    atual = normalizar_estado(estado_atual)
    destino = normalizar_estado(novo_estado)

    if destino not in TRANSICOES_PERMITIDAS:
        estados = ", ".join(TRANSICOES_PERMITIDAS.keys())
        return False, None, f"Estado inválido '{novo_estado}'. Estados permitidos: {estados}."

    permitidos = TRANSICOES_PERMITIDAS.get(atual, set())
    if destino not in permitidos:
        if not permitidos:
            return False, None, f"A senha está no estado final '{atual}' e não pode mais ser alterada."
        proximos = ", ".join(sorted(permitidos))
        return False, None, f"Transição proibida: '{atual}' -> '{destino}'. Permitidos a partir de '{atual}': {proximos}."

    return True, destino, None