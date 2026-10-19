from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analise.rq06_robustez import ajustar_regressao, coeficientes, correlacao_parcial, vif_preditores


def dados_confundidos(n=400, semente=0):
    rng = np.random.default_rng(semente)
    z = rng.normal(size=n)
    x = z + rng.normal(scale=0.3, size=n)
    y = 2.0 * z + rng.normal(scale=0.3, size=n)
    return pd.DataFrame({"x": x, "y": y, "z": z})


def dados_efeito_direto(n=400, semente=1, beta=1.5):
    rng = np.random.default_rng(semente)
    z = rng.normal(size=n)
    x = rng.normal(size=n)
    y = beta * x + 0.5 * z + rng.normal(scale=0.3, size=n)
    return pd.DataFrame({"x": x, "y": y, "z": z})


def test_correlacao_parcial_cai_quando_o_efeito_e_so_do_confundidor():
    df = dados_confundidos()
    simples = df["x"].corr(df["y"], method="spearman")
    parcial = correlacao_parcial(df, "x", "y", ["z"])

    assert simples > 0.7
    assert abs(parcial["rho_parcial"]) < 0.25
    assert parcial["n"] == len(df)


def test_correlacao_parcial_mantem_efeito_direto():
    df = dados_efeito_direto()
    parcial = correlacao_parcial(df, "x", "y", ["z"])

    assert parcial["rho_parcial"] > 0.7
    assert parcial["p"] < 0.001


def test_correlacao_parcial_sem_graus_de_liberdade_devolve_nan():
    df = dados_confundidos(n=3)
    parcial = correlacao_parcial(df, "x", "y", ["z"])

    assert parcial["gl"] <= 0
    assert np.isnan(parcial["rho_parcial"])


def test_regressao_recupera_coeficiente_conhecido():
    rng = np.random.default_rng(2)
    n = 500
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    y = 3.0 + 2.0 * x1 + 0.0 * x2 + rng.normal(scale=0.5, size=n)
    exog = pd.DataFrame({"x1": x1, "x2": x2})

    modelo = ajustar_regressao(exog, y)
    tabela = coeficientes(modelo).set_index("preditor")

    assert tabela.loc["x1", "ic_lo"] < 2.0 < tabela.loc["x1", "ic_hi"]
    assert tabela.loc["x2", "ic_lo"] < 0.0 < tabela.loc["x2", "ic_hi"]


def test_vif_alto_quando_preditores_sao_quase_iguais():
    rng = np.random.default_rng(3)
    n = 300
    base = rng.normal(size=n)
    exog = pd.DataFrame({
        "a": base,
        "b": base + rng.normal(scale=0.01, size=n),
        "c": rng.normal(size=n),
    })

    tabela = vif_preditores(exog).set_index("preditor")

    assert tabela.loc["a", "vif"] > 5
    assert tabela.loc["b", "vif"] > 5
    assert tabela.loc["c", "vif"] < 5
