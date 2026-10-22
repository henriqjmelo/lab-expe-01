from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from analise import graficos as g

DATA_FIM = pd.Timestamp("2026-09-30")
METADADOS_NUMERICOS = (("estrelas", "Estrelas"), ("idade_anos", "Idade (anos)"))
ETAPAS = ("com_actions", "min_5_releases", "min_50_runs")


def situacao_candidatos(
    candidatos: pd.DataFrame, aceitos: pd.DataFrame, descartes: pd.DataFrame
) -> pd.DataFrame:
    resultado = candidatos.copy()
    if "full_name" not in resultado:
        resultado["full_name"] = resultado["owner"].astype(str) + "/" + resultado["repo"].astype(str)
    aceitos_nomes = set(_full_names(aceitos))
    descartes_por_nome = descartes.drop_duplicates("full_name").set_index("full_name")["etapa"].to_dict()
    resultado["situacao"] = resultado["full_name"].map(
        lambda nome: "aceito" if nome in aceitos_nomes else
        f"descartado_{descartes_por_nome[nome]}" if nome in descartes_por_nome else "nao_avaliado"
    )
    return resultado


def _full_names(df: pd.DataFrame) -> pd.Series:
    if "full_name" in df:
        return df["full_name"].astype(str)
    return df["owner"].astype(str) + "/" + df["repo"].astype(str)


def _idade(candidatos: pd.DataFrame) -> pd.Series:
    criacao = pd.to_datetime(candidatos["criado_em"].astype(str).str[:10], errors="coerce")
    dias = (DATA_FIM - criacao).dt.days
    return (dias / 365.25).round(2)


