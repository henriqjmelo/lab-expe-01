from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from analise.distribuicoes import duracoes_por_repositorio, medias_amostrais, tabela_weibull
from analise.graficos import (
    EIXO,
    GRADE,
    LARGURA,
    SERIE,
    SUPERFICIE,
    TINTA,
    TINTA_2,
    cabecalho,
    estilo,
    fmt_num,
    salvar,
)

TAMANHOS_TLC = (30, 100, 300)


def _milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _moldura(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(EIXO)
    ax.spines["bottom"].set_color(EIXO)
    ax.grid(axis="y", color=GRADE, linewidth=0.6)
    ax.set_axisbelow(True)


def fig_tlc(df: pd.DataFrame, destino: Path, coluna: str = "df_release_semana",
            repeticoes: int = 10000, tamanhos: tuple[int, ...] = TAMANHOS_TLC) -> Path:
    populacao = df[coluna].dropna().to_numpy()

    fig, eixos = plt.subplots(1, 1 + len(tamanhos), figsize=(LARGURA, 2.45))
    primeiro = eixos[0]

    corte = float(np.quantile(populacao, 0.98))
    primeiro.hist(populacao[populacao <= corte], bins=26, color=SERIE[1],
                  edgecolor=SUPERFICIE, linewidth=0.5)
    primeiro.set_xlabel("releases/semana", fontsize=8)
    primeiro.set_ylabel("Repositórios", fontsize=8.5)
    primeiro.set_title(f"População\nassimetria {fmt_num(float(stats.skew(populacao)), 2)}",
                       fontsize=8.5, color=TINTA_2, loc="left", pad=5)

    for ax, tamanho in zip(eixos[1:], tamanhos):
        medias = medias_amostrais(populacao, tamanho=tamanho, repeticoes=repeticoes)
        ax.hist(medias, bins=32, density=True, color=SERIE[0], edgecolor=SUPERFICIE, linewidth=0.5)
        mu, sigma = float(medias.mean()), float(medias.std(ddof=1))
        grade = np.linspace(medias.min(), medias.max(), 300)
        ax.plot(grade, stats.norm.pdf(grade, mu, sigma), color=TINTA, linewidth=1.3, zorder=4)
        ax.set_xlabel("média amostral", fontsize=8)
        ax.set_title(f"n = {tamanho}\nassimetria {fmt_num(float(stats.skew(medias)), 2)}",
                     fontsize=8.5, color=TINTA_2, loc="left", pad=5)
        ax.set_yticks([])

    for ax in eixos:
        _moldura(ax)
        ax.tick_params(labelsize=7.5)

    cabecalho(primeiro, "A normal não está nos dados: ela aparece na média, e só com amostra grande",
              f"Os quatro painéis saem da mesma população (A1, n = {len(populacao)}); "
              f"cada painel de média resume {_milhar(repeticoes)} reamostragens", folga=30)
    return salvar(fig, destino)


def fig_weibull(por_repo: pd.DataFrame, destino: Path) -> Path:
    forma = por_repo["forma"].dropna().to_numpy()
    mediana = float(np.median(forma))
    abaixo = float((forma < 1).mean())

    fig, ax = plt.subplots(figsize=(LARGURA, 2.9))
    corte = float(np.quantile(forma, 0.99))
    ax.hist(forma[forma <= corte], bins=38, color=SERIE[2], edgecolor=SUPERFICIE, linewidth=0.6)
    topo = ax.get_ylim()[1]
    ax.set_ylim(0, topo * 1.18)

    ax.axvline(1.0, color=TINTA, linewidth=1.2, linestyle=(0, (4, 2)), zorder=4)
    ax.axvline(mediana, color=TINTA, linewidth=1.1, zorder=4)
    ax.annotate(f"mediana {fmt_num(mediana, 2)}", xy=(mediana, topo * 1.15),
                xytext=(-4, 0), textcoords="offset points",
                fontsize=8, color=TINTA, ha="right", va="top")
    ax.annotate("β = 1 · taxa constante", xy=(1.0, topo * 1.15), xytext=(4, 0),
                textcoords="offset points", fontsize=8, color=TINTA_2, ha="left", va="top")

    ax.set_xlabel("Parâmetro de forma β da Weibull ajustada aos episódios de falha")
    ax.set_ylabel("Repositórios")
    _moldura(ax)
    cabecalho(ax, "Quanto mais longa a falha, menor a chance de ela ser resolvida agora",
              f"Cada barra conta os repositórios num intervalo de β (n = {len(forma)} com episódios "
              f"suficientes); β < 1 em {fmt_num(abaixo * 100, 1)}%, o que indica taxa de recuperação decrescente")
    return salvar(fig, destino)


COR_TIPO = {"independente": SERIE[0], "operacionalizacao": SERIE[1], "controle": SERIE[2]}
ROTULO_TIPO = {
    "independente": "Atributo independente",
    "operacionalizacao": "Outra operacionalização da mesma métrica",
    "controle": "Métrica que define a faixa (tautológico)",
}


def fig_discriminancia(tabela: pd.DataFrame, destino: Path) -> Path:
    t = tabela.dropna(subset=["epsilon2"]).sort_values("epsilon2").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(LARGURA, 3.2))

    for i, linha in t.iterrows():
        tipo = linha["tipo"]
        ax.barh(i, linha["epsilon2"], height=0.62, color=COR_TIPO[tipo],
                edgecolor=SUPERFICIE, linewidth=0.8,
                hatch="///" if tipo == "controle" else None, zorder=3)
        marca = "" if linha["tipo"] == "controle" or linha["separa"] else "  n.s."
        ax.annotate(f"{fmt_num(linha['epsilon2'], 3)}{marca}", xy=(linha["epsilon2"], i),
                    xytext=(5, 0), textcoords="offset points", va="center",
                    fontsize=8, color=TINTA_2)

    ax.set_yticks(range(len(t)))
    ax.set_yticklabels(t["atributo"], fontsize=8.5)
    ax.set_xlim(0, float(t["epsilon2"].max()) * 1.28)
    ax.set_xlabel("Tamanho de efeito ε² do Kruskal-Wallis entre as faixas DORA")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(EIXO)
    ax.spines["bottom"].set_color(EIXO)
    ax.grid(axis="x", color=GRADE, linewidth=0.6)
    ax.set_axisbelow(True)

    vistos, alcas = [], []
    for tipo in ("independente", "operacionalizacao", "controle"):
        if tipo in set(t["tipo"]) and tipo not in vistos:
            vistos.append(tipo)
            alcas.append(plt.Rectangle((0, 0), 1, 1, color=COR_TIPO[tipo],
                                       hatch="///" if tipo == "controle" else None))
    ax.legend(alcas, [ROTULO_TIPO[v] for v in vistos], fontsize=7.5, loc="lower right",
              frameon=False, handlelength=1.1, handleheight=1.0)

    cabecalho(ax, "As faixas DORA separam o que as define, e quase nada além disso",
              f"Kruskal-Wallis entre Elite/High/Medium/Low (n = {int(t['n'].max())}); "
              f"p corrigido por Holm, controles fora da correção. n.s. = não significativo")
    return salvar(fig, destino)


