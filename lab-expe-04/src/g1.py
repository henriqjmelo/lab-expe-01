"""G1: dados reais (KC1) ao lado dos dados simulados da situacao B.

Mostra so as marginais (LOC e defeitos), que e o que a situacao B herda dos dados
reais. A correlacao latente r nao altera as marginais, entao nao entra aqui.

    python src/g1.py     # grava results/g1.png
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import estilo
import params


def amostra_marginais_b(n: int = 10_000, seed: int = params.SEED):
    """n observacoes das marginais lognormais da situacao B (mesmos parametros de generate.py)."""
    rng = np.random.default_rng(seed)
    loc = np.exp(rng.normal(params.LOC_LOG_MU, params.LOC_LOG_SIGMA, n))
    defeitos = np.exp(rng.normal(params.DEF_LOG_MU, params.DEF_LOG_SIGMA, n))
    return loc, defeitos


def figura_g1():
    estilo.aplicar()
    real = params.carregar_reais()
    loc_r = real[params.COL_LOC].to_numpy()
    def_r = real[params.COL_DEF].to_numpy()
    loc_s, def_s = amostra_marginais_b()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

    # Painel 1: LOC em escala log
    bins = np.logspace(0, np.log10(max(loc_r.max(), np.percentile(loc_s, 99.5))), 30)
    ax1.hist(loc_r, bins=bins, weights=np.full(len(loc_r), 1 / len(loc_r)), alpha=0.65, color=estilo.COR_REAL,
             label=f"Dados reais (KC1, n = {len(loc_r)})")
    ax1.hist(loc_s, bins=bins, weights=np.full(len(loc_s), 1 / len(loc_s)), alpha=0.55, color=estilo.COR_SIMULADO,
             label="Simulado, situação B (lognormal)")
    ax1.set_xscale("log")
    ax1.set_title("Tamanho da classe (LOC)")
    ax1.set_xlabel("Linhas de código (LOC, escala log)")
    ax1.set_ylabel("Proporção das classes")
    ax1.legend(loc="upper left", fontsize=8)

    # Painel 2: defeitos em escala log de (defeitos + 1) para caber os zeros
    bins2 = np.logspace(0, np.log10(def_r.max() + 1), 22)
    ax2.hist(def_r + 1, bins=bins2, weights=np.full(len(def_r), 1 / len(def_r)), alpha=0.65, color=estilo.COR_REAL,
             label=f"Dados reais ({int((def_r == 0).sum())} de {len(def_r)} sem defeito)")
    ax2.hist(def_s + 1, bins=bins2, weights=np.full(len(def_s), 1 / len(def_s)), alpha=0.55, color=estilo.COR_SIMULADO,
             label="Simulado, situação B (nunca zero)")
    ax2.set_xscale("log")
    ticks = [0, 1, 3, 10, 30, 100]
    ax2.set_xticks([t + 1 for t in ticks])
    ax2.set_xticklabels([str(t) for t in ticks])
    ax2.minorticks_off()
    ax2.set_title("Número de defeitos por classe")
    ax2.set_xlabel("Defeitos (nº, escala log de defeitos + 1)")
    ax2.set_ylabel("Proporção das classes")
    ax2.legend()

    fig.suptitle("G1: dados reais × situação B simulada", fontweight="bold")
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    saida = params.RAIZ / "results" / "g1.png"
    figura_g1().savefig(saida, bbox_inches="tight")
    print("gravado:", saida)
