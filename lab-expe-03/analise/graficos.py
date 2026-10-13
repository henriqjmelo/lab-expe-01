from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

from analise import estatisticas as est
from metricas.dora import SEMANAS_POR_MES

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TINTA_FRACA = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"

SERIE = ("#2a78d6", "#eb6834", "#1baf7a")

DORA_COR = {"Elite": "#0d366b", "High": "#1c5cab", "Medium": "#3987e5", "Low": "#86b6ef"}
DORA_TEXTO = {"Elite": "#ffffff", "High": "#ffffff", "Medium": "#ffffff", "Low": TINTA}
ORDEM_DORA = ("Elite", "High", "Medium", "Low")

RAMPA_AZUL = ["#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

LARGURA = 7.2
DPI = 220


def estilo() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.labelsize": 9,
        "axes.labelcolor": TINTA_2,
        "axes.edgecolor": EIXO,
        "axes.linewidth": 0.8,
        "axes.facecolor": SUPERFICIE,
        "figure.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "grid.color": GRADE,
        "grid.linewidth": 0.6,
        "xtick.color": TINTA_FRACA,
        "ytick.color": TINTA_FRACA,
        "xtick.labelcolor": TINTA_2,
        "ytick.labelcolor": TINTA_2,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "xtick.major.pad": 5,
        "ytick.major.pad": 5,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "text.color": TINTA,
    })


def cabecalho(ax, titulo: str, sub: str, folga: float = 0) -> None:
    comum = dict(xy=(0, 1), xycoords="axes fraction", textcoords="offset points", ha="left", va="bottom",
                 annotation_clip=False)
    t = ax.annotate(titulo, xytext=(0, folga + 19), fontsize=10.5, fontweight="bold", color=TINTA, **comum)
    s = ax.annotate(sub, xytext=(0, folga + 5), fontsize=8.5, color=TINTA_2, **comum)
    ax.figure._cabecalho = (ax, [t, s])


def _alinhar_cabecalho(fig) -> None:
    if not hasattr(fig, "_cabecalho"):
        return
    ax, anotacoes = fig._cabecalho
    for a in anotacoes:
        a.set_visible(False)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    x0 = min(e.get_tightbbox(renderer).x0 for e in fig.axes if e.get_visible())
    xfrac = (x0 - ax.bbox.x0) / ax.bbox.width
    for a in anotacoes:
        a.xy = (xfrac, 1)
        a.set_visible(True)


