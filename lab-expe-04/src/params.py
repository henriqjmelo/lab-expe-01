"""Parametros estimados dos dados reais (KC1, nivel de classe) e constantes do Lab04.

Uso:
    from params import SEED, N_SIM, N_REP, EFEITOS, LOC_LOG_MU, LOC_LOG_SIGMA, ...
    python src/params.py          # imprime o resumo dos dados reais

As constantes de situacao B vem dos dados reais, calculadas no import.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parent.parent
CSV_REAL = RAIZ / "data" / "kc1_class.csv"

COL_LOC = "sumLOC_TOTAL"
COL_DEF = "NUMDEFECTS"

# Configuracao da simulacao (enunciado + plano)
SEED = 42
N_SIM = 30
N_REP = 10_000
EFEITOS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)
ALFA = 0.05
ALFA_EXTRA = 0.01


def carregar_reais() -> pd.DataFrame:
    """Le as duas colunas usadas (LOC e defeitos) das 145 classes."""
    return pd.read_csv(CSV_REAL)[[COL_LOC, COL_DEF]]


def estimar(df: pd.DataFrame | None = None) -> dict:
    """Calcula resumo descritivo, correlacoes reais e parametros da situacao B."""
    df = carregar_reais() if df is None else df
    loc, dfc = df[COL_LOC], df[COL_DEF]
    pos = dfc[dfc > 0]
    pr, pp = stats.pearsonr(loc, dfc)
    sr, sp = stats.spearmanr(loc, dfc)
    sub = df.sample(30, random_state=SEED)
    return {
        "n": len(df),
        "mediana_loc": float(loc.median()),
        "assimetria_loc": float(stats.skew(loc)),
        "assimetria_def": float(stats.skew(dfc)),
        "classes_sem_defeito": int((dfc == 0).sum()),
        "prop_sem_defeito": float((dfc == 0).mean()),
        "pearson": float(pr), "pearson_p": float(pp),
        "spearman": float(sr), "spearman_p": float(sp),
        "sub30_pearson": float(stats.pearsonr(sub[COL_LOC], sub[COL_DEF])[0]),
        "sub30_spearman": float(stats.spearmanr(sub[COL_LOC], sub[COL_DEF])[0]),
        # Situacao B: log(LOC) ~ Normal(mu, sigma), estimada nas 145 classes
        "loc_log_mu": float(np.log(loc).mean()),
        "loc_log_sigma": float(np.log(loc).std(ddof=1)),
        # Defeitos: 59% sao zero, entao log nao existe para eles. Estimamos so nas
        # classes com defeito (n = 60). Escolha do grupo, ver JUSTIFICATIVA abaixo.
        "def_log_mu": float(np.log(pos).mean()),
        "def_log_sigma": float(np.log(pos).std(ddof=1)),
        "n_com_defeito": int(len(pos)),
    }


_P = estimar()

# Parametros da situacao B (usados por generate.py e G1)
LOC_LOG_MU = _P["loc_log_mu"]        # ~4,676  (mediana e^mu ~ 107; real = 162)
LOC_LOG_SIGMA = _P["loc_log_sigma"]  # ~1,749
DEF_LOG_MU = _P["def_log_mu"]        # ~1,919  (so classes com defeito)
DEF_LOG_SIGMA = _P["def_log_sigma"]  # ~0,979

JUSTIFICATIVA = """\
LOC: o log de LOC das 145 classes e usado direto (nenhuma classe tem LOC = 0, minimo = 1).
Defeitos: 85 de 145 classes (58,6%) tem zero defeito, e log(0) nao existe. Os parametros
(def_log_mu, def_log_sigma) vem so das 60 classes com pelo menos 1 defeito. A lognormal
simulada, portanto, nunca gera zero e nao reproduz os 59% de classes sem defeito; isso e
uma limitacao registrada no dashboard. A correlacao latente r e definida na escala log.
"""


if __name__ == "__main__":
    for k, v in _P.items():
        print(f"{k:22s} {v}")
    print()
    print(JUSTIFICATIVA)
