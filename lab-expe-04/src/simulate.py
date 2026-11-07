"""Motor de simulacao vetorizado: erro tipo I (Q1), poder (Q2) e violacao de pressuposto (Q3).

Cada celula (situacao, r latente) gera N_REP conjuntos de N_SIM pares de uma vez, em matrizes
N_REP x N_SIM, e aplica Pearson e Spearman a todas as linhas sem laco em Python.

- Pearson: r por linha; t = r * sqrt((n - 2) / (1 - r^2)); p bicaudal pela t(n - 2).
- Spearman: o mesmo calculo sobre os postos (scipy.stats.rankdata, axis=1).
- Situacao A: normal bivariada com correlacao r.
- Situacao B: exp() da normal bivariada (lognormal), parametros estimados dos dados reais.
- Semente: numpy.random.default_rng(42) no inicio de cada situacao, efeitos em ordem crescente,
  entao cada CSV sai identico a cada execucao.

Uso:
    python src/simulate.py                    # situacoes A e B -> results/situacao_{A,B}.csv
    python src/simulate.py --situacao A
"""
from __future__ import annotations

import argparse
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

PASTA_RESULTADOS = _RAIZ / "results"
ALFAS = (params.ALFA, params.ALFA_EXTRA)  # 0,05 e 0,01, aplicados aos mesmos p-valores
COLUNAS_CSV = [
    "situacao", "r_latente", "teste", "n", "repeticoes",
    "rejeicoes_005", "taxa_005", "rejeicoes_001", "taxa_001", "estatistica_media",
]


def parametros_situacao_b() -> dict[str, float]:
    """Parametros lognormais da situacao B, estimados dos dados reais (params.py)."""
    return {
        "loc_log_mu": params.LOC_LOG_MU, "loc_log_sigma": params.LOC_LOG_SIGMA,
        "def_log_mu": params.DEF_LOG_MU, "def_log_sigma": params.DEF_LOG_SIGMA,
    }


def gerar_lote(situacao: str, r: float, n_rep: int, n: int, rng: np.random.Generator,
               parametros: dict[str, float] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """n_rep conjuntos de n pares (x = LOC, y = defeitos), como duas matrizes n_rep x n.

    A normal bivariada sai de duas normais independentes: y = r * z1 + sqrt(1 - r^2) * z2.
    O mesmo modelo de generate.py, so que de uma vez para todas as repeticoes.
    """
    if not -1 <= r <= 1:
        raise ValueError("r precisa estar entre -1 e 1.")
    z1 = rng.standard_normal((n_rep, n))
    z2 = rng.standard_normal((n_rep, n))
    z_y = r * z1 + np.sqrt(1.0 - r**2) * z2
    if situacao == "A":
        return z1, z_y
    if situacao == "B":
        p = parametros_situacao_b() if parametros is None else parametros
        x = np.exp(p["loc_log_mu"] + p["loc_log_sigma"] * z1)
        y = np.exp(p["def_log_mu"] + p["def_log_sigma"] * z_y)
        return x, y
    raise ValueError(f"Situacao desconhecida: {situacao}")


def correlacao_por_linha(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Coeficiente de Pearson de cada linha (par de matrizes n_rep x n)."""
    xc = x - x.mean(axis=1, keepdims=True)
    yc = y - y.mean(axis=1, keepdims=True)
    return (xc * yc).sum(axis=1) / np.sqrt((xc**2).sum(axis=1) * (yc**2).sum(axis=1))


def p_valor_de_r(r: np.ndarray, n: int) -> np.ndarray:
    """p-valor bicaudal: t = r * sqrt((n - 2) / (1 - r^2)) contra a t de Student com n - 2 gl."""
    t = r * np.sqrt((n - 2) / (1.0 - r**2))
    return 2.0 * stats.t.sf(np.abs(t), n - 2)


def pearson_vetorizado(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(r, p-valor) de Pearson para cada linha."""
    r = correlacao_por_linha(x, y)
    return r, p_valor_de_r(r, x.shape[1])


def spearman_vetorizado(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(rho, p-valor) de Spearman para cada linha: Pearson sobre os postos."""
    rx = stats.rankdata(x, axis=1)
    ry = stats.rankdata(y, axis=1)
    rho = correlacao_por_linha(rx, ry)
    return rho, p_valor_de_r(rho, x.shape[1])


def simular_celula(situacao: str, r: float, rng: np.random.Generator,
                   n_rep: int = params.N_REP, n: int = params.N_SIM) -> pd.DataFrame:
    """Uma celula (situacao, r): 2 linhas (Pearson e Spearman) com as taxas de rejeicao."""
    x, y = gerar_lote(situacao, r, n_rep, n, rng)
    linhas = []
    for teste, funcao in (("Pearson", pearson_vetorizado), ("Spearman", spearman_vetorizado)):
        estat, p = funcao(x, y)
        rej_005 = int((p < ALFAS[0]).sum())
        rej_001 = int((p < ALFAS[1]).sum())
        linhas.append({
            "situacao": situacao, "r_latente": r, "teste": teste, "n": n, "repeticoes": n_rep,
            "rejeicoes_005": rej_005, "taxa_005": rej_005 / n_rep,
            "rejeicoes_001": rej_001, "taxa_001": rej_001 / n_rep,
            "estatistica_media": float(estat.mean()),
        })
    return pd.DataFrame(linhas, columns=COLUNAS_CSV)


def simular_situacao(situacao: str, efeitos=params.EFEITOS, n_rep: int = params.N_REP,
                     n: int = params.N_SIM, seed: int = params.SEED) -> pd.DataFrame:
    """Todos os efeitos de uma situacao, com a semente reiniciada no comeco."""
    rng = np.random.default_rng(seed)
    return pd.concat([simular_celula(situacao, r, rng, n_rep, n) for r in efeitos], ignore_index=True)


def gravar(situacao: str, **kwargs) -> Path:
    """Simula a situacao e grava results/situacao_<A|B>.csv."""
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    caminho = PASTA_RESULTADOS / f"situacao_{situacao}.csv"
    simular_situacao(situacao, **kwargs).to_csv(caminho, index=False)
    return caminho


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--situacao", choices=["A", "B", "todas"], default="todas")
    args = ap.parse_args()
    for sit in ("A", "B") if args.situacao == "todas" else (args.situacao,):
        print("gravado:", gravar(sit))
