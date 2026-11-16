"""As primitivas estatisticas, conferidas contra referencias independentes."""
import numpy as np
import pytest
from statsmodels.stats.multitest import multipletests

from analysis import estatistica as est


def test_holm_bate_com_o_statsmodels():
    ps = [0.001, 0.012, 0.03, 0.2, 0.45, 0.9, 0.004, 0.07]
    esperado = list(multipletests(ps, method="holm")[1])
    assert est.holm(ps) == pytest.approx(esperado)


def test_bh_bate_com_o_statsmodels():
    ps = [0.001, 0.012, 0.03, 0.2, 0.45, 0.9, 0.004, 0.07]
    esperado = list(multipletests(ps, method="fdr_bh")[1])
    assert est.benjamini_hochberg(ps) == pytest.approx(esperado)


def test_holm_nunca_rejeita_menos_que_bonferroni():
    rng = np.random.default_rng(0)
    ps = list(rng.uniform(0, 0.2, 12))
    holm = np.array(est.holm(ps))
    bonferroni = np.minimum(np.array(ps) * 12, 1.0)
    assert (holm <= bonferroni + 1e-12).all()


def test_holm_e_monotono():
    ps = [0.03, 0.001, 0.2, 0.012]
    corrigidos = est.holm(ps)
    ordem_p = np.argsort(ps)
    assert list(np.argsort(np.array(corrigidos)[ordem_p])) == list(range(len(ps)))


def test_hedges_g_e_menor_que_cohen_d():
    rng = np.random.default_rng(1)
    a, b = rng.normal(1, 1, 20), rng.normal(0, 1, 20)
    gl = 38
    s = np.sqrt((19 * a.var(ddof=1) + 19 * b.var(ddof=1)) / gl)
    d = (a.mean() - b.mean()) / s
    assert abs(est.hedges_g(a, b)) < abs(d)
    assert est.hedges_g(a, b) == pytest.approx(d * (1 - 3 / (4 * gl - 1)))


def test_cliff_delta_nos_extremos():
    assert est.cliff_delta(np.array([5, 6, 7]), np.array([1, 2, 3])) == 1.0
    assert est.cliff_delta(np.array([1, 2, 3]), np.array([5, 6, 7])) == -1.0
    assert est.cliff_delta(np.array([1, 2, 3]), np.array([1, 2, 3])) == pytest.approx(0.0)


def test_bootstrap_cobre_a_razao_verdadeira():
    rng = np.random.default_rng(42)
    g1 = rng.lognormal(0, 0.04, 40)
    zgc = rng.lognormal(np.log(1.07), 0.04, 40)
    razao, baixo, alto = est.ic_bootstrap_bca(zgc, g1)
    assert baixo < 1.07 < alto
    assert baixo < razao < alto


def test_bootstrap_e_deterministico_pela_semente():
    rng = np.random.default_rng(5)
    g1, zgc = rng.lognormal(0, 0.05, 25), rng.lognormal(0.05, 0.05, 25)
    assert est.ic_bootstrap_bca(zgc, g1) == est.ic_bootstrap_bca(zgc, g1)


def test_bootstrap_de_amostras_identicas_fica_em_torno_de_um():
    v = np.linspace(100, 110, 30)
    razao, baixo, alto = est.ic_bootstrap_bca(v, v.copy())
    assert razao == pytest.approx(1.0)
    assert baixo <= 1.0 <= alto
