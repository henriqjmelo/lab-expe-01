from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.multitest import multipletests

from metricas.dora import NOMES, classificar


@dataclass(frozen=True)
class Combinacao:
    nome: str
    unidade: str
    frequencia: str
    lead_time: str
    cfr: str
    descricao: str


COMBINACOES = (
    Combinacao("C1", "release", "df_release_semana", "lt_a_release_dias", "cfr_a", "release · LT (a) · CFR (a)"),
    Combinacao(
        "C2", "release_pre", "df_release_pre_semana", "lt_b_release_pre_dias", "cfr_b_release_pre",
        "release + pré · LT (b) · CFR (b)",
    ),
    Combinacao("C3", "tag", "df_tag_semana", "lt_b_tag_dias", "cfr_a", "tag · LT (b) · CFR (a)"),
)

METRICAS = (
    ("df_release_semana", "Frequência"),
    ("lt_a_release_dias", "Lead time (a)"),
    ("lt_b_release_dias", "Lead time (b)"),
    ("cfr_a", "CFR (a)"),
    ("cfr_b_release", "CFR (b)"),
    ("recuperacao_mediana_horas", "Recuperação"),
)

UNIDADES = {
    "df_release_semana": "releases/semana",
    "lt_a_release_dias": "dias",
    "lt_b_release_dias": "dias",
    "cfr_a": "proporção",
    "cfr_b_release": "proporção",
    "recuperacao_mediana_horas": "horas",
}

LINGUAGENS_MIN = 15


def carregar(caminho) -> pd.DataFrame:
    return pd.read_csv(caminho)


ALTERNATIVAS = (
    ("cfr_a", "CFR (a) · falha de CI", "proporção"),
    ("cfr_a_reexec", "CFR (a+) · com reexecuções", "proporção"),
    ("taxa_reexecucao", "Taxa de reexecução de runs", "proporção"),
    ("cfr_b_release", "CFR (b) · release corretiva", "proporção"),
    ("cfr_c_revert", "CFR (c) · release revertida", "proporção"),
    ("feedback_mediana_min", "Feedback do CI", "minutos"),
    ("prop_convencional", "Commits no padrão convencional", "proporção"),
    ("prop_fix", "fix entre os convencionais", "proporção"),
    ("prop_feat", "feat entre os convencionais", "proporção"),
)


def carregar_com_alternativas(caminho) -> pd.DataFrame:
    df = carregar(caminho)
    extra = Path(caminho).parent / "medidas_alternativas.csv"
    if extra.exists():
        alt = pd.read_csv(extra).drop(columns=["cfr_a"])
        df = df.merge(alt, on=["owner", "repo"], how="left")
    graphql = Path(caminho).parent / "medidas_graphql.csv"
    if graphql.exists():
        df = df.merge(pd.read_csv(graphql), on=["owner", "repo"], how="left")
    return df


