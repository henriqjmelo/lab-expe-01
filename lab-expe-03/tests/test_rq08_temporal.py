from __future__ import annotations

import math

from analise.rq08_temporal import (
    classificar_tendencia,
    meses_da_janela,
    periodo_de,
    serie_cfr,
    serie_frequencia,
    serie_lead_time,
    trimestres_da_janela,
)
from metricas.cfr import cfr_ci
from metricas.frequencia import frequencia_semanal

INICIO, FIM = "2025-10-01T00:00:00Z", "2026-10-01T00:00:00Z"


def test_meses_da_janela_tem_doze_periodos():
    meses = meses_da_janela(INICIO, FIM)

    assert len(meses) == 12
    assert meses[0][0] == "2025-10"
    assert meses[-1][0] == "2026-09"


def test_trimestres_da_janela_tem_quatro_periodos():
    trimestres = trimestres_da_janela(INICIO, FIM)

    assert [t[0] for t in trimestres] == ["T1", "T2", "T3", "T4"]
    assert trimestres[0][1] == INICIO
    assert trimestres[-1][2] == FIM


def test_fronteira_antes_da_meia_noite_cai_no_periodo_anterior():
    meses = meses_da_janela(INICIO, FIM)
    trimestres = trimestres_da_janela(INICIO, FIM)

    assert periodo_de("2025-12-31T23:59:59Z", meses) == "2025-12"
    assert periodo_de("2025-12-31T23:59:59Z", trimestres) == "T1"


def test_fronteira_na_meia_noite_cai_no_proximo_periodo():
    meses = meses_da_janela(INICIO, FIM)
    trimestres = trimestres_da_janela(INICIO, FIM)

    assert periodo_de("2026-01-01T00:00:00Z", meses) == "2026-01"
    assert periodo_de("2026-01-01T00:00:00Z", trimestres) == "T2"


def test_data_fora_da_janela_nao_cai_em_nenhum_periodo():
    meses = meses_da_janela(INICIO, FIM)

    assert periodo_de("2026-10-01T00:00:00Z", meses) is None
    assert periodo_de("2024-01-01T00:00:00Z", meses) is None


def test_serie_crescente_classifica_melhora_quando_subir_e_bom():
    serie = [float(i) for i in range(12)]

    r = classificar_tendencia(serie, melhora_se_sobe=True)

    assert r["status"] == "melhora"
    assert r["tendencia"] == "increasing"


def test_serie_crescente_classifica_piora_quando_subir_e_ruim():
    # lead time e CFR: subir e ruim, entao uma serie crescente e piora
    serie = [float(i) for i in range(12)]

    r = classificar_tendencia(serie, melhora_se_sobe=False)

    assert r["status"] == "piora"


def test_serie_decrescente_classifica_melhora_para_lead_time():
    serie = [float(12 - i) for i in range(12)]

    r = classificar_tendencia(serie, melhora_se_sobe=False)

    assert r["status"] == "melhora"
    assert r["tendencia"] == "decreasing"


def test_serie_constante_nao_tem_tendencia():
    serie = [5.0] * 12

    r = classificar_tendencia(serie, melhora_se_sobe=True)

    assert r["status"] == "sem_tendencia"
    assert r["tendencia"] == "no trend"


def test_serie_toda_nan_apos_passar_por_dataframe_e_insuficiente():
    # pd.DataFrame(...) converte None em NaN nas colunas numericas (pandas 3.x);
    # classificar_tendencia tem que tratar NaN igual a None, senao o pymannkendall
    # recebe menos pontos validos do que o esperado e quebra (ver issue #158)
    import pandas as pd

    # precisa de um float real em algum lugar da coluna pra forçar dtype float64;
    # so assim o pandas converte os None dessa linha em NaN (reproduz o bug real)
    df = pd.DataFrame({"grupo": ["a"] * 12 + ["b"], "valor": [None] * 12 + [1.0]})
    serie = df[df["grupo"] == "a"]["valor"].tolist()
    assert any(v != v for v in serie)  # confirma que virou NaN, nao None

    r = classificar_tendencia(serie, melhora_se_sobe=True)

    assert r["status"] == "insuficiente"
    assert r["n"] == 0


def test_poucos_pontos_validos_e_insuficiente():
    serie = [1.0, 2.0, 3.0] + [None] * 9

    r = classificar_tendencia(serie, melhora_se_sobe=True)

    assert r["status"] == "insuficiente"
    assert r["p"] is None


def test_serie_frequencia_bate_com_frequencia_semanal_da_janela_inteira():
    datas = ["2025-11-05T00:00:00Z", "2026-03-20T00:00:00Z", "2026-08-01T00:00:00Z"]
    periodo_unico = [("janela", INICIO, FIM)]

    serie = serie_frequencia(datas, periodo_unico)

    assert serie["janela"] == frequencia_semanal(datas, INICIO, FIM)


def test_serie_lead_time_trata_release_sem_commits_novos_como_vazio_nao_nan():
    # release nao ignorada mas sem commit novo: pipeline/exportar.py grava lt_a_dias
    # vazio (NaN depois do pandas), e isso tem que virar None, nunca entrar como nan
    # numa serie, porque nan quebra o pymannkendall (ver issue #158)
    releases = [
        {"published_at": "2025-11-01T00:00:00Z", "lt_a_dias": math.nan, "ignorada": False},
        {"published_at": "2025-11-15T00:00:00Z", "lt_a_dias": 5.0, "ignorada": False},
    ]
    periodo_unico = [("janela", INICIO, FIM)]

    serie = serie_lead_time(releases, periodo_unico)

    assert serie["janela"] == 5.0


def test_serie_cfr_bate_com_cfr_ci_da_janela_inteira():
    pares = [
        ("2025-11-05T00:00:00Z", "success"),
        ("2025-12-01T00:00:00Z", "failure"),
        ("2026-02-01T00:00:00Z", "success"),
        ("2026-02-02T00:00:00Z", "cancelled"),
    ]
    periodo_unico = [("janela", INICIO, FIM)]

    serie = serie_cfr(pares, periodo_unico)

    assert serie["janela"] == cfr_ci([c for _, c in pares])["cfr"]
