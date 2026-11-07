import numpy as np
import pytest
from scipy import stats

from src import simulate


def _lote(situacao, r=0.3, n_rep=60, n=30, seed=7):
    return simulate.gerar_lote(situacao, r, n_rep, n, np.random.default_rng(seed))


@pytest.mark.parametrize("situacao", ["A", "B"])
def test_pvalores_batem_com_o_scipy_linha_a_linha(situacao):
    x, y = _lote(situacao)

    r, p = simulate.pearson_vetorizado(x, y)
    rho, p_s = simulate.spearman_vetorizado(x, y)

    for i in range(len(x)):
        pearson = stats.pearsonr(x[i], y[i])
        spearman = stats.spearmanr(x[i], y[i])
        assert np.isclose(r[i], pearson.statistic)
        assert np.isclose(p[i], pearson.pvalue)
        assert np.isclose(rho[i], spearman.statistic)
        assert np.isclose(p_s[i], spearman.pvalue)


def test_formato_das_matrizes_e_situacao_invalida():
    x, y = _lote("B", n_rep=10, n=30)
    assert x.shape == y.shape == (10, 30)
    assert (x > 0).all() and (y > 0).all()  # lognormal nunca e negativa
    with pytest.raises(ValueError):
        simulate.gerar_lote("C", 0.0, 5, 30, np.random.default_rng(1))
    with pytest.raises(ValueError):
        simulate.gerar_lote("A", 1.5, 5, 30, np.random.default_rng(1))


def test_correlacao_do_gerador_vetorizado_acompanha_r_latente():
    x, y = simulate.gerar_lote("A", 0.5, 4000, 30, np.random.default_rng(3))
    assert abs(simulate.correlacao_por_linha(x, y).mean() - 0.5) < 0.02


def test_mesma_semente_gera_o_mesmo_resultado():
    a = simulate.simular_situacao("A", efeitos=(0.0, 0.3), n_rep=500)
    b = simulate.simular_situacao("A", efeitos=(0.0, 0.3), n_rep=500)
    assert a.equals(b)


def test_celulas_do_csv_e_taxas_coerentes():
    df = simulate.simular_situacao("A", n_rep=2000)
    assert len(df) == 12  # 6 efeitos x 2 testes
    assert set(df["teste"]) == {"Pearson", "Spearman"}
    assert (df["taxa_001"] <= df["taxa_005"]).all()
    assert np.allclose(df["taxa_005"], df["rejeicoes_005"] / df["repeticoes"])


def test_erro_tipo_i_perto_de_5_porcento_e_poder_cresce_com_r():
    df = simulate.simular_situacao("A", n_rep=10_000)
    nulo = df[df["r_latente"] == 0.0]
    assert (abs(nulo["taxa_005"] - 0.05) < 0.01).all()
    for teste in ("Pearson", "Spearman"):
        poder = df[df["teste"] == teste].sort_values("r_latente")["taxa_005"].to_numpy()
        assert (np.diff(poder) > 0).all()