def resumo_alternativas(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for coluna, rotulo, unidade in ALTERNATIVAS:
        v = df[coluna].dropna()
        linhas.append({
            "medida": rotulo, "coluna": coluna, "unidade": unidade, "n": len(v),
            "mediana": v.median(), "q1": v.quantile(0.25), "q3": v.quantile(0.75),
            "prop_elite": (v <= 0.15).mean() if coluna.startswith("cfr") else None,
        })
    linhas.append({"medida": "Adotam Conventional Commits", "coluna": "adota_convencional", "unidade": "proporção",
                   "n": len(df), "mediana": (df["adota_convencional"] == True).mean(),  # noqa: E712
                   "q1": None, "q3": None, "prop_elite": None})
    return pd.DataFrame(linhas)


def resumo(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for coluna, rotulo in METRICAS:
        v = df[coluna].dropna()
        linhas.append({
            "metrica": rotulo,
            "coluna": coluna,
            "unidade": UNIDADES[coluna],
            "n": len(v),
            "mediana": v.median(),
            "q1": v.quantile(0.25),
            "q3": v.quantile(0.75),
        })
    return pd.DataFrame(linhas)


def classificacoes(df: pd.DataFrame, combinacao: Combinacao) -> pd.DataFrame:
    pontos = [
        classificar(
            _num(l[combinacao.frequencia]), _num(l[combinacao.lead_time]), _num(l[combinacao.cfr]),
            _num(l["recuperacao_mediana_horas"]),
        )
        for _, l in df.iterrows()
    ]
    out = pd.DataFrame(pontos, index=df.index).astype("Int64")
    out.insert(0, "repo", df["owner"] + "/" + df["repo"])
    return out


def _num(valor) -> float | None:
    return None if pd.isna(valor) else float(valor)


def distribuicao_categorias(df: pd.DataFrame) -> pd.DataFrame:
    c1 = classificacoes(df, COMBINACOES[0])
    c2 = classificacoes(df, COMBINACOES[1])
    colunas = {
        "Frequência": c1["frequencia"],
        "Lead time (a)": c1["lead_time"],
        "CFR (a)": c1["cfr"],
        "CFR (b)": c2["cfr"],
        "Recuperação": c1["recuperacao"],
        "Geral (C1)": c1["geral"],
    }
    linhas = []
    for nome, serie in colunas.items():
        v = serie.dropna()
        linha = {"metrica": nome, "n": len(v)}
        for pontos in (4, 3, 2, 1):
            linha[NOMES[pontos]] = (v == pontos).mean() if len(v) else np.nan
        linhas.append(linha)
    return pd.DataFrame(linhas)


def rq05(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for cfr, rotulo in (("cfr_a", "CFR (a)"), ("cfr_b_release", "CFR (b)")):
        par = df[["df_release_semana", cfr]].dropna()
        rho, p = stats.spearmanr(par["df_release_semana"], par[cfr])
        linhas.append({"x": "Frequência", "y": rotulo, "coluna_y": cfr, "rho": rho, "p": p, "n": len(par)})
    return pd.DataFrame(linhas)


def fatores(df: pd.DataFrame) -> dict[str, pd.Series]:
    contagem = df["linguagem"].value_counts()
    principais = contagem[contagem >= LINGUAGENS_MIN].index
    linguagem = df["linguagem"].where(df["linguagem"].isin(principais))
    quartis = ["Q1", "Q2", "Q3", "Q4"]
    return {
        "Linguagem": linguagem,
        "Estrelas (quartil)": pd.qcut(df["estrelas"], 4, labels=quartis),
        "Contribuidores (quartil)": pd.qcut(df["contribuidores"].rank(method="first"), 4, labels=quartis),
        "Idade (quartil)": pd.qcut(df["idade_anos"], 4, labels=quartis),
    }


def rq06(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for fator, grupos in fatores(df).items():
        for coluna, rotulo in METRICAS:
            dados = pd.DataFrame({"g": grupos, "v": df[coluna]}).dropna()
            amostras = [g["v"].to_numpy() for _, g in dados.groupby("g", observed=True) if len(g) > 0]
            h, p = stats.kruskal(*amostras)
            n = len(dados)
            linhas.append({
                "fator": fator, "metrica": rotulo, "coluna": coluna, "k_grupos": len(amostras),
                "n": n, "H": h, "p": p, "epsilon2": h / (n - 1),
            })
    tabela = pd.DataFrame(linhas)
    tabela["p_holm"] = multipletests(tabela["p"], method="holm")[1]
    tabela["significativo"] = tabela["p_holm"] < 0.05
    return tabela


def rq07(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    gerais = pd.DataFrame({c.nome: classificacoes(df, c)["geral"] for c in COMBINACOES})
    gerais.insert(0, "repo", df["owner"] + "/" + df["repo"])
    completos = gerais.dropna()
    pares = []
    for a, b in (("C1", "C2"), ("C1", "C3"), ("C2", "C3")):
        x, y = completos[a].astype(int), completos[b].astype(int)
        pares.append({
            "par": f"{a}×{b}",
            "n": len(completos),
            "mudou": float((x != y).mean()),
            "kappa_linear": cohen_kappa_score(x, y, weights="linear"),
        })
    return completos, pd.DataFrame(pares)


def mann_whitney_amostras(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for coluna, rotulo in METRICAS:
        x, y = a[coluna].dropna(), b[coluna].dropna()
        u, p = stats.mannwhitneyu(x, y, alternative="two-sided")
        linhas.append({
            "metrica": rotulo, "coluna": coluna, "n1": len(x), "n2": len(y),
            "mediana1": x.median(), "mediana2": y.median(), "U": u, "p": p,
            "cliff_delta": 2 * u / (len(x) * len(y)) - 1,
        })
    tabela = pd.DataFrame(linhas)
    tabela["p_holm"] = multipletests(tabela["p"], method="holm")[1]
    return tabela


def ic_bootstrap_mediana(valores: pd.Series, reps: int = 5000, semente: int = 42) -> tuple[float, float]:
    v = valores.dropna().to_numpy()
    rng = np.random.default_rng(semente)
    medianas = np.median(rng.choice(v, size=(reps, len(v)), replace=True), axis=1)
    return float(np.percentile(medianas, 2.5)), float(np.percentile(medianas, 97.5))
