from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy import stats

from src.generate import gerar_situacao

TestResult = dict[str, float | str | int]


def analisar_conjunto(dados: pd.DataFrame, nome: str = "simulado") -> pd.DataFrame:
    x = dados["loc"].to_numpy(dtype=float)
    y = dados["defeitos"].to_numpy(dtype=float)
    resultados = []
    for teste, funcao in (("Pearson", stats.pearsonr), ("Spearman", stats.spearmanr)):
        resultado = funcao(x, y)
        coeficiente = float(resultado.statistic)
        p_valor = float(resultado.pvalue)
        resultados.append({
            "conjunto": nome,
            "teste": teste,
            "n": len(dados),
            "estatistica": coeficiente,
            "p_valor": p_valor,
            "significativo_005": p_valor < 0.05,
        })
    return pd.DataFrame(resultados)


def gerar_exemplo(seed: int = 42, n: int = 30, correlacao: float = 0.3) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    dados = gerar_situacao("A", n, correlacao, rng)
    return dados, analisar_conjunto(dados, "Situação A · normal")


def interpretar_resultados(resultados: pd.DataFrame) -> str:
    linhas = []
    for _, linha in resultados.iterrows():
        direcao = "positiva" if linha["estatistica"] > 0 else "negativa" if linha["estatistica"] < 0 else "nula"
        decisao = "há evidência contra H₀" if linha["p_valor"] < 0.05 else "não há evidência suficiente contra H₀"
        p_formatado = "< 0,001" if linha["p_valor"] < 0.001 else f"= {linha['p_valor']:.3f}"
        linhas.append(
            f"{linha['teste']}: associação {direcao} (estatística = {linha['estatistica']:.3f}; "
            f"p {p_formatado}); {decisao}."
        )
    return " ".join(linhas)
