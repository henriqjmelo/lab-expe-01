"""Figuras do pipeline. Tudo em results/figures/, uma funcao por figura."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CORES = {"G1": "#1f77b4", "ZGC": "#d62728"}
plt.rcParams.update({"figure.dpi": 130, "savefig.bbox": "tight", "font.size": 10})


def _salvar(fig, destino: Path, nome: str) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / nome
    fig.savefig(caminho)
    plt.close(fig)
    return caminho


def distribuicao_por_celula(df: pd.DataFrame, destino: Path, metrica: str = "exec_ms") -> Path:
    """Violino + pontos: mostra a forma da distribuicao, nao so a media."""
    sub = df[df[metrica].notna()]
    benchmarks = sorted(sub["benchmark"].unique())
    heaps = sorted(sub["heap_mult"].unique())
    fig, eixos = plt.subplots(1, len(benchmarks), figsize=(3.1 * len(benchmarks), 4), sharey=False)
    eixos = np.atleast_1d(eixos)

    for eixo, bench in zip(eixos, benchmarks):
        dados, rotulos, cores = [], [], []
        for heap in heaps:
            for gc in ("G1", "ZGC"):
                v = sub[(sub["benchmark"] == bench) & (sub["heap_mult"] == heap) & (sub["gc"] == gc)][metrica]
                if len(v) > 1:
                    dados.append(v.to_numpy())
                    rotulos.append(f"{gc}\nh={heap:g}")
                    cores.append(CORES[gc])
        if not dados:
            continue
        partes = eixo.violinplot(dados, showextrema=False)
        for corpo, cor in zip(partes["bodies"], cores):
            corpo.set_facecolor(cor)
            corpo.set_alpha(0.35)
        for i, (v, cor) in enumerate(zip(dados, cores), start=1):
            x = np.random.default_rng(42).normal(i, 0.045, len(v))
            eixo.plot(x, v, ".", color=cor, markersize=3, alpha=0.6)
            eixo.plot([i - 0.25, i + 0.25], [np.median(v)] * 2, color=cor, linewidth=2)
        eixo.set_xticks(range(1, len(rotulos) + 1), rotulos, fontsize=8)
        eixo.set_title(bench, fontsize=10)
        eixo.grid(axis="y", alpha=0.25)
    eixos[0].set_ylabel(metrica)
    fig.suptitle(f"Distribuicao de {metrica} por celula (traco = mediana)", y=1.02)
    return _salvar(fig, destino, f"distribuicao_{metrica}.png")


def efeitos_com_ic(testes: pd.DataFrame, destino: Path) -> Path:
    """Forest plot da razao ZGC/G1 com IC 95%. A linha de 1,0 e o 'nao faz diferenca'."""
    sub = testes[testes["razao"].notna()].copy() if "razao" in testes else testes.iloc[0:0]
    if sub.empty:
        fig, eixo = plt.subplots(figsize=(7.0, 2.2))
        eixo.axis("off")
        eixo.text(0.5, 0.5, "nenhum par com n suficiente para o teste confirmatorio\n"
                            "(ver coluna 'motivo' em testes.csv)",
                  ha="center", va="center", fontsize=10, color="#8d99ae")
        return _salvar(fig, destino, "efeitos_ic.png")
    sub = sub.sort_values(["metrica", "benchmark", "heap_mult"]).reset_index(drop=True)
    rotulos = [f"{r.metrica} | {r.benchmark} | h={r.heap_mult:g}" for r in sub.itertuples()]
    y = np.arange(len(sub))

    fig, eixo = plt.subplots(figsize=(7.6, 0.42 * len(sub) + 1.8))
    for i, r in enumerate(sub.itertuples()):
        cor = "#d62728" if getattr(r, "significativo", False) else "#8d99ae"
        eixo.plot([r.razao_ic_baixo, r.razao_ic_alto], [i, i], color=cor, linewidth=2)
        eixo.plot(r.razao, i, "o", color=cor, markersize=6)
    eixo.axvline(1.0, color="#2b2d42", linestyle="--", linewidth=1)
    eixo.text(1.0, -0.72, " sem diferenca", fontsize=8, color="#2b2d42")
    eixo.set_yticks(y, rotulos, fontsize=8)
    eixo.invert_yaxis()
    eixo.set_xlabel("razao ZGC / G1 (IC 95% por bootstrap BCa)")
    eixo.set_title("Efeito por par, com intervalo de confianca\n(vermelho = significativo depois da correcao)")
    eixo.grid(axis="x", alpha=0.25)
    return _salvar(fig, destino, "efeitos_ic.png")


def ecdf_latencia(df: pd.DataFrame, destino: Path) -> Path | None:
    """ECDF do p99: a cauda inteira, nao so um resumo dela."""
    sub = df[df["lat_p99_ms"].notna()]
    if sub.empty:
        return None
    benchmarks = sorted(sub["benchmark"].unique())
    heaps = sorted(sub["heap_mult"].unique())
    fig, eixos = plt.subplots(len(benchmarks), len(heaps),
                              figsize=(4.2 * len(heaps), 3.2 * len(benchmarks)), squeeze=False)
    for i, bench in enumerate(benchmarks):
        for j, heap in enumerate(heaps):
            eixo = eixos[i][j]
            for gc in ("G1", "ZGC"):
                v = np.sort(sub[(sub["benchmark"] == bench) & (sub["heap_mult"] == heap)
                                & (sub["gc"] == gc)]["lat_p99_ms"].to_numpy())
                if v.size:
                    eixo.step(v, np.arange(1, v.size + 1) / v.size, where="post",
                              color=CORES[gc], label=gc, linewidth=1.8)
            eixo.set_title(f"{bench} | heap {heap:g}x", fontsize=9)
            eixo.set_xlabel("lat_p99_ms")
            eixo.set_ylabel("proporcao de runs")
            eixo.grid(alpha=0.25)
            eixo.legend(fontsize=8)
    fig.suptitle("Distribuicao acumulada da latencia p99", y=1.0)
    return _salvar(fig, destino, "ecdf_p99.png")


def interacao_gc_heap(df: pd.DataFrame, destino: Path) -> Path:
    """Razao ZGC/G1 em cada heap. Linhas nao paralelas = interacao (RQ2)."""
    sub = df[df["exec_ms"].notna()]
    heaps = sorted(sub["heap_mult"].unique())
    fig, eixo = plt.subplots(figsize=(6.4, 4.2))
    for bench in sorted(sub["benchmark"].unique()):
        razoes = []
        for heap in heaps:
            c = sub[(sub["benchmark"] == bench) & (sub["heap_mult"] == heap)]
            g = c[c["gc"] == "G1"]["exec_ms"]
            z = c[c["gc"] == "ZGC"]["exec_ms"]
            razoes.append(np.exp(np.log(z).mean() - np.log(g).mean()) if len(g) and len(z) else np.nan)
        eixo.plot(heaps, razoes, "o-", label=bench, linewidth=1.8)
    eixo.axhline(1.0, color="#2b2d42", linestyle="--", linewidth=1)
    eixo.set_xticks(heaps, [f"{h:g}x" for h in heaps])
    eixo.set_xlabel("multiplo do heap minimo")
    eixo.set_ylabel("razao ZGC / G1 do tempo")
    eixo.set_title("RQ2: a vantagem muda com o heap?\nlinhas nao paralelas indicam interacao")
    eixo.legend(fontsize=8)
    eixo.grid(alpha=0.25)
    return _salvar(fig, destino, "interacao_gc_heap.png")


def curva_de_poder(tabela_poder: pd.DataFrame, destino: Path) -> Path:
    """Poder x N, uma curva por CV, nos dois extremos do Holm."""
    fig, eixo = plt.subplots(figsize=(6.6, 4.2))
    cores = plt.cm.viridis(np.linspace(0.15, 0.85, tabela_poder["cv"].nunique()))
    for cor, (cv, grupo) in zip(cores, tabela_poder.groupby("cv")):
        g = grupo.sort_values("n")
        eixo.plot(g["n"], g["poder_welch_alfa"], "o-", color=cor, label=f"CV {cv*100:.0f}% (a=0,05)")
        eixo.plot(g["n"], g["poder_welch_holm_pior"], "s--", color=cor, alpha=0.75,
                  label=f"CV {cv*100:.0f}% (a/12)")
    eixo.axhline(0.80, color="#d62728", linestyle=":", linewidth=1.4)
    eixo.text(tabela_poder["n"].min(), 0.815, "alvo de 80%", fontsize=8, color="#d62728")
    eixo.set_xlabel("N (blocos por celula)")
    eixo.set_ylabel("poder")
    eixo.set_ylim(0, 1.05)
    eixo.set_title("Poder para detectar razao de 1,05\n(cheia: alfa; tracejada: pior caso do Holm)")
    eixo.legend(fontsize=7, ncol=2)
    eixo.grid(alpha=0.25)
    return _salvar(fig, destino, "poder.png")