def _com_idade(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df.copy()
    if "idade_anos" not in resultado and "criado_em" in resultado:
        resultado["idade_anos"] = _idade(resultado)
    elif "idade_anos" in resultado and "criado_em" in resultado:
        idade_calculada = _idade(resultado)
        resultado["idade_anos"] = idade_calculada.fillna(resultado["idade_anos"])
    resultado["linguagem"] = resultado["linguagem"].fillna("Sem linguagem")
    resultado.loc[resultado["linguagem"].astype(str).str.strip().eq(""), "linguagem"] = "Sem linguagem"
    return resultado


def _top_linguagens(df: pd.DataFrame, n: int = 8) -> list[str]:
    return _com_idade(df)["linguagem"].value_counts().head(n).index.tolist()


def _categorias_linguagem(df: pd.DataFrame, principais: list[str]) -> pd.Series:
    linguagens = _com_idade(df)["linguagem"]
    return linguagens.where(linguagens.isin(principais), "Outras")


def tabela_caracterizacao(amostras: list[tuple[str, pd.DataFrame]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    linhas_numericas = []
    linhas_linguagens = []
    for nome, original in amostras:
        df = _com_idade(original)
        for coluna, rotulo in (*METADADOS_NUMERICOS, ("contribuidores", "Contribuidores")):
            if coluna not in df:
                continue
            valores = pd.to_numeric(df[coluna], errors="coerce").dropna()
            linhas_numericas.append({
                "amostra": nome, "metadado": rotulo, "n": len(valores), "mediana": valores.median(),
                "q1": valores.quantile(0.25), "q3": valores.quantile(0.75),
            })
        principais = _top_linguagens(df)
        distribuicao = _categorias_linguagem(df, principais).value_counts()
        for linguagem, quantidade in distribuicao.items():
            linhas_linguagens.append({
                "amostra": nome, "linguagem": linguagem, "n": int(quantidade),
                "proporcao": quantidade / len(df) if len(df) else np.nan,
            })
    return pd.DataFrame(linhas_numericas), pd.DataFrame(linhas_linguagens)


def _comparar_numerico(
    grupo_a: pd.DataFrame, grupo_b: pd.DataFrame, nome_a: str, nome_b: str,
    principais: list[str] | None = None,
) -> list[dict]:
    linhas = []
    a, b = _com_idade(grupo_a), _com_idade(grupo_b)
    for coluna, rotulo in METADADOS_NUMERICOS:
        if coluna not in a or coluna not in b:
            continue
        x = pd.to_numeric(a[coluna], errors="coerce").dropna()
        y = pd.to_numeric(b[coluna], errors="coerce").dropna()
        if x.empty or y.empty:
            u, p = np.nan, np.nan
            delta = np.nan
        else:
            u, p = stats.mannwhitneyu(x, y, alternative="two-sided")
            delta = 2 * u / (len(x) * len(y)) - 1
        linhas.append({
            "comparacao": f"{nome_a} × {nome_b}", "variavel": rotulo, "teste": "mann_whitney",
            "n_a": len(x), "n_b": len(y), "mediana_a": x.median(), "mediana_b": y.median(),
            "estatistica": u, "p": p, "delta_cliff": delta,
            "magnitude_delta": magnitude_delta(delta),
        })
    principais = principais or _top_linguagens(pd.concat([a, b], ignore_index=True))
    categorias_a = _categorias_linguagem(a, principais)
    categorias_b = _categorias_linguagem(b, principais)
    tabela = pd.crosstab(
        pd.concat([pd.Series([nome_a] * len(a)), pd.Series([nome_b] * len(b))], ignore_index=True),
        pd.concat([categorias_a.reset_index(drop=True), categorias_b.reset_index(drop=True)], ignore_index=True),
    ).reindex(index=[nome_a, nome_b], fill_value=0)
    if tabela.shape[1] < 2 or (tabela.sum(axis=0) == 0).all() or (tabela.sum(axis=1) == 0).any():
        chi2, p, gl = np.nan, np.nan, 0
    else:
        chi2, p, gl, _ = stats.chi2_contingency(tabela)
    linhas.append({
        "comparacao": f"{nome_a} × {nome_b}", "variavel": "Linguagem (8 principais + Outras)",
        "teste": "qui_quadrado", "n_a": len(a), "n_b": len(b), "mediana_a": np.nan,
        "mediana_b": np.nan, "estatistica": chi2, "p": p, "delta_cliff": np.nan,
        "magnitude_delta": "", "gl": gl,
    })
    return linhas


def magnitude_delta(delta: float) -> str:
    if pd.isna(delta):
        return "indefinido"
    valor = abs(delta)
    if valor < 0.147:
        return "desprezivel"
    if valor < 0.33:
        return "pequeno"
    if valor < 0.474:
        return "medio"
    return "grande"


def comparar_selecao(candidatos: pd.DataFrame, aceitos: pd.DataFrame, descartes: pd.DataFrame) -> pd.DataFrame:
    situacoes = situacao_candidatos(candidatos, aceitos, descartes)
    avaliados = situacoes[situacoes["situacao"] != "nao_avaliado"]
    nao_avaliados = situacoes[situacoes["situacao"] == "nao_avaliado"]
    aceitos_nomes = set(_full_names(aceitos))
    aceitos_candidatos = situacoes[situacoes["full_name"].isin(aceitos_nomes)]
    principais = _top_linguagens(aceitos_candidatos)
    linhas = []
    for etapa in ETAPAS:
        descartados_etapa = situacoes[situacoes["situacao"] == f"descartado_{etapa}"]
        linhas.extend(_comparar_numerico(
            aceitos_candidatos, descartados_etapa, "aceitos", f"descartados_{etapa}", principais
        ))
    descartados_todos = situacoes[situacoes["situacao"].str.startswith("descartado_")]
    linhas.extend(_comparar_numerico(
        aceitos_candidatos, descartados_todos, "aceitos", "descartados_todos", principais
    ))
    linhas.extend(_comparar_numerico(avaliados, nao_avaliados, "avaliados", "nao_avaliados", principais))
    return _ajustar_holm(pd.DataFrame(linhas))


def comparar_amostras(a1: pd.DataFrame, a2: pd.DataFrame) -> pd.DataFrame:
    principais = _top_linguagens(pd.concat([a1, a2], ignore_index=True))
    return _ajustar_holm(pd.DataFrame(_comparar_numerico(a1, a2, "A1", "A2", principais)))


def _ajustar_holm(tabela: pd.DataFrame) -> pd.DataFrame:
    resultado = tabela.copy()
    resultado["p_holm"] = np.nan
    validos = resultado["p"].notna()
    if validos.any():
        resultado.loc[validos, "p_holm"] = multipletests(resultado.loc[validos, "p"], method="holm")[1]
    resultado["significativo_holm"] = resultado["p_holm"] < 0.05
    return resultado


def fig_distribuicoes(situacoes: pd.DataFrame, destino: Path) -> Path:
    g.estilo()
    grupos = [("aceito", "Amostra aceita", g.SERIE[0])]
    cores = (g.SERIE[1], g.SERIE[2], "#777777")
    rotulos = ("Sem Actions", "< 5 releases", "< 50 runs")
    for etapa, rotulo, cor in zip(ETAPAS, rotulos, cores):
        grupos.append((f"descartado_{etapa}", rotulo, cor))
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7))
    for ax, coluna, titulo, unidade in (
        (axes[0], "estrelas", "Candidatos aceitos concentram mais estrelas", "estrelas"),
        (axes[1], "idade_anos", "Idade dos projetos varia por etapa do funil", "anos"),
    ):
        for chave, rotulo, cor in grupos:
            grupo = situacoes[situacoes["situacao"] == chave]
            if coluna not in grupo:
                grupo = _com_idade(grupo)
            valores = pd.to_numeric(grupo[coluna], errors="coerce").dropna().sort_values().to_numpy()
            if len(valores):
                ax.step(valores, np.arange(1, len(valores) + 1) / len(valores), where="post", color=cor,
                        linewidth=1.8, label=f"{rotulo} (n={len(valores)})")
        ax.set_xscale("log")
        ax.set_xlabel(unidade + " (escala log)")
        ax.set_ylabel("Proporção acumulada")
        ax.grid(axis="y", alpha=0.4)
        ax.legend(fontsize=7, loc="lower right")
        ax.set_title(titulo, loc="left", fontsize=10, fontweight="bold", pad=12)
    fig.tight_layout()
    return g.salvar(fig, destino)


def fig_linguagens(situacoes: pd.DataFrame, destino: Path) -> Path:
    g.estilo()
    aceitos = situacoes[situacoes["situacao"] == "aceito"]
    principais = _top_linguagens(aceitos)
    grupos = [("aceito", "Aceitos"), ("descartado_com_actions", "Sem Actions"),
              ("descartado_min_5_releases", "< 5 releases"), ("descartado_min_50_runs", "< 50 runs")]
    linhas = []
    for chave, rotulo in grupos:
        dados = situacoes[situacoes["situacao"] == chave]
        contagens = _categorias_linguagem(dados, principais).value_counts(normalize=True)
        linhas.append({"grupo": rotulo, **contagens.to_dict()})
    tabela = pd.DataFrame(linhas).set_index("grupo").fillna(0)
    colunas = principais + ["Outras"]
    tabela = tabela.reindex(columns=colunas, fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    tabela.plot(kind="bar", stacked=True, ax=ax, colormap="tab20", width=0.72)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Proporção de repositórios")
    ax.set_xlabel("")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda valor, _: g.fmt_pct(valor)))
    ax.legend(title="Linguagem (top 8 da amostra)", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7)
    ax.set_title("A distribuição de linguagens difere entre aceitos e descartados", loc="left", fontsize=10,
                 fontweight="bold", pad=12)
    fig.tight_layout()
    return g.salvar(fig, destino)


