from __future__ import annotations

import math
import statistics

ELITE, HIGH, MEDIUM, LOW = 4, 3, 2, 1
NOMES = {ELITE: "Elite", HIGH: "High", MEDIUM: "Medium", LOW: "Low"}

SEMANAS_POR_MES = 52.143 / 12


def _vazio(valor: float | None) -> bool:
    return valor is None or (isinstance(valor, float) and math.isnan(valor))


def classificar_frequencia(por_semana: float | None) -> int | None:
    if _vazio(por_semana):
        return None
    if por_semana >= 7:
        return ELITE
    if por_semana >= 1:
        return HIGH
    if por_semana >= 1 / SEMANAS_POR_MES:
        return MEDIUM
    return LOW


def classificar_lead_time(dias: float | None) -> int | None:
    if _vazio(dias):
        return None
    if dias < 1:
        return ELITE
    if dias < 7:
        return HIGH
    if dias < 30:
        return MEDIUM
    return LOW


def classificar_cfr(taxa: float | None) -> int | None:
    if _vazio(taxa):
        return None
    if taxa <= 0.15:
        return ELITE
    if taxa <= 0.30:
        return HIGH
    if taxa <= 0.45:
        return MEDIUM
    return LOW


def classificar_recuperacao(horas: float | None) -> int | None:
    if _vazio(horas):
        return None
    if horas < 1:
        return ELITE
    if horas < 24:
        return HIGH
    if horas < 24 * 7:
        return MEDIUM
    return LOW


def classificacao_geral(pontos: list[int | None]) -> int | None:
    validos = [p for p in pontos if p is not None]
    if not validos:
        return None
    return math.floor(statistics.median(validos))


def classificar(
    frequencia: float | None, lead_time: float | None, cfr: float | None, recuperacao: float | None
) -> dict[str, int | None]:
    pontos = {
        "frequencia": classificar_frequencia(frequencia),
        "lead_time": classificar_lead_time(lead_time),
        "cfr": classificar_cfr(cfr),
        "recuperacao": classificar_recuperacao(recuperacao),
    }
    pontos["geral"] = classificacao_geral(list(pontos.values()))
    return pontos