def salvar(fig, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    _alinhar_cabecalho(fig)
    fig.savefig(destino, dpi=DPI, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return destino


def fmt_num(v: float, casas: int = 1) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v: float, casas: int = 0) -> str:
    return fmt_num(100 * v, casas) + "%"


def enxame(x: np.ndarray, largura_px: float, diametro_px: float, xlim_log: tuple[float, float]) -> np.ndarray:
    lo, hi = xlim_log
    px = (np.log10(x) - lo) / (hi - lo) * largura_px
    ordem = np.argsort(px)
    y = np.zeros(len(x))
    colocados: list[tuple[float, float]] = []
    for i in ordem:
        vizinhos = [(cx, cy) for cx, cy in colocados if abs(cx - px[i]) < diametro_px]
        passo = 0
        while True:
            for sinal in ((0,) if passo == 0 else (1, -1)):
                candidato = sinal * passo * diametro_px * 0.5
                if all((cx - px[i]) ** 2 + (cy - candidato) ** 2 >= diametro_px**2 for cx, cy in vizinhos):
                    y[i] = candidato
                    colocados.append((px[i], candidato))
                    break
            else:
                passo += 1
                continue
            break
    return y


def fig_funil(funil: pd.DataFrame, destino: Path) -> Path:
    rotulos = {
        "candidatos_busca": "Candidatos da busca",
        "fora_de_amostra_anterior": "Fora de amostra anterior",
        "avaliados": "Avaliados (ordem aleatória)",
        "com_actions": "Usam GitHub Actions",
        "min_5_releases": "≥ 5 releases na janela",
        "min_50_runs": "≥ 50 runs válidos",
        "amostra_final": "Amostra final",
    }
    candidatos = int(funil.loc[funil["etapa"] == "candidatos_busca", "restantes"].iloc[0])
    funil = funil[funil["etapa"] != "candidatos_busca"].reset_index(drop=True)
    if funil["restantes"].iloc[-1] == funil["restantes"].iloc[-2]:
        funil = funil.iloc[:-1].copy()
        rotulos = {**rotulos, funil["etapa"].iloc[-1]: rotulos[funil["etapa"].iloc[-1]] + " = amostra final"}
    fig, ax = plt.subplots(figsize=(LARGURA, 0.42 * len(funil) + 0.5))
    y = np.arange(len(funil))[::-1]
    topo = funil["restantes"].iloc[0]
    for yi, (_, linha) in zip(y, funil.iterrows()):
        ax.barh(yi, linha["restantes"], height=0.56, color=SERIE[0], linewidth=0)
        ax.text(-12, yi, rotulos.get(linha["etapa"], linha["etapa"]), ha="right", va="center", fontsize=9, color=TINTA)
        texto = f"{linha['restantes']:,}".replace(",", ".")
        if linha["etapa"] != "avaliados":
            anterior = funil["restantes"].iloc[_ - 1] if _ > 0 else topo
            if anterior:
                texto += f"   ({fmt_pct(linha['restantes'] / anterior)} da etapa anterior)"
        ax.text(linha["restantes"] + 14, yi, texto, va="center", fontsize=8.5, color=TINTA_2)
    ax.set_xlim(0, topo * 1.55)
    ax.set_ylim(-0.6, len(funil) - 0.4)
    ax.axis("off")
    cabecalho(ax, "Funil de seleção: o filtro de releases é o mais restritivo",
              f"Repositórios restantes após cada etapa, de {fmt_num(candidatos, 0)} candidatos da busca")
    return salvar(fig, destino)


def _faixas(ax, limites: list[float], nomes: list[str], xlim: tuple[float, float], contagens: dict[str, int], n: int):
    bordas = [xlim[0], *limites, xlim[1]]
    for (a, b), nome in zip(zip(bordas[:-1], bordas[1:]), nomes):
        ax.axvspan(a, b, color=DORA_COR[nome], alpha=0.09, linewidth=0, zorder=0)
        if a != xlim[0]:
            ax.axvline(a, color=EIXO, linewidth=0.8, zorder=1)
        meio = 10 ** ((np.log10(a) + np.log10(b)) / 2)
        ax.text(meio, 0.97, nome, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=8.5,
                fontweight="bold", color=TINTA)
        ax.text(meio, 0.895, f"{contagens.get(nome, 0)} repos · {fmt_pct(contagens.get(nome, 0) / n)}",
                transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=7.8, color=TINTA_2)


def _ticks_log(ax, valores: list[float], rotulos: list[str]) -> None:
    ax.xaxis.set_major_locator(FixedLocator(valores))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: rotulos[valores.index(v)] if v in valores else ""))
    ax.xaxis.set_minor_locator(NullLocator())


def fig_rq01(df: pd.DataFrame, destino: Path) -> Path:
    x = df["df_release_semana"].dropna().to_numpy()
    xlim = (0.07, 60.0)
    fig, ax = plt.subplots(figsize=(LARGURA, 3.0))
    largura_px = LARGURA * 72 * 0.9
    d = 5.6
    y = enxame(x, largura_px, d, (np.log10(xlim[0]), np.log10(xlim[1])))
    ax.set_xscale("log")
    ax.set_xlim(*xlim)
    lim_y = max(abs(y).max() + d * 3, 60)
    ax.set_ylim(-lim_y, lim_y * 1.45)
    limites = [1 / SEMANAS_POR_MES, 1, 7]
    nomes = ["Low", "Medium", "High", "Elite"]
    contagem = {
        "Low": int((x < limites[0]).sum()), "Medium": int(((x >= limites[0]) & (x < 1)).sum()),
        "High": int(((x >= 1) & (x < 7)).sum()), "Elite": int((x >= 7).sum()),
    }
    _faixas(ax, limites, nomes, xlim, contagem, len(x))
    ax.scatter(x, y, s=d**2 * 0.62, color=SERIE[0], edgecolor=SUPERFICIE, linewidth=0.6, zorder=3)
    mediana = np.median(x)
    ax.axvline(mediana, color=TINTA, linewidth=1.1, zorder=4, ymax=0.8)
    ax.text(mediana * 1.06, -lim_y * 0.92, f"mediana {fmt_num(mediana, 2)}/semana\n≈ 1 release a cada {fmt_num(7 / mediana, 0)} dias",
            fontsize=8, color=TINTA, va="bottom")
    _ticks_log(ax, [0.1, 0.25, 0.5, 1, 2, 5, 10, 25, 50], ["0,1", "0,25", "0,5", "1", "2", "5", "10", "25", "50"])
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])
    ax.set_xlabel("Releases publicadas por semana (escala log)")
    cabecalho(ax, "RQ 01 · Frequência de deploy: quase metade dos repositórios fica em Medium",
              f"Cada ponto é um repositório (n = {len(x)}); faixas ao fundo = tabela de referência DORA")
    return salvar(fig, destino)