def fig_convergencia(tabela: pd.DataFrame, destino: Path) -> Path:
    t = tabela.dropna(subset=["rho"]).sort_values("rho").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(LARGURA, 2.9))

    ax.axvspan(0.7, 1.0, color=SERIE[2], alpha=0.12, zorder=1)
    ax.axvline(0.7, color=TINTA_2, linewidth=1.0, linestyle=(0, (4, 2)), zorder=2)

    for i, linha in t.iterrows():
        ax.plot([0, linha["rho"]], [i, i], color=EIXO, linewidth=1.2, zorder=3)
        ax.scatter(linha["rho"], i, s=58, color=SERIE[0], edgecolor=SUPERFICIE,
                   linewidth=1.0, zorder=4)
        marca = "" if linha["associacao"] else "  n.s."
        ax.annotate(f"{fmt_num(linha['rho'], 3)}{marca}", xy=(linha["rho"], i),
                    xytext=(9, 0), textcoords="offset points", va="center",
                    fontsize=8, color=TINTA_2)

    ax.set_yticks(range(len(t)))
    ax.set_yticklabels(t["par"], fontsize=8.5)
    ax.set_xlim(-0.08, 1.0)
    ax.set_xlabel("Correlação de Spearman (ρ) entre a medida DORA e a medida de fluxo por PR")
    ax.text(0.85, (len(t) - 1) / 2, "mesmo constructo\nρ ≥ 0,7", fontsize=8,
            color=TINTA_2, ha="center", va="center")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(EIXO)
    ax.spines["bottom"].set_color(EIXO)
    ax.grid(axis="x", color=GRADE, linewidth=0.6)
    ax.set_axisbelow(True)

    cabecalho(ax, "DORA e fluxo por PR não medem a mesma coisa",
              f"Spearman por repositório nos 600 (n varia com a cobertura de cada medida); "
              f"p corrigido por Holm. Nenhum par alcança ρ = 0,7")
    return salvar(fig, destino)


