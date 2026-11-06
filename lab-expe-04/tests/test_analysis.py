import numpy as np
import pandas as pd
from scipy import stats

from src.analysis import analisar_conjunto, gerar_exemplo, interpretar_resultados
from src.dashboard_demo import renderizar_exemplo
from src.generate import gerar_normal


def test_resultados_de_pearson_e_spearman_coincidem_com_scipy():
    dados = gerar_normal(30, 0.3, np.random.default_rng(42))

    resultado = analisar_conjunto(dados, "teste").set_index("teste")
    pearson = stats.pearsonr(dados["loc"], dados["defeitos"])
    spearman = stats.spearmanr(dados["loc"], dados["defeitos"])

    assert np.isclose(resultado.loc["Pearson", "estatistica"], pearson.statistic)
    assert np.isclose(resultado.loc["Pearson", "p_valor"], pearson.pvalue)
    assert np.isclose(resultado.loc["Spearman", "estatistica"], spearman.statistic)
    assert np.isclose(resultado.loc["Spearman", "p_valor"], spearman.pvalue)
    assert (resultado["n"] == 30).all()


def test_exemplo_e_interpretacao_contem_os_dois_testes():
    dados, resultados = gerar_exemplo(seed=42, n=30, correlacao=0.3)

    texto = interpretar_resultados(resultados)

    assert len(dados) == 30
    assert set(resultados["teste"]) == {"Pearson", "Spearman"}
    assert "Pearson" in texto and "Spearman" in texto
    assert all(0 <= p <= 1 for p in resultados["p_valor"])


def test_componente_do_dashboard_renderiza_tabela_e_texto():
    class DashboardFalso:
        def __init__(self):
            self.elementos = []

        def __getattr__(self, nome):
            return lambda *args, **kwargs: self.elementos.append((nome, args, kwargs))

    dashboard = DashboardFalso()

    dados = renderizar_exemplo(dashboard)

    assert len(dados) == 30
    assert any(nome == "dataframe" for nome, _, _ in dashboard.elementos)
    assert sum(nome == "markdown" for nome, _, _ in dashboard.elementos) >= 2