def fig_rq02(df: pd.DataFrame, destino: Path) -> Path:
    par = df[["lt_a_release_dias", "lt_b_release_dias"]].dropna()
    par = par[(par > 0).all(axis=1)]
    a, b = par["lt_a_release_dias"].to_numpy(), par["lt_b_release_dias"].to_numpy()
    fig, ax = plt.subplots(figsize=(LARGURA * 0.62, LARGURA * 0.56))
    lim = (0.01, 2000)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    for limite in (1, 7, 30):
        ax.axvline(limite, color=GRADE, linewidth=0.7, zorder=0)
        ax.axhline(limite, color=GRADE, linewidth=0.7, zorder=0)
    ax.plot(lim, lim, color=TINTA_FRACA, linewidth=1, zorder=1)
    ax.text(0.03, 0.045, "y = x", color=TINTA_FRACA, fontsize=8, rotation=45, ha="center", va="center")
    ax.scatter(a, b, s=22, color=SERIE[0], edgecolor=SUPERFICIE, linewidth=0.6, alpha=0.9, zorder=3)
    abaixo = (b < a).mean()
    ax.text(0.97, 0.05, f"{fmt_pct(abaixo)} abaixo da diagonal:\nlead time (b) < (a)", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8.5, color=TINTA)
    ticks = [0.01, 0.1, 1, 7, 30, 365]
    rot = ["0,01", "0,1", "1", "7", "30", "365"]
    for eixo in (ax.xaxis, ax.yaxis):
        eixo.set_major_locator(FixedLocator(ticks))
        eixo.set_major_formatter(FuncFormatter(lambda v, _: rot[ticks.index(v)] if v in ticks else ""))
        eixo.set_minor_locator(NullLocator())
    ax.set_xlabel("Lead time (a) por release, em dias (log)")
    ax.set_ylabel("Lead time (b) por commit, em dias (log)")
    cabecalho(ax, "RQ 02 · As duas variantes de lead time divergem",
              f"Mediana por repositório (n = {len(par)}); grade nas fronteiras DORA (1, 7 e 30 dias)")
    return salvar(fig, destino)


def ecdf(valores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    v = np.sort(valores)
    return v, np.arange(1, len(v) + 1) / len(v)


def _degraus(ax, v, p, **kw):
    ax.step(np.r_[v[0], v], np.r_[0, p], where="post", linewidth=2, solid_joinstyle="round", **kw)


def fig_rq03(df: pd.DataFrame, destino: Path) -> Path:
    fig, ax = plt.subplots(figsize=(LARGURA, 3.0))
    ax.grid(axis="y")
    for limite, nome in ((0.15, "Elite ≤ 15%"), (0.30, "High ≤ 30%"), (0.45, "Medium ≤ 45%")):
        ax.axvline(limite, color=EIXO, linewidth=0.8, zorder=1)
        ax.text(limite, 1.03, nome, ha="center", va="bottom", fontsize=7.8, color=TINTA_2,
                transform=ax.get_xaxis_transform())
    series = (("cfr_a", "CFR (a) · falha de CI", SERIE[0]), ("cfr_b_release", "CFR (b) · release corrigida em ≤ 7 dias*", SERIE[1]))
    for coluna, rotulo, cor in series:
        v, p = ecdf(df[coluna].dropna().to_numpy())
        _degraus(ax, v, p, color=cor, label=rotulo, zorder=3)
        ate15 = (v <= 0.15).mean()
        ax.plot([0.15], [ate15], marker="o", markersize=6, color=cor, markeredgecolor=SUPERFICIE, markeredgewidth=1.5, zorder=4)
        ax.text(0.165, ate15 - 0.035, fmt_pct(ate15), va="top", ha="left", fontsize=8.5, color=TINTA, zorder=5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_pct(v)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_pct(v)))
    ax.set_xlabel("Change failure rate")
    ax.set_ylabel("% acumulado de repositórios")
    ax.legend(loc="lower right")
    cabecalho(ax, "RQ 03 · O proxy muda a conclusão: Elite pelo CI, disperso pela entrega",
              "Distribuição acumulada; o ponto marca a % de repositórios Elite (≤ 15%) · *heurística v0, preliminar",
              folga=14)
    return salvar(fig, destino)