def fig_confusao(tabela: pd.DataFrame, destino: Path, par: str | None = None) -> Path:
    t = tabela if par is None else tabela[tabela["par"] == par]
    agregado = float(t[t["estrato"] == "agregado"]["rho"].iloc[0])
    controles = [c for c in t["controle"].unique() if c != "nenhum"]

    fig, ax = plt.subplots(figsize=(LARGURA, 3.0))
    ax.axhline(agregado, color=TINTA, linewidth=1.2, zorder=4)
    ax.annotate(f"agregado  ρ = {fmt_num(agregado, 3)}", xy=(-0.45, agregado),
                xytext=(0, 6), textcoords="offset points", fontsize=8, color=TINTA, ha="left")

    for i, controle in enumerate(controles):
        do_controle = t[t["controle"] == controle]
        estratos = do_controle[do_controle["estrato"].isin(["Q1", "Q2", "Q3", "Q4"])]
        ax.scatter([i] * len(estratos), estratos["rho"], s=46, color=SERIE[0],
                   edgecolor=SUPERFICIE, linewidth=1.0, zorder=3, label="_")
        parcial = do_controle[do_controle["estrato"] == "parcial"]["rho"]
        if not parcial.empty:
            ax.scatter([i], parcial, s=120, marker="D", color=SERIE[1],
                       edgecolor=SUPERFICIE, linewidth=1.2, zorder=5)

    ax.set_xticks(range(len(controles)))
    ax.set_xticklabels(controles, fontsize=9)
    ax.set_xlim(-0.5, len(controles) - 0.5)
    ax.set_ylim(0, max(1.0, float(t["rho"].max()) * 1.15))
    ax.set_ylabel("ρ de Spearman")
    ax.set_xlabel("Variável controlada")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(EIXO)
    ax.spines["bottom"].set_color(EIXO)
    ax.grid(axis="y", color=GRADE, linewidth=0.6)
    ax.set_axisbelow(True)

    alcas = [plt.Line2D([], [], marker="o", color=SERIE[0], linestyle="", markersize=7),
             plt.Line2D([], [], marker="D", color=SERIE[1], linestyle="", markersize=8)]
    ax.legend(alcas, ["ρ dentro de cada quartil", "ρ parcial, controlando a variável"],
              fontsize=7.5, loc="lower right", frameon=False)

    cabecalho(ax, "A relação da RQ05 não é tamanho disfarçado: ela se mantém dentro dos quartis",
              f"Spearman entre frequência de deploy e CFR (b) nos 600; se a associação fosse "
              f"confusão por tamanho, os pontos cairiam para perto de zero")
    return salvar(fig, destino)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise.figuras_distribuicoes")
    ap.add_argument("--dataset", type=Path, default=Path("data/dataset_dora.csv"))
    ap.add_argument("--runs", type=Path, default=Path("data/eventos/runs.csv.gz"))
    ap.add_argument("--tabelas", type=Path, default=Path("analise/saida/tabelas"))
    ap.add_argument("--saida", type=Path, default=Path("analise/saida/figuras"))
    args = ap.parse_args(argv)

    estilo()
    df = pd.read_csv(args.dataset)
    print(fig_tlc(df, args.saida / "distribuicoes-tlc.png"))

    discriminancia = args.tabelas / "distribuicoes_discriminancia.csv"
    if discriminancia.exists():
        print(fig_discriminancia(pd.read_csv(discriminancia),
                                 args.saida / "distribuicoes-discriminancia.png"))

    convergencia = args.tabelas / "distribuicoes_convergencia.csv"
    if convergencia.exists():
        print(fig_convergencia(pd.read_csv(convergencia),
                               args.saida / "distribuicoes-convergencia.png"))

    confusao = args.tabelas / "distribuicoes_confusao.csv"
    if confusao.exists():
        t = pd.read_csv(confusao)
        print(fig_confusao(t, args.saida / "distribuicoes-confusao.png",
                           par="df_release_semana x cfr_b_release"))

    if args.runs.exists():
        por_repo = tabela_weibull(duracoes_por_repositorio(pd.read_csv(args.runs)))
        print(fig_weibull(por_repo, args.saida / "distribuicoes-weibull.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
