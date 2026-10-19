from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor

from analise import graficos as g
from analise.estatisticas import LINGUAGENS_MIN, METRICAS, carregar_com_alternativas

FATORES_CONTINUOS = ("estrelas", "contribuidores", "idade_anos")
PREDITORES_CONTINUOS = ("log_estrelas", "log_contribuidores", "idade_anos")
METRICAS_CFR = ("cfr_a", "cfr_b_release")


def correlacao_entre_fatores(df: pd.DataFrame) -> pd.DataFrame:
    dados = df[list(FATORES_CONTINUOS)].dropna()
    linhas = []
    for i, a in enumerate(FATORES_CONTINUOS):
        for b in FATORES_CONTINUOS[i + 1 :]:
            rho, p = stats.spearmanr(dados[a], dados[b])
            linhas.append({"fator_x": a, "fator_y": b, "rho": rho, "p": p, "n": len(dados)})
    return pd.DataFrame(linhas)


def _residuo_de_postos(alvo: np.ndarray, controles: list[np.ndarray]) -> np.ndarray:
    postos_alvo = stats.rankdata(alvo)
    postos_controles = np.column_stack([stats.rankdata(c) for c in controles])
    X = sm.add_constant(postos_controles)
    return sm.OLS(postos_alvo, X).fit().resid


def correlacao_parcial(df: pd.DataFrame, fator: str, metrica: str, controles: list[str]) -> dict:
    colunas = [fator, metrica, *controles]
    dados = df[colunas].dropna()
    n, k = len(dados), len(controles)
    gl = n - 2 - k
    if gl <= 0:
        return {"n": n, "gl": gl, "rho_parcial": np.nan, "t": np.nan, "p": np.nan}
    resid_f = _residuo_de_postos(dados[fator].to_numpy(), [dados[c].to_numpy() for c in controles])
    resid_m = _residuo_de_postos(dados[metrica].to_numpy(), [dados[c].to_numpy() for c in controles])
    rho, _ = stats.pearsonr(resid_f, resid_m)
    denom = 1 - rho**2
    t = rho * np.sqrt(gl / denom) if denom > 0 else np.sign(rho) * np.inf
    p = 2 * stats.t.sf(abs(t), gl)
    return {"n": n, "gl": gl, "rho_parcial": rho, "t": t, "p": p}