def fig_rq04(df: pd.DataFrame, destino: Path) -> Path:
    v, p = ecdf(df["recuperacao_mediana_horas"].dropna().to_numpy())
    v = np.clip(v, 1 / 60, None)
    fig, ax = plt.subplots(figsize=(LARGURA, 3.0))
    ax.set_xscale("log")
    xlim = (1 / 60, 24 * 60)
    ax.set_xlim(*xlim)
    ax.set_ylim(0, 1)
    ax.grid(axis="y")
    cortes = ((1, "1 hora"), (24, "1 dia"), (168, "1 semana"))
    for limite, nome in cortes:
        ax.axvline(limite, color=EIXO, linewidth=0.8, zorder=1)
    _degraus(ax, v, p, color=SERIE[0], zorder=3)
    for limite, nome in cortes:
        frac = (v < limite).mean()
        ax.plot([limite], [frac], marker="o", markersize=6, color=SERIE[0], markeredgecolor=SUPERFICIE,
                markeredgewidth=1.5, zorder=4)
        if frac > 0.9:
            ax.text(limite * 1.18, frac - 0.05, f"{fmt_pct(frac)} < {nome}", ha="left", va="top", fontsize=8.5, color=TINTA)
        else:
            ax.text(limite * 0.86, frac + 0.035, f"{fmt_pct(frac)} < {nome}", ha="right", va="bottom", fontsize=8.5,
                    color=TINTA)
    nomes = (("Elite", 1 / 60, 1), ("High", 1, 24), ("Medium", 24, 168), ("Low", 168, xlim[1]))
    for nome, a, b in nomes:
        ax.text(10 ** ((np.log10(a) + np.log10(b)) / 2), 1.02, nome, transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=TINTA)
    _ticks_log(ax, [1 / 60, 0.25, 1, 6, 24, 168, 720], ["1 min", "15 min", "1 h", "6 h", "1 dia", "1 sem.", "30 dias"])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: fmt_pct(val)))
    ax.set_xlabel("Mediana do tempo de recuperação por repositório (escala log)")
    ax.set_ylabel("% acumulado de repositórios")
    episodios = df["n_episodios"].sum()
    censurados = df["n_episodios_censurados"].sum()
    cabecalho(ax, "RQ 04 · A maioria recupera o CI em menos de um dia",
              f"n = {len(v)} repositórios com episódio fechado · {fmt_num(episodios, 0)} episódios, "
              f"{fmt_pct(censurados / episodios, 1)} censurados (sem recuperação na janela)", folga=14)
    return salvar(fig, destino)


