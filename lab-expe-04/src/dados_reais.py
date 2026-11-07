"""Pearson e Spearman nas 145 classes reais do KC1 (secao 6 do dashboard).

Mede LOC x defeitos com os dois testes, bicaudal, alfa = 0,05, e reporta o tamanho do efeito
(o proprio r ou rho, mais r^2 e o IC de 95% por Fisher).

    python src/dados_reais.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

_RAIZ = Path(__file__).resolve().parent.parent
for _caminho in (_RAIZ, _RAIZ / "src"):
    if str(_caminho) not in sys.path:
        sys.path.insert(0, str(_caminho))

import params  # noqa: E402


def classificar_efeito(coef: float) -> str:
    """Rotulos de Cohen (1988) para correlacao: |r| < 0,1 desprezivel, 0,1 pequeno, 0,3 medio, 0,5 grande."""
    a = abs(coef)
    if a < 0.1:
        return "desprezível"
    if a < 0.3:
        return "pequeno"
    if a < 0.5:
        return "médio"
    return "grande"


def _ic95(coef: float, n: int, spearman: bool) -> tuple[float, float]:
    """IC de 95% pela transformacao de Fisher; para Spearman, erro-padrao de Bonett e Wright."""
    var = (1 + coef**2 / 2) / (n - 3) if spearman else 1 / (n - 3)
    z, half = np.arctanh(coef), stats.norm.ppf(0.975) * np.sqrt(var)
    return float(np.tanh(z - half)), float(np.tanh(z + half))


def testar_dados_reais(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Uma linha por teste: estatistica, t, p-valor, IC95, r^2, tamanho do efeito e decisao."""
    df = params.carregar_reais() if df is None else df
    x, y = df[params.COL_LOC].to_numpy(float), df[params.COL_DEF].to_numpy(float)
    n = len(df)
    linhas = []
    for teste, funcao in (("Pearson", stats.pearsonr), ("Spearman", stats.spearmanr)):
        res = funcao(x, y)
        coef, p = float(res.statistic), float(res.pvalue)
        lo, hi = _ic95(coef, n, teste == "Spearman")
        linhas.append({
            "teste": teste, "n": n, "estatistica": coef,
            "t": coef * np.sqrt((n - 2) / (1 - coef**2)), "gl": n - 2,
            "p_valor": p, "ic95_inf": lo, "ic95_sup": hi, "r2": coef**2,
            "tamanho_efeito": classificar_efeito(coef),
            "decisao": "rejeita H₀" if p < params.ALFA else "não rejeita H₀",
        })
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 200)
    print(testar_dados_reais().to_string(index=False))