def executar(
    candidatos_path: Path = Path("data/candidatos.csv"),
    amostra1_path: Path = Path("data/dataset_dora.csv"),
    descartes1_path: Path = Path("data/descartes.csv"),
    amostra2_path: Path = Path("data/amostra2/dataset_dora.csv"),
    saida_path: Path = Path("analise/saida/caracterizacao"),
) -> list[Path]:
    saida_path.mkdir(parents=True, exist_ok=True)
    candidatos = pd.read_csv(candidatos_path)
    a1, descartes1 = pd.read_csv(amostra1_path), pd.read_csv(descartes1_path)
    a2 = pd.read_csv(amostra2_path) if amostra2_path.exists() else pd.DataFrame()
    amostras = [("A1", a1)]
    if not a2.empty:
        amostras.append(("A1+A2", pd.concat([a1, a2], ignore_index=True)))
    tabela_numerica, tabela_linguagens = tabela_caracterizacao(amostras)
    situacoes = situacao_candidatos(candidatos, a1, descartes1)
    selecao = comparar_selecao(candidatos, a1, descartes1)
    tabela_numerica.to_csv(saida_path / "caracterizacao_numerica.csv", index=False)
    tabela_linguagens.to_csv(saida_path / "caracterizacao_linguagens.csv", index=False)
    selecao.to_csv(saida_path / "vies_selecao.csv", index=False)
    situacoes.to_csv(saida_path / "situacao_candidatos.csv", index=False)
    gerados = [
        saida_path / "caracterizacao_numerica.csv", saida_path / "caracterizacao_linguagens.csv",
        saida_path / "vies_selecao.csv", saida_path / "situacao_candidatos.csv",
        fig_distribuicoes(situacoes, saida_path / "figuras" / "distribuicoes_estrelas_idade.png"),
        fig_linguagens(situacoes, saida_path / "figuras" / "distribuicao_linguagens.png"),
    ]
    if not a2.empty:
        comparacao = comparar_amostras(a1, a2)
        comparacao.to_csv(saida_path / "a1_x_a2_metadados.csv", index=False)
        gerados.append(saida_path / "a1_x_a2_metadados.csv")
    return gerados


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m analise.caracterizacao")
    parser.add_argument("--candidatos", type=Path, default=Path("data/candidatos.csv"))
    parser.add_argument("--amostra1", type=Path, default=Path("data/dataset_dora.csv"))
    parser.add_argument("--descartes1", type=Path, default=Path("data/descartes.csv"))
    parser.add_argument("--amostra2", type=Path, default=Path("data/amostra2/dataset_dora.csv"))
    parser.add_argument("--saida", type=Path, default=Path("analise/saida/caracterizacao"))
    args = parser.parse_args(argv)
    for caminho in executar(args.candidatos, args.amostra1, args.descartes1, args.amostra2, args.saida):
        print(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())