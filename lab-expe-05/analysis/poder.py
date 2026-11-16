"""Poder por simulacao de Monte Carlo - reuso direto do Lab04.

Gera a tabela da secao 9.2 do plano de analise. A ideia e a mesma do Lab04:
em vez de confiar numa formula fechada, finge-se o mundo milhares de vezes com
a resposta conhecida e conta-se quantas vezes o teste acerta.

    poder   = com efeito real plantado, quantas vezes o teste rejeita H0
    erro I  = sem efeito nenhum, quantas vezes o teste rejeita assim mesmo
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

REPETICOES = 10_000
SEMENTE = 42
ALFA = 0.05
K_CONFIRMATORIOS = 12   # a familia do Holm
CVS = (0.02, 0.03, 0.05, 0.08)
NS = (20, 30, 40, 50)
EFEITO_PADRAO = 1.05    # menor efeito de interesse pratico do exec_ms


def simular(n: int, cv: float, razao: float, repeticoes: int = REPETICOES,
            semente: int = SEMENTE) -> tuple[np.ndarray, np.ndarray]:
    """Devolve os p do Welch e do Mann-Whitney em `repeticoes` experimentos."""
    rng = np.random.default_rng(semente)
    sigma = np.sqrt(np.log(1 + cv**2))
    g1 = rng.lognormal(0.0, sigma, size=(repeticoes, n))
    zgc = rng.lognormal(np.log(razao), sigma, size=(repeticoes, n))
    welch = stats.ttest_ind(np.log(zgc), np.log(g1), equal_var=False, axis=1)
    mw = stats.mannwhitneyu(zgc, g1, alternative="two-sided", axis=1)
    return welch.pvalue, mw.pvalue


def tabela(cvs=CVS, ns=NS, razao: float = EFEITO_PADRAO,
           repeticoes: int = REPETICOES, semente: int = SEMENTE) -> pd.DataFrame:
    """Poder nos dois extremos entre os quais o Holm opera: alfa e alfa/12.

    O Holm compara o menor p contra alfa/12 e o maior contra alfa. O poder real
    de cada par fica entre as duas colunas; reportar so uma esconderia metade
    da historia.
    """
    linhas = []
    for cv in cvs:
        for n in ns:
            p_welch, p_mw = simular(n, cv, razao, repeticoes, semente)
            linhas.append({
                "cv": cv, "n": n, "razao": razao, "repeticoes": repeticoes,
                "poder_welch_alfa": float((p_welch < ALFA).mean()),
                "poder_welch_holm_pior": float((p_welch < ALFA / K_CONFIRMATORIOS).mean()),
                "poder_mw_alfa": float((p_mw < ALFA).mean()),
                "poder_mw_holm_pior": float((p_mw < ALFA / K_CONFIRMATORIOS).mean()),
            })
    return pd.DataFrame(linhas)


def erro_tipo_i(n: int = 30, cv: float = 0.05, repeticoes: int = REPETICOES,
                semente: int = SEMENTE) -> dict:
    """Calibracao: sem efeito nenhum, a taxa de rejeicao tem de bater com alfa."""
    p_welch, p_mw = simular(n, cv, 1.0, repeticoes, semente)
    return {
        "n": n, "cv": cv, "alfa_nominal": ALFA,
        "welch": float((p_welch < ALFA).mean()),
        "mann_whitney": float((p_mw < ALFA).mean()),
    }


def n_para_poder(cv: float, alvo: float = 0.80, razao: float = EFEITO_PADRAO,
                 alfa: float = ALFA / K_CONFIRMATORIOS, maximo: int = 400,
                 repeticoes: int = 4000, semente: int = 7) -> int | None:
    """Menor N (de 5 em 5) que atinge o poder alvo no pior caso do Holm."""
    for n in range(10, maximo + 1, 5):
        p_welch, _ = simular(n, cv, razao, repeticoes, semente)
        if (p_welch < alfa).mean() >= alvo:
            return n
    return None
