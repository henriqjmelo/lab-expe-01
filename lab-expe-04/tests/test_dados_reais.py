import numpy as np
import pandas as pd
from scipy import stats

from src import params
from src.dados_reais import classificar_efeito, testar_dados_reais


def test_resultados_batem_com_o_scipy_nas_145_classes():
    df = params.carregar_reais()
    res = testar_dados_reais(df).set_index("teste")
    pearson = stats.pearsonr(df[params.COL_LOC], df[params.COL_DEF])
    spearman = stats.spearmanr(df[params.COL_LOC], df[params.COL_DEF])

    assert (res["n"] == 145).all() and (res["gl"] == 143).all()
    assert np.isclose(res.loc["Pearson", "estatistica"], pearson.statistic)
    assert np.isclose(res.loc["Pearson", "p_valor"], pearson.pvalue)
    assert np.isclose(res.loc["Spearman", "estatistica"], spearman.statistic)
    assert np.isclose(res.loc["Spearman", "p_valor"], spearman.pvalue)
    assert (res["decisao"] == "rejeita H₀").all()


def test_ic95_contem_a_estimativa_e_r2_e_o_quadrado():
    res = testar_dados_reais()
    assert (res["ic95_inf"] < res["estatistica"]).all()
    assert (res["estatistica"] < res["ic95_sup"]).all()
    assert np.allclose(res["r2"], res["estatistica"] ** 2)


def test_classificacao_do_tamanho_do_efeito():
    assert [classificar_efeito(v) for v in (0.05, 0.2, -0.4, 0.69)] == [
        "desprezível", "pequeno", "médio", "grande"]


def test_dados_sem_associacao_nao_rejeitam():
    rng = np.random.default_rng(1)
    df = pd.DataFrame({params.COL_LOC: rng.normal(size=200), params.COL_DEF: rng.normal(size=200)})
    assert (testar_dados_reais(df)["decisao"] == "não rejeita H₀").all()
