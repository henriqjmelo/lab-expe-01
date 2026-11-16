"""A arvore de decisao do plano de analise, aplicada par a par.

Um par = (benchmark, heap_mult), comparando G1 contra ZGC. Cada par rende um
teste. A arvore esta em docs/04-plano-analise.md, secao 5, e o codigo abaixo e
a traducao literal dela - inclusive a regra de desempate.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import estatistica as est
from . import io_dados

ALFA = 0.05
ALFA_SHAPIRO = 0.01   # tela conservadora: o padrao e ficar no parametrico
N_MINIMO = 10         # abaixo disso o par sai dos confirmatorios e o k cai


def _amostras(df: pd.DataFrame, metrica: str, benchmark: str, heap: float):
    sub = df[(df["benchmark"] == benchmark) & (df["heap_mult"] == heap) & df[metrica].notna()]
    g1 = sub.loc[sub["gc"] == "G1", metrica].to_numpy(dtype=float)
    zgc = sub.loc[sub["gc"] == "ZGC", metrica].to_numpy(dtype=float)
    return g1, zgc


def comparar_par(
    g1: np.ndarray,
    zgc: np.ndarray,
    *,
    metrica: str,
    benchmark: str,
    heap: float,
    papel: str,
    bootstrap: bool = True,
) -> dict:
    """Roda a arvore num par e devolve a linha da tabela de saida."""
    # O esquema da linha e sempre o mesmo, inclusive quando o par nao roda: o
    # contrato promete essas colunas, e um piloto de 5 blocos (que fica abaixo
    # do n minimo) nao pode produzir uma tabela com colunas faltando.
    linha = {
        "metrica": metrica, "benchmark": benchmark, "heap_mult": heap, "papel": papel,
        "n_g1": len(g1), "n_zgc": len(zgc),
        "teste": "", "estatistica": np.nan, "p": np.nan,
        "efeito": "", "efeito_valor": np.nan,
        "razao": np.nan, "razao_ic_baixo": np.nan, "razao_ic_alto": np.nan,
        "shapiro_g1": np.nan, "shapiro_zgc": np.nan, "levene_p": np.nan,
        "teste_sensibilidade": "", "p_sensibilidade": np.nan,
        "concordam": False, "motivo": "",
    }
    if len(g1) < N_MINIMO or len(zgc) < N_MINIMO:
        linha.update({"teste": "sem_poder", "motivo": f"n < {N_MINIMO} em algum grupo"})
        return linha

    log_g1, log_zgc = np.log(g1), np.log(zgc)
    sh_g1 = float(stats.shapiro(log_g1).pvalue)
    sh_zgc = float(stats.shapiro(log_zgc).pvalue)
    normal = sh_g1 > ALFA_SHAPIRO and sh_zgc > ALFA_SHAPIRO
    levene = float(stats.levene(log_g1, log_zgc, center="median").pvalue)

    # Os DOIS testes rodam sempre: o principal sai da tela de normalidade, o
    # outro vira analise de sensibilidade. Isso tira do caminho a critica de
    # "escolheram o teste que deu o resultado que queriam".
    welch = stats.ttest_ind(log_zgc, log_g1, equal_var=False)
    mw = stats.mannwhitneyu(zgc, g1, alternative="two-sided")

    if normal:
        principal, sens = "welch", "mann_whitney"
        p, estatistica = float(welch.pvalue), float(welch.statistic)
        p_sens = float(mw.pvalue)
        nome_efeito, valor_efeito = "hedges_g", est.hedges_g(log_zgc, log_g1)
        f_razao = est.razao_media_geometrica
    else:
        principal, sens = "mann_whitney", "welch"
        p, estatistica = float(mw.pvalue), float(mw.statistic)
        p_sens = float(welch.pvalue)
        nome_efeito, valor_efeito = "cliff_delta", est.cliff_delta(zgc, g1)
        f_razao = est.razao_mediana

    if bootstrap:
        razao, ic_baixo, ic_alto = est.ic_bootstrap_bca(zgc, g1, f_razao)
    else:
        razao, ic_baixo, ic_alto = f_razao(zgc, g1), np.nan, np.nan

    linha.update({
        "teste": principal, "estatistica": estatistica, "p": p,
        "efeito": nome_efeito, "efeito_valor": valor_efeito,
        "razao": razao, "razao_ic_baixo": ic_baixo, "razao_ic_alto": ic_alto,
        "shapiro_g1": sh_g1, "shapiro_zgc": sh_zgc, "levene_p": levene,
        "teste_sensibilidade": sens, "p_sensibilidade": p_sens,
        "concordam": bool((p < ALFA) == (p_sens < ALFA)),
        "motivo": "",
    })
    return linha


def _familia(df: pd.DataFrame, metricas: list[str], papel: str, correcao, nome_correcao: str,
             bootstrap: bool = True) -> pd.DataFrame:
    linhas = []
    for metrica in io_dados.metricas_presentes(df, metricas):
        for benchmark, heap in io_dados.pares(df, metrica):
            g1, zgc = _amostras(df, metrica, benchmark, heap)
            linhas.append(comparar_par(g1, zgc, metrica=metrica, benchmark=benchmark,
                                       heap=heap, papel=papel, bootstrap=bootstrap))
    tabela = pd.DataFrame(linhas)
    if tabela.empty:
        return tabela

    # Pares sem poder nao entram na correcao: o k e o numero de testes que de
    # fato rodaram, e a tabela registra quem ficou de fora e por que.
    entra = tabela["p"].notna()
    tabela["p_corrigido"] = np.nan
    tabela.loc[entra, "p_corrigido"] = correcao(list(tabela.loc[entra, "p"]))
    tabela["correcao"] = nome_correcao
    tabela["k_familia"] = int(entra.sum())
    tabela["significativo"] = tabela["p_corrigido"] < ALFA
    return tabela.sort_values(["metrica", "benchmark", "heap_mult"]).reset_index(drop=True)


def confirmatorios(df: pd.DataFrame, bootstrap: bool = True) -> pd.DataFrame:
    """Os 12 testes confirmatorios (8 de tempo + 4 de p99), com Holm."""
    return _familia(df, io_dados.METRICAS_CONFIRMATORIAS, "confirmatoria",
                    est.holm, "holm", bootstrap)


def exploratorios(df: pd.DataFrame, bootstrap: bool = True) -> pd.DataFrame:
    """Pausa maxima, CPU e RSS, com BH (FDR) na propria familia."""
    return _familia(df, io_dados.METRICAS_EXPLORATORIAS, "exploratoria",
                    est.benjamini_hochberg, "benjamini_hochberg", bootstrap)