def fig_perfil(dist: pd.DataFrame, destino: Path) -> Path:
    fig, ax = plt.subplots(figsize=(LARGURA, 2.9))
    linhas = dist.iloc[::-1].reset_index(drop=True)
    altura = 0.56
    for i, linha in linhas.iterrows():
        esquerda = 0.0
        for nome in ORDEM_DORA:
            w = linha[nome]
            if w <= 0:
                continue
            ax.barh(i, w - 0.004, left=esquerda + 0.002, height=altura, color=DORA_COR[nome], linewidth=0)
            if w >= 0.06:
                ax.text(esquerda + w / 2, i, fmt_pct(w), ha="center", va="center", fontsize=8, color=DORA_TEXTO[nome])
            esquerda += w
        negrito = "bold" if linha["metrica"].startswith("Geral") else "normal"
        ax.text(-0.015, i, linha["metrica"], ha="right", va="center", fontsize=9, color=TINTA, fontweight=negrito)
        ax.text(1.012, i, f"n = {linha['n']}", ha="left", va="center", fontsize=8, color=TINTA_FRACA)
    ax.axhline(0.5, color=EIXO, linewidth=0.8)
    ax.set_xlim(0, 1)
    ax.set_ylim(-1.25, len(linhas) - 0.4)
    ax.axis("off")
    for k, nome in enumerate(ORDEM_DORA):
        ax.add_patch(Rectangle((k * 0.13, -1.05), 0.022, 0.3, color=DORA_COR[nome], linewidth=0))
        ax.text(0.03 + k * 0.13, -0.9, nome, va="center", fontsize=8.5, color=TINTA)
    cabecalho(ax, "Perfil DORA da amostra (combinação de referência C1)",
              "% de repositórios por categoria · Geral = mediana dos pontos das 4 métricas, arredondada para baixo · "
              "CFR (b) preliminar")
    return salvar(fig, destino)


def fig_rq05(df: pd.DataFrame, tabela: pd.DataFrame, destino: Path) -> Path:
    fig, eixos = plt.subplots(1, 2, figsize=(LARGURA, 3.1), sharex=True)
    for ax, (_, linha), cor in zip(eixos, tabela.iterrows(), SERIE[:2]):
        par = df[["df_release_semana", linha["coluna_y"]]].dropna()
        ax.set_xscale("log")
        ax.grid(axis="y")
        ax.scatter(par["df_release_semana"], par[linha["coluna_y"]], s=16, color=cor, edgecolor=SUPERFICIE,
                   linewidth=0.5, alpha=0.85, zorder=3)
        p = "p < 0,001" if linha["p"] < 0.001 else f"p = {fmt_num(linha['p'], 3)}"
        ax.text(0.03, 0.97, f"ρ = {fmt_num(linha['rho'], 2)}\n{p} · n = {linha['n']}", transform=ax.transAxes,
                va="top", fontsize=9, color=TINTA, zorder=5,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=SUPERFICIE, edgecolor="none", alpha=0.9))
        ax.set_ylim(-0.02, 1.02)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_pct(v)))
        ax.set_xlabel("Releases por semana (log)")
        ax.set_title(linha["y"] + (" · proxy de CI" if linha["coluna_y"] == "cfr_a" else " · proxy de entrega*"),
                     fontsize=9.5, pad=6)
        _ticks_log(ax, [0.1, 0.3, 1, 3, 10, 30], ["0,1", "0,3", "1", "3", "10", "30"])
    eixos[0].set_ylabel("Change failure rate")
    fig.tight_layout()
    cabecalho(eixos[0], "RQ 05 · Velocidade × estabilidade: a correlação depende do proxy de falha",
              "Spearman entre frequência de deploy e CFR · *heurística v0: mais releases = mais chances de uma "
              "\"corretiva\" em 7 dias", folga=20)
    return salvar(fig, destino)