def tabela_correlacao_parcial(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for fator in FATORES_CONTINUOS:
        controles = [c for c in FATORES_CONTINUOS if c != fator]
        for coluna, rotulo in METRICAS:
            r = correlacao_parcial(df, fator, coluna, controles)
            linhas.append({"fator": fator, "metrica": rotulo, "coluna": coluna, **r})
    tabela = pd.DataFrame(linhas)
    tabela["p_holm"] = multipletests(tabela["p"].fillna(1.0), method="holm")[1]
    tabela["significativo"] = tabela["p_holm"] < 0.05
    return tabela


def ajustar_regressao(exog: pd.DataFrame, y: np.ndarray, cov_type: str = "HC3"):
    return sm.OLS(y, sm.add_constant(exog)).fit(cov_type=cov_type)


def coeficientes(modelo) -> pd.DataFrame:
    ic = modelo.conf_int()
    return pd.DataFrame(
        [
            {"preditor": nome, "coef": modelo.params[nome], "ic_lo": ic.loc[nome, 0],
             "ic_hi": ic.loc[nome, 1], "p": modelo.pvalues[nome]}
            for nome in modelo.params.index
            if nome != "const"
        ]
    )


def padronizar(exog: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    out = exog.copy()
    for c in colunas:
        out[c] = (out[c] - out[c].mean()) / out[c].std()
    return out


def vif_preditores(exog: pd.DataFrame) -> pd.DataFrame:
    matriz = sm.add_constant(exog).to_numpy(dtype=float)
    return pd.DataFrame(
        {"preditor": list(exog.columns), "vif": [variance_inflation_factor(matriz, i) for i in range(1, matriz.shape[1])]}
    )


def preparar_preditores(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["log_estrelas"] = np.log10(df["estrelas"])
    out["log_contribuidores"] = np.log10(df["contribuidores"])
    out["idade_anos"] = df["idade_anos"].astype(float)
    contagem = df["linguagem"].value_counts()
    principais = contagem[contagem >= LINGUAGENS_MIN].index
    out["linguagem"] = df["linguagem"].where(df["linguagem"].isin(principais), "Outras")
    return out


def _exog_completo(preditores: pd.DataFrame, padronizar_continuos: bool) -> pd.DataFrame:
    continuos = preditores[list(PREDITORES_CONTINUOS)]
    if padronizar_continuos:
        continuos = padronizar(continuos, list(PREDITORES_CONTINUOS))
    dummies = pd.get_dummies(preditores["linguagem"], prefix="lang", drop_first=True, dtype=float)
    return pd.concat([continuos, dummies], axis=1)


def _dados_do_modelo(df: pd.DataFrame, metrica: str) -> tuple[pd.DataFrame, pd.Series]:
    preditores = preparar_preditores(df)
    dados = pd.concat([preditores, df[metrica]], axis=1).dropna()
    return dados[preditores.columns], dados[metrica]


def regressao_log(df: pd.DataFrame, metrica: str, padronizar_continuos: bool = False):
    preditores, y = _dados_do_modelo(df, metrica)
    exog = _exog_completo(preditores, padronizar_continuos)
    return ajustar_regressao(exog, np.log1p(y.to_numpy(dtype=float))), exog


def regressao_fracionaria(df: pd.DataFrame, metrica: str, padronizar_continuos: bool = False):
    preditores, y = _dados_do_modelo(df, metrica)
    exog = _exog_completo(preditores, padronizar_continuos)
    y_limitado = y.to_numpy(dtype=float).clip(1e-6, 1 - 1e-6)
    modelo = sm.GLM(y_limitado, sm.add_constant(exog), family=sm.families.Binomial()).fit()
    return modelo, exog


def ajustar_metrica(df: pd.DataFrame, coluna: str, padronizar_continuos: bool = False):
    if coluna in METRICAS_CFR:
        return regressao_fracionaria(df, coluna, padronizar_continuos)
    return regressao_log(df, coluna, padronizar_continuos)


def tabela_robustez(df: pd.DataFrame, rotulo_amostra: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coefs_padronizados, vifs = [], []
    for coluna, rotulo in METRICAS:
        modelo, exog = ajustar_metrica(df, coluna, padronizar_continuos=True)
        c = coeficientes(modelo)
        c.insert(0, "metrica", rotulo)
        c.insert(0, "amostra", rotulo_amostra)
        coefs_padronizados.append(c)
        v = vif_preditores(exog[list(PREDITORES_CONTINUOS)])
        v.insert(0, "metrica", rotulo)
        v.insert(0, "amostra", rotulo_amostra)
        vifs.append(v)
    parcial = tabela_correlacao_parcial(df)
    parcial.insert(0, "amostra", rotulo_amostra)
    return pd.concat(coefs_padronizados, ignore_index=True), pd.concat(vifs, ignore_index=True), parcial


ROTULOS_PREDITORES = {"log_estrelas": "Estrelas (log)", "log_contribuidores": "Contribuidores (log)", "idade_anos": "Idade"}


def fig_forest(coefs: pd.DataFrame, destino: Path) -> Path:
    preditores = [p for p in PREDITORES_CONTINUOS if p in coefs["preditor"].unique()]
    metricas = list(dict.fromkeys(coefs["metrica"]))
    amostras = list(dict.fromkeys(coefs["amostra"]))
    cores = dict(zip(amostras, g.SERIE))

    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    fig, eixos = plt.subplots(1, len(metricas), figsize=(g.LARGURA, 2.9))
    eixos = np.atleast_1d(eixos)
    for indice, (eixo, metrica) in enumerate(zip(eixos, metricas)):
        sub = coefs[(coefs["metrica"] == metrica) & (coefs["preditor"].isin(preditores))]
        for deslocamento, amostra in enumerate(amostras):
            linha = sub[sub["amostra"] == amostra].set_index("preditor").reindex(preditores)
            y = np.arange(len(preditores)) - 0.16 + 0.32 * deslocamento
            eixo.errorbar(
                linha["coef"], y,
                xerr=[linha["coef"] - linha["ic_lo"], linha["ic_hi"] - linha["coef"]],
                fmt="o", color=cores[amostra], markersize=4, capsize=2, linewidth=1.2, label=amostra,
            )
        eixo.axvline(0, color=g.EIXO, linewidth=0.8, zorder=0)
        eixo.set_yticks(range(len(preditores)))
        eixo.set_yticklabels([ROTULOS_PREDITORES[p] for p in preditores] if indice == 0 else [])
        eixo.tick_params(axis="y", labelleft=(indice == 0))
        eixo.set_ylim(-0.7, len(preditores) - 0.3)
        eixo.xaxis.set_major_locator(MaxNLocator(nbins=3))
        eixo.xaxis.set_major_formatter(FuncFormatter(lambda v, _: g.fmt_num(v, 2)))
        eixo.set_title(metrica, fontsize=8.5, pad=4)
    eixos[-1].legend(loc="lower right", fontsize=7, bbox_to_anchor=(1.05, -0.05))
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    g.cabecalho(eixos[0], "Os fatores continuam associados controlando os outros dois?",
                "Coeficiente padronizado (z-score) com IC de 95%, por métrica e por amostra", folga=20)
    return g.salvar(fig, destino)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise.rq06_robustez")
    ap.add_argument("--dados", type=Path, default=Path("data/dataset_dora.csv"))
    ap.add_argument("--extra", type=Path, nargs="*", default=[Path("data/amostra2/dataset_dora.csv")])
    ap.add_argument("--saida", type=Path, default=Path("analise/saida"))
    args = ap.parse_args(argv)

    g.estilo()
    tabelas = args.saida / "tabelas"
    figuras = args.saida / "figuras"
    tabelas.mkdir(parents=True, exist_ok=True)
    figuras.mkdir(parents=True, exist_ok=True)

    a1 = carregar_com_alternativas(args.dados)
    amostras = [(f"A1 · n = {len(a1)}", a1)]
    extras = [carregar_com_alternativas(p) for p in args.extra if p.exists()]
    if extras:
        todas = pd.concat([a1, *extras], ignore_index=True)
        amostras.append((f"A1 + A2 · n = {len(todas)}", todas))

    correlacoes, coefs, vifs, parciais = [], [], [], []
    for rotulo, df in amostras:
        c = correlacao_entre_fatores(df)
        c.insert(0, "amostra", rotulo)
        correlacoes.append(c)
        coef, vif, parcial = tabela_robustez(df, rotulo)
        coefs.append(coef)
        vifs.append(vif)
        parciais.append(parcial)

    pd.concat(correlacoes, ignore_index=True).to_csv(tabelas / "rq06_correlacao_fatores.csv", index=False)
    pd.concat(parciais, ignore_index=True).to_csv(tabelas / "rq06_correlacao_parcial.csv", index=False)
    coefs_final = pd.concat(coefs, ignore_index=True)
    coefs_final.to_csv(tabelas / "rq06_coeficientes_padronizados.csv", index=False)
    pd.concat(vifs, ignore_index=True).to_csv(tabelas / "rq06_vif.csv", index=False)
    figura = fig_forest(coefs_final, figuras / "fig16_rq06_robustez.png")

    for caminho in (tabelas / "rq06_correlacao_fatores.csv", tabelas / "rq06_correlacao_parcial.csv",
                    tabelas / "rq06_coeficientes_padronizados.csv", tabelas / "rq06_vif.csv", figura):
        print(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
