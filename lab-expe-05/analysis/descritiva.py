"""Estatistica descritiva por celula (coletor x heap x benchmark)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import io_dados

CHAVE = ["gc", "heap_mult", "benchmark"]


def _resumo(s: pd.Series) -> dict:
    s = s.dropna()
    if s.empty:
        return {}
    media = float(s.mean())
    dp = float(s.std(ddof=1)) if len(s) > 1 else 0.0
    q1, q3 = (float(x) for x in np.percentile(s, [25, 75]))
    return {
        "n": int(len(s)),
        "media": media,
        "mediana": float(s.median()),
        "dp": dp,
        "iqr": q3 - q1,
        "minimo": float(s.min()),
        "maximo": float(s.max()),
        # O CV e o numero que dispara o plano B (limiar de 5% no contrato).
        "cv": dp / media if media else np.nan,
        # Media geometrica: coerente com efeito expresso em razao.
        "media_geometrica": float(np.exp(np.log(s).mean())) if (s > 0).all() else np.nan,
    }


def tabela(df: pd.DataFrame, falhas: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por celula x metrica. `falhas` entra como contagem, nunca some."""
    metricas = io_dados.METRICAS_CONFIRMATORIAS + io_dados.METRICAS_EXPLORATORIAS
    n_falhas = falhas.groupby(CHAVE).size() if not falhas.empty else pd.Series(dtype=int)

    linhas = []
    for chave, grupo in df.groupby(CHAVE, sort=True):
        for metrica in metricas:
            r = _resumo(grupo[metrica])
            if not r:
                continue   # p99 nos benchmarks sem latencia: ausencia e dado, nao erro
            linhas.append({
                "gc": chave[0], "heap_mult": chave[1], "benchmark": chave[2],
                "metrica": metrica, **r,
                "n_falhas": int(n_falhas.get(chave, 0)),
            })
    return pd.DataFrame(linhas).sort_values(["metrica", "benchmark", "heap_mult", "gc"]).reset_index(drop=True)


def celulas_acima_do_limiar(descritiva: pd.DataFrame, limiar: float = 0.05,
                            metrica: str = "exec_ms") -> pd.DataFrame:
    """Celulas cujo CV passa do limiar do plano B (contrato, secao 8)."""
    sub = descritiva[(descritiva["metrica"] == metrica) & (descritiva["cv"] > limiar)]
    return sub[["gc", "heap_mult", "benchmark", "n", "cv"]].reset_index(drop=True)