def fig_rq06(tabela: pd.DataFrame, destino: Path) -> Path:
    fatores = list(dict.fromkeys(tabela["fator"]))
    metricas = list(dict.fromkeys(tabela["metrica"]))
    matriz = tabela.pivot(index="fator", columns="metrica", values="epsilon2").loc[fatores, metricas]
    sig = tabela.pivot(index="fator", columns="metrica", values="significativo").loc[fatores, metricas]
    cmap = LinearSegmentedColormap.from_list("azul", RAMPA_AZUL)
    vmax = 0.26
    fig, ax = plt.subplots(figsize=(LARGURA, 2.7))
    ax.imshow(matriz.to_numpy(dtype=float), cmap=cmap, vmin=0, vmax=vmax, aspect="auto")
    for i in range(len(fatores)):
        for j in range(len(metricas)):
            v = matriz.iat[i, j]
            escuro = v / vmax > 0.55
            texto = fmt_num(v, 2) + ("*" if sig.iat[i, j] else "")
            ax.text(j, i, texto, ha="center", va="center", fontsize=8.5,
                    color="#ffffff" if escuro else TINTA, fontweight="bold" if sig.iat[i, j] else "normal")
    for i in range(len(fatores) + 1):
        ax.axhline(i - 0.5, color=SUPERFICIE, linewidth=2)
    for j in range(len(metricas) + 1):
        ax.axvline(j - 0.5, color=SUPERFICIE, linewidth=2)
    ax.set_xticks(range(len(metricas)), metricas)
    ax.set_yticks(range(len(fatores)), fatores)
    ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)
    cabecalho(ax, "RQ 06 · Idade e tamanho da equipe se associam ao lead time; linguagem não",
              f"Tamanho de efeito ε² = H/(n−1) do Kruskal-Wallis · negrito* = p < 0,05 após Holm ({len(tabela)} testes)",
              folga=20)
    ax.text(len(metricas) - 0.5, len(fatores) - 0.35,
            "referência: ε² < 0,01 desprezível · < 0,06 pequeno · < 0,14 médio · ≥ 0,14 grande",
            ha="right", va="top", fontsize=7.6, color=TINTA_FRACA)
    return salvar(fig, destino)


def fig_rq07(completos: pd.DataFrame, pares: pd.DataFrame, destino: Path) -> Path:
    descricoes = {c.nome: c.descricao for c in est.COMBINACOES}
    nomes = {4: "Elite", 3: "High", 2: "Medium", 1: "Low"}
    n = len(completos)
    fig, (esq, dir_) = plt.subplots(1, 2, figsize=(LARGURA, 2.9), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.55})

    altura = 0.56
    for i, c in enumerate(["C3", "C2", "C1"]):
        esquerda = 0.0
        for pt in (4, 3, 2, 1):
            w = float((completos[c] == pt).mean())
            nome = nomes[pt]
            esq.barh(i, w - 0.004, left=esquerda + 0.002, height=altura, color=DORA_COR[nome], linewidth=0)
            if w >= 0.08:
                esq.text(esquerda + w / 2, i, fmt_pct(w), ha="center", va="center", fontsize=8, color=DORA_TEXTO[nome])
            esquerda += w
        esq.text(-0.03, i + 0.1, c, ha="right", va="center", fontsize=9, fontweight="bold", color=TINTA)
        esq.text(-0.03, i - 0.2, descricoes[c], ha="right", va="center", fontsize=7.2, color=TINTA_2)
    esq.set_xlim(0, 1)
    esq.set_ylim(-1.3, 2.5)
    esq.axis("off")
    for k, nome in enumerate(ORDEM_DORA):
        esq.add_patch(Rectangle((k * 0.25, -1.1), 0.04, 0.28, color=DORA_COR[nome], linewidth=0))
        esq.text(0.055 + k * 0.25, -0.96, nome, va="center", fontsize=8, color=TINTA)
    esq.text(0, 2.45, "Distribuição das categorias", fontsize=8.5, color=TINTA_2, va="bottom")

    movimentos = (("desceu", "Desceu", SERIE[1]), ("igual", "Igual", "#c3c2b7"), ("subiu", "Subiu", SERIE[0]))
    for i, (_, linha) in enumerate(pares.iloc[::-1].iterrows()):
        a, b = linha["par"].split("×")
        delta = completos[b].astype(int) - completos[a].astype(int)
        partes = {"desceu": float((delta < 0).mean()), "igual": float((delta == 0).mean()), "subiu": float((delta > 0).mean())}
        esquerda = 0.0
        for chave, _, cor in movimentos:
            w = partes[chave]
            dir_.barh(i, w - 0.004, left=esquerda + 0.002, height=altura, color=cor, linewidth=0)
            if w >= 0.08:
                dir_.text(esquerda + w / 2, i, fmt_pct(w), ha="center", va="center", fontsize=8,
                          color=TINTA if chave == "igual" else "#ffffff")
            esquerda += w
        dir_.text(-0.03, i, f"{a} × {b}", ha="right", va="center", fontsize=9, fontweight="bold", color=TINTA)
        dir_.text(1.03, i, f"κ = {fmt_num(linha['kappa_linear'], 2)}", ha="left", va="center", fontsize=8.5, color=TINTA)
    dir_.set_xlim(0, 1)
    dir_.set_ylim(-1.3, 2.5)
    dir_.axis("off")
    for k, (_, rotulo, cor) in enumerate(movimentos):
        dir_.add_patch(Rectangle((k * 0.3, -1.1), 0.045, 0.28, color=cor, linewidth=0))
        dir_.text(0.06 + k * 0.3, -0.96, rotulo, va="center", fontsize=8, color=TINTA)
    dir_.text(0, 2.45, "Mudança de categoria entre combinações", fontsize=8.5, color=TINTA_2, va="bottom")

    cabecalho(esq, "RQ 07 · Trocar a definição de deploy reclassifica até um terço dos repositórios",
              f"Classificação DORA geral de cada repositório (n = {n}) · κ = kappa de Cohen ponderado linear "
              "(1 = concordância perfeita)", folga=14)
    return salvar(fig, destino)


