"""RQ2: a diferenca entre os coletores muda com o tamanho do heap?

Modelo linear sobre log(exec_ms). Em log, o coeficiente de interacao
gc x heap e um CONTRASTE DE RAZOES: quanto a razao ZGC/G1 no heap maior
difere da razao no heap menor. exp(coeficiente) devolve esse numero na escala
que um operador le.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

FORMULA = "log_exec ~ C(gc) * C(heap_mult) + C(gc) * C(benchmark) + rep"


def ajustar(df: pd.DataFrame):
    dados = df[df["exec_ms"].notna()].copy()
    dados["log_exec"] = np.log(dados["exec_ms"])
    dados["rep"] = dados["rep"].astype(float)   # deriva linear ao longo da coleta
    return smf.ols(FORMULA, data=dados).fit()


def tabela(df: pd.DataFrame) -> tuple[pd.DataFrame, object]:
    """Devolve (tabela de coeficientes, modelo ajustado)."""
    modelo = ajustar(df)
    ic = modelo.conf_int(alpha=0.05)
    linhas = []
    for termo in modelo.params.index:
        coef = float(modelo.params[termo])
        baixo, alto = float(ic.loc[termo, 0]), float(ic.loc[termo, 1])
        linhas.append({
            "termo": termo,
            "coeficiente_log": coef,
            "razao": float(np.exp(coef)),          # leitura na escala original
            "razao_ic_baixo": float(np.exp(baixo)),
            "razao_ic_alto": float(np.exp(alto)),
            "p": float(modelo.pvalues[termo]),
            "interacao_gc_heap": termo.startswith("C(gc)") and "C(heap_mult)" in termo,
        })
    tab = pd.DataFrame(linhas)
    tab.attrs["r2"] = float(modelo.rsquared)
    tab.attrs["r2_ajustado"] = float(modelo.rsquared_adj)
    tab.attrs["n"] = int(modelo.nobs)
    return tab, modelo


def resumo_rq2(tab: pd.DataFrame) -> dict:
    """O veredito do RQ2: ha interacao GC x heap?"""
    inter = tab[tab["interacao_gc_heap"]]
    if inter.empty:
        return {"ha_interacao": False, "motivo": "modelo sem termo de interacao gc x heap"}
    menor_p = inter.loc[inter["p"].idxmin()]
    return {
        "ha_interacao": bool(menor_p["p"] < 0.05),
        "termo": str(menor_p["termo"]),
        "razao_de_razoes": float(menor_p["razao"]),
        "p": float(menor_p["p"]),
        "r2": tab.attrs.get("r2"),
    }
