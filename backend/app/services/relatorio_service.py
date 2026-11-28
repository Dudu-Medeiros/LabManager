from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from app.repositories.relatorio_repository import RelatorioRepository
from app.services.maquina_estados import TRANSICOES_PERMITIDAS, normalizar_estado
from app.services.senha_service import FUSO_BR

TIPOS = ("SP", "SE", "SG")
UTC = timezone.utc
POR_PAGINA_PADRAO = 50
POR_PAGINA_MAXIMA = 200


def _hoje():
    return datetime.now(FUSO_BR).date()


def _para_utc(dia_local):
    return datetime.combine(dia_local, time.min, tzinfo=FUSO_BR).astimezone(UTC).replace(tzinfo=None)


def _formatar_br(dt):
    if not dt:
        return None
    return dt.replace(tzinfo=UTC).astimezone(FUSO_BR).isoformat()


def _primeiro_dia_do_mes_seguinte(dia):
    return date(dia.year + (dia.month == 12), dia.month % 12 + 1, 1)


def _ler_dia(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date(), None
    except (TypeError, ValueError):
        return None, "Data inválida. Use o formato AAAA-MM-DD (ex: 2026-11-21)."


def _ler_mes(texto):
    try:
        return datetime.strptime(texto, "%Y-%m").date(), None
    except (TypeError, ValueError):
        return None, "Mês inválido. Use o formato AAAA-MM (ex: 2026-11)."


def _ler_inteiro(texto, nome, minimo):
    try:
        valor = int(texto)
    except (TypeError, ValueError):
        return None, f"O parâmetro '{nome}' deve ser um número inteiro."
    if valor < minimo:
        return None, f"O parâmetro '{nome}' deve ser maior ou igual a {minimo}."
    return valor, None


def _contar(senhas):
    por_tipo = {
        tipo: {"emitidas": 0, "atendidas": 0, "nao_compareceu": 0, "nao_finalizadas": 0}
        for tipo in TIPOS
    }
    for _numero, tipo, estado in senhas:
        if tipo not in por_tipo:
            continue
        bloco = por_tipo[tipo]
        bloco["emitidas"] += 1
        if estado == "ATENDIDA":
            bloco["atendidas"] += 1
        elif estado == "NAO_COMPARECEU":
            bloco["nao_compareceu"] += 1
        else:
            bloco["nao_finalizadas"] += 1

    totais = {
        chave: sum(bloco[chave] for bloco in por_tipo.values())
        for chave in ("emitidas", "atendidas", "nao_compareceu", "nao_finalizadas")
    }
    return por_tipo, totais


def _media(duracoes):
    if not duracoes:
        return {"amostras": 0, "segundos": None, "minutos": None}
    media = sum(duracoes) / len(duracoes)
    return {"amostras": len(duracoes), "segundos": round(media, 1), "minutos": round(media / 60, 2)}


def _indexar_marcos(marcos):
    por_senha = {}
    for senha_id, tipo, estado, quando in marcos:
        info = por_senha.setdefault(senha_id, {"tipo": tipo})
        info.setdefault(estado, quando)
    return por_senha


def _tempos_medios(por_senha):
    atendimento = defaultdict(list)
    espera = defaultdict(list)
    for info in por_senha.values():
        tipo = info["tipo"]
        if info.get("EM_ATENDIMENTO") and info.get("ATENDIDA"):
            atendimento[tipo].append((info["ATENDIDA"] - info["EM_ATENDIMENTO"]).total_seconds())
        if info.get("AGUARDANDO") and info.get("CHAMADA"):
            espera[tipo].append((info["CHAMADA"] - info["AGUARDANDO"]).total_seconds())

    resultado = {
        tipo: {"atendimento": _media(atendimento[tipo]), "espera": _media(espera[tipo])}
        for tipo in TIPOS
    }
    resultado["geral"] = {
        "atendimento": _media([d for tipo in TIPOS for d in atendimento[tipo]]),
        "espera": _media([d for tipo in TIPOS for d in espera[tipo]]),
    }
    return resultado


def _por_dia(senhas):
    dias = defaultdict(list)
    for linha in senhas:
        dias[linha.numero[:6]].append(linha)

    resultado = []
    for prefixo_dia in sorted(dias):
        _por_tipo, totais = _contar(dias[prefixo_dia])
        data = f"20{prefixo_dia[0:2]}-{prefixo_dia[2:4]}-{prefixo_dia[4:6]}"
        resultado.append({"data": data, **totais})
    return resultado


def _montar_detalhado(detalhes, marcos_por_senha):
    lista = []
    for item in detalhes:
        marcos = marcos_por_senha.get(item.id, {})
        foi_atendida = item.estado_atual == "ATENDIDA"
        data_atendimento = marcos.get("EM_ATENDIMENTO") or marcos.get("ATENDIDA")

        lista.append({
            "senha_id": item.id,
            "numero": item.numero,
            "tipo": item.tipo,
            "estado_atual": item.estado_atual,
            "data_emissao": _formatar_br(item.data_emissao),
            "data_atendimento": _formatar_br(data_atendimento) if foi_atendida else None,
            "guiche": item.guiche if foi_atendida else None,
        })
    return lista


def _montar_indicadores(totais, detalhes):
    emitidas = totais["emitidas"]
    taxa_atendimento = round((totais["atendidas"] / emitidas) * 100, 1) if emitidas else 0.0
    taxa_nao_comparecimento = round((totais["nao_compareceu"] / emitidas) * 100, 1) if emitidas else 0.0

    por_guiche = {}
    por_atendente = {}

    for item in detalhes:
        if item.guiche:
            g = por_guiche.setdefault(
                item.guiche,
                {"guiche": item.guiche, "atendidas": 0, "nao_compareceu": 0, "total": 0}
            )
            g["total"] += 1
            if item.estado_atual == "ATENDIDA":
                g["atendidas"] += 1
            elif item.estado_atual == "NAO_COMPARECEU":
                g["nao_compareceu"] += 1

        if item.usuario_id is not None:
            a = por_atendente.setdefault(
                item.usuario_id,
                {
                    "usuario_id": item.usuario_id,
                    "atendente": item.usuario_nome or f"Usuário #{item.usuario_id}",
                    "atendidas": 0,
                    "nao_compareceu": 0,
                    "total": 0,
                }
            )
            a["total"] += 1
            if item.estado_atual == "ATENDIDA":
                a["atendidas"] += 1
            elif item.estado_atual == "NAO_COMPARECEU":
                a["nao_compareceu"] += 1

    return {
        "taxa_atendimento_percentual": taxa_atendimento,
        "taxa_nao_comparecimento_percentual": taxa_nao_comparecimento,
        "por_guiche": sorted(por_guiche.values(), key=lambda x: x["guiche"]),
        "por_atendente": sorted(por_atendente.values(), key=lambda x: x["atendidas"], reverse=True),
    }


class RelatorioService:
    @staticmethod
    def _montar(periodo, prefixo, incluir_por_dia=False):
        senhas = RelatorioRepository.listar_senhas_por_prefixo(prefixo)
        detalhes = RelatorioRepository.listar_detalhes_senhas_por_prefixo(prefixo)
        marcos = RelatorioRepository.listar_marcos_por_prefixo(
            prefixo, ("AGUARDANDO", "CHAMADA", "CHAMADA_NOVAMENTE", "EM_ATENDIMENTO", "ATENDIDA")
        )
        marcos_por_senha = _indexar_marcos(marcos)
        por_tipo, totais = _contar(senhas)

        relatorio = {
            "periodo": periodo,
            "totais": totais,
            "por_tipo": por_tipo,
            "tempo_medio": _tempos_medios(marcos_por_senha),
            "indicadores": _montar_indicadores(totais, detalhes),
            "detalhado": _montar_detalhado(detalhes, marcos_por_senha),
        }
        if incluir_por_dia:
            relatorio["por_dia"] = _por_dia(senhas)
        return relatorio

    @staticmethod
    def diario(data_texto=None):
        if data_texto:
            dia, erro = _ler_dia(data_texto)
            if erro:
                return None, erro, 400
        else:
            dia = _hoje()

        periodo = {"tipo": "diario", "data": dia.isoformat()}
        return RelatorioService._montar(periodo, dia.strftime("%y%m%d") + "-"), None, 200

    @staticmethod
    def mensal(mes_texto=None):
        if mes_texto:
            dia, erro = _ler_mes(mes_texto)
            if erro:
                return None, erro, 400
        else:
            dia = _hoje().replace(day=1)

        periodo = {"tipo": "mensal", "mes": dia.strftime("%Y-%m")}
        return RelatorioService._montar(periodo, dia.strftime("%y%m"), incluir_por_dia=True), None, 200

    @staticmethod
    def auditoria_senhas(data=None, mes=None, usuario_id=None, numero=None):
        if data and mes:
            return None, "Informe 'data' ou 'mes', não os dois.", 400

        if mes:
            primeiro, erro = _ler_mes(mes)
            if erro:
                return None, erro, 400
            prefixo = primeiro.strftime("%y%m")
            periodo = {"tipo": "mensal", "mes": primeiro.strftime("%Y-%m")}
        else:
            if data:
                primeiro, erro = _ler_dia(data)
                if erro:
                    return None, erro, 400
            else:
                primeiro = _hoje()
            prefixo = primeiro.strftime("%y%m%d") + "-"
            periodo = {"tipo": "diario", "data": primeiro.isoformat()}

        if usuario_id not in (None, ""):
            usuario_id, erro = _ler_inteiro(usuario_id, "usuario_id", 1)
            if erro:
                return None, erro, 400
        else:
            usuario_id = None

        detalhes = RelatorioRepository.listar_detalhes_senhas_por_prefixo(prefixo)
        marcos = RelatorioRepository.listar_marcos_por_prefixo(
            prefixo, ("CHAMADA", "CHAMADA_NOVAMENTE", "EM_ATENDIMENTO", "ATENDIDA")
        )
        marcos_por_senha = _indexar_marcos(marcos)

        registros = []
        for item in detalhes:
            if usuario_id is not None and item.usuario_id != usuario_id:
                continue
            if numero and item.numero != numero:
                continue

            marcos_item = marcos_por_senha.get(item.id, {})
            registros.append({
                "senha_id": item.id,
                "senha": item.numero,
                "tipo": item.tipo,
                "estado_atual": item.estado_atual,
                "atendente": item.usuario_nome,
                "guiche": item.guiche,
                "primeira_chamada": _formatar_br(marcos_item.get("CHAMADA")),
                "segunda_chamada": _formatar_br(marcos_item.get("CHAMADA_NOVAMENTE")),
                "inicio_atendimento": _formatar_br(marcos_item.get("EM_ATENDIMENTO")),
                "fim_atendimento": _formatar_br(marcos_item.get("ATENDIDA")),
            })

        return {
            "periodo": periodo,
            "total": len(registros),
            "registros": registros,
        }, None, 200

    @staticmethod
    def auditoria(data=None, mes=None, usuario_id=None, estado=None, numero=None, pagina=None, por_pagina=None):
        if data and mes:
            return None, "Informe 'data' ou 'mes', não os dois.", 400

        if mes:
            primeiro, erro = _ler_mes(mes)
            if erro:
                return None, erro, 400
            ultimo_exclusivo = _primeiro_dia_do_mes_seguinte(primeiro)
            periodo = {"tipo": "mensal", "mes": primeiro.strftime("%Y-%m")}
        else:
            if data:
                primeiro, erro = _ler_dia(data)
                if erro:
                    return None, erro, 400
            else:
                primeiro = _hoje()
            ultimo_exclusivo = primeiro + timedelta(days=1)
            periodo = {"tipo": "diario", "data": primeiro.isoformat()}

        if usuario_id not in (None, ""):
            usuario_id, erro = _ler_inteiro(usuario_id, "usuario_id", 1)
            if erro:
                return None, erro, 400
        else:
            usuario_id = None

        if estado:
            estado = normalizar_estado(estado)
            if estado not in TRANSICOES_PERMITIDAS:
                estados = ", ".join(TRANSICOES_PERMITIDAS.keys())
                return None, f"Estado inválido. Estados permitidos: {estados}.", 400
        else:
            estado = None

        pagina, erro = _ler_inteiro(pagina if pagina not in (None, "") else 1, "pagina", 1)
        if erro:
            return None, erro, 400
        por_pagina, erro = _ler_inteiro(por_pagina if por_pagina not in (None, "") else POR_PAGINA_PADRAO, "por_pagina", 1)
        if erro:
            return None, erro, 400
        por_pagina = min(por_pagina, POR_PAGINA_MAXIMA)

        linhas, total = RelatorioRepository.buscar_auditoria(
            inicio_utc=_para_utc(primeiro),
            fim_utc=_para_utc(ultimo_exclusivo),
            usuario_id=usuario_id,
            estado=estado,
            numero=numero or None,
            limite=por_pagina,
            deslocamento=(pagina - 1) * por_pagina
        )

        registros = [
            {
                "id": linha.id,
                "senha_id": linha.senha_id,
                "senha_numero": linha.senha_numero,
                "senha_tipo": linha.senha_tipo,
                "guiche": linha.guiche,
                "estado": linha.estado,
                "data_hora": _formatar_br(linha.data_hora),
                "usuario_id": linha.usuario_id,
                "usuario_nome": linha.usuario_nome,
            }
            for linha in linhas
        ]

        return {
            "periodo": periodo,
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "registros": registros,
        }, None, 200