def fig_comparacao_ecdf(a: pd.DataFrame, b: pd.DataFrame, tabela: pd.DataFrame, destino: Path) -> Path:
    fig, eixos = plt.subplots(2, 3, figsize=(LARGURA, 4.6))
    escalas = {"df_release_semana": "log", "lt_a_release_dias": "log", "lt_b_release_dias": "log",
               "cfr_a": "linear", "cfr_b_release": "linear", "recuperacao_mediana_horas": "log"}
    for ax, (_, linha) in zip(eixos.flat, tabela.iterrows()):
        coluna = linha["coluna"]
        for dados, cor, rotulo in ((a, SERIE[0], "Amostra 1"), (b, SERIE[1], "Amostra 2")):
            v = dados[coluna].dropna().to_numpy()
            if escalas[coluna] == "log":
                v = v[v > 0]
            vv, p = ecdf(v)
            _degraus(ax, vv, p, color=cor, label=rotulo)
        ax.set_xscale(escalas[coluna])
        ax.set_ylim(0, 1)
        ax.grid(axis="y")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_pct(v)))
        if coluna.startswith("cfr"):
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_pct(v)))
        ax.set_title(f"{linha['metrica']} ({est.UNIDADES[coluna]})", fontsize=9, pad=4)
        sig = "* " if linha["p_holm"] < 0.05 else ""
        ax.text(0.97, 0.05, f"{sig}δ = {fmt_num(linha['cliff_delta'], 2)}\np(Holm) = {fmt_num(linha['p_holm'], 2)}",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=7.8, color=TINTA)
    eixos.flat[0].legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    cabecalho(eixos.flat[0], "Amostra 1 × amostra 2: as distribuições se sobrepõem?",
              "Distribuição acumulada por métrica · Mann-Whitney com Holm e delta de Cliff (|δ| < 0,147 desprezível) · "
              "* = p < 0,05", folga=18)
    return salvar(fig, destino)


def fig_comparacao_medianas(a: pd.DataFrame, b: pd.DataFrame, destino: Path) -> Path:
    fig, eixos = plt.subplots(1, len(est.METRICAS), figsize=(LARGURA, 2.4))
    for ax, (coluna, rotulo) in zip(eixos, est.METRICAS):
        for k, (dados, cor) in enumerate(((a, SERIE[0]), (b, SERIE[1]))):
            m = dados[coluna].median()
            lo, hi = est.ic_bootstrap_mediana(dados[coluna])
            ax.plot([k, k], [lo, hi], color=cor, linewidth=2, solid_capstyle="round")
            ax.plot([k], [m], marker="o", markersize=7, color=cor, markeredgecolor=SUPERFICIE, markeredgewidth=1.5)
        ax.set_xlim(-0.6, 1.6)
        ax.set_xticks([0, 1], ["A1", "A2"])
        ax.grid(axis="y")
        ax.set_title(rotulo, fontsize=8.5, pad=4)
        if coluna.startswith("cfr"):
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_pct(v)))
    fig.tight_layout()
    cabecalho(eixos[0], "Medianas por amostra, com IC de 95% (bootstrap)",
              "A1 = amostra 1 (azul) · A2 = amostra 2 (laranja) · intervalos que se sobrepõem indicam medianas compatíveis",
              folga=16)
    return salvar(fig, destino)
