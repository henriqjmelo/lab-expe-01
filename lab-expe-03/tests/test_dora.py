from __future__ import annotations

import math

import pytest

from metricas.dora import (
    ELITE,
    HIGH,
    LOW,
    MEDIUM,
    classificacao_geral,
    classificar,
    classificar_cfr,
    classificar_frequencia,
    classificar_lead_time,
    classificar_recuperacao,
)


@pytest.mark.parametrize(
    "por_semana, esperado",
    [(7, ELITE), (10, ELITE), (6.99, HIGH), (1, HIGH), (0.99, MEDIUM), (0.2302, MEDIUM), (0.2298, LOW), (0, LOW)],
)
def test_frequencia_nas_fronteiras(por_semana, esperado):
    assert classificar_frequencia(por_semana) == esperado


@pytest.mark.parametrize("dias, esperado", [(0.5, ELITE), (1, HIGH), (6.99, HIGH), (7, MEDIUM), (29.9, MEDIUM), (30, LOW)])
def test_lead_time_nas_fronteiras(dias, esperado):
    assert classificar_lead_time(dias) == esperado


@pytest.mark.parametrize("taxa, esperado", [(0, ELITE), (0.15, ELITE), (0.151, HIGH), (0.30, HIGH), (0.45, MEDIUM), (0.46, LOW)])
def test_cfr_nas_fronteiras(taxa, esperado):
    assert classificar_cfr(taxa) == esperado


@pytest.mark.parametrize("horas, esperado", [(0.5, ELITE), (1, HIGH), (23.9, HIGH), (24, MEDIUM), (167, MEDIUM), (168, LOW)])
def test_recuperacao_nas_fronteiras(horas, esperado):
    assert classificar_recuperacao(horas) == esperado


@pytest.mark.parametrize("funcao", [classificar_frequencia, classificar_lead_time, classificar_cfr, classificar_recuperacao])
def test_valor_ausente_nao_classifica(funcao):
    assert funcao(None) is None
    assert funcao(math.nan) is None


def test_exemplo_do_enunciado_mediana_arredondada_para_baixo():
    assert classificacao_geral([4, 3, 3, 1]) == HIGH
    assert classificacao_geral([4, 3, 2, 1]) == MEDIUM


def test_classificacao_geral_ignora_metricas_ausentes():
    assert classificacao_geral([4, None, 4, None]) == ELITE
    assert classificacao_geral([None, None]) is None


def test_classificar_completo():
    r = classificar(frequencia=2, lead_time=3, cfr=0.05, recuperacao=None)
    assert r == {"frequencia": HIGH, "lead_time": HIGH, "cfr": ELITE, "recuperacao": None, "geral": HIGH}
    assert classificar(0.1, 40, 0.5, 200)["geral"] == LOW
