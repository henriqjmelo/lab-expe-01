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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise.figuras_distribuicoes")
    ap.add_argument("--dataset", type=Path, default=Path("data/dataset_dora.csv"))
    ap.add_argument("--runs", type=Path, default=Path("data/eventos/runs.csv.gz"))
    ap.add_argument("--saida", type=Path, default=Path("analise/saida/figuras"))
    args = ap.parse_args(argv)

    estilo()
    df = pd.read_csv(args.dataset)
    print(fig_tlc(df, args.saida / "distribuicoes-tlc.png"))
    if args.runs.exists():
        por_repo = tabela_weibull(duracoes_por_repositorio(pd.read_csv(args.runs)))
        print(fig_weibull(por_repo, args.saida / "distribuicoes-weibull.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
