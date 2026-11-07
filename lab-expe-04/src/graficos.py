"""G2: distribuicao da estatistica do teste sob H0, com regiao de rejeicao e p-valor.

O teste de correlacao de Pearson usa t = r * sqrt(n - 2) / sqrt(1 - r^2), que sob H0
(nenhuma associacao) segue uma t de Student com n - 2 graus de liberdade. Com n = 30
sao 28 graus de liberdade e o corte bicaudal de 5% fica em +-2,048.

    python src/graficos.py     # grava results/g2.png
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

import estilo
import params

# analysis.py importa "src.generate", entao a raiz do projeto precisa estar no path
# tambem quando este arquivo roda direto (python src/graficos.py).
if str(params.RAIZ) not in sys.path:
    sys.path.insert(0, str(params.RAIZ))

import analysis

GL = params.N_SIM - 2
T_CRITICO = float(stats.t.ppf(1 - params.ALFA / 2, GL))

COR_REJEICAO = "#c44536"
COR_PVALOR = "#e9c46a"

def t_de_pearson(r: float, n: int = params.N_SIM) -> float:
    """Converte o r de Pearson na estatistica t que o teste compara com a t(n - 2)."""
    return float(r * np.sqrt(n - 2) / np.sqrt(1 - r**2))


def exemplo_do_g2() -> dict:
    """r, t e p-valor do conjunto de exemplo da S01, usados no G2 e no dashboard.

    E o mesmo conjunto da Issue #188 (analysis.gerar_exemplo): situacao A, n = 30,
    correlacao latente 0,3 e semente 42. Usar o conjunto oficial faz o p-valor marcado
    no G2 ser exatamente o da tabela dos dois testes na secao 3 do dashboard.
    """
    _, resultados = analysis.gerar_exemplo()
    por_teste = resultados.set_index("teste")
    pearson, spearman = por_teste.loc["Pearson"], por_teste.loc["Spearman"]
    return {
        "r": float(pearson["estatistica"]),
        "t": t_de_pearson(float(pearson["estatistica"]), n=int(pearson["n"])),
        "p": float(pearson["p_valor"]),
        "r_spearman": float(spearman["estatistica"]),
        "p_spearman": float(spearman["p_valor"]),
        "conjunto": str(resultados["conjunto"].iloc[0]),
        "n": int(pearson["n"]),
        "gl": GL,
        "t_critico": T_CRITICO,
    }


def figura_g2(t_obs: float | None = None):
    """Densidade t(28) sob H0, caudas de rejeicao sombreadas e o p-valor como area."""
    estilo.aplicar()
    ex = exemplo_do_g2()
    if t_obs is None:
        t_obs = ex["t"]
    t_obs = float(t_obs)
    p_obs = float(2 * stats.t.sf(abs(t_obs), GL))

    limite = max(4.2, abs(t_obs) + 1.2)
    x = np.linspace(-limite, limite, 1200)
    y = stats.t.pdf(x, GL)

    rejeita = np.abs(x) >= T_CRITICO          # as duas caudas de 2,5%
    extremo = np.abs(x) >= abs(t_obs)         # as duas caudas do p-valor

    rot_rejeicao = (f"Região de rejeição (α = {params.ALFA:.0%}, bicaudal: ±{T_CRITICO:.3f})"
                    .replace(".", ","))
    rot_pvalor = f"Área do p-valor = {p_obs:.4f}".replace(".", ",")
    rot_t = f"t observado no exemplo = {t_obs:+.3f}".replace(".", ",")

    def desenhar(eixo, com_rotulo: bool):
        eixo.plot(x, y, color=estilo.COR_PEARSON, lw=2,
                  label=f"Densidade t({GL}) sob H₀ (nenhuma associação)" if com_rotulo else None)
        eixo.fill_between(x, 0, y, where=rejeita, color=COR_REJEICAO, alpha=0.30,
                          label=rot_rejeicao if com_rotulo else None)
        # O p-valor fica por cima da regiao de rejeicao quando o resultado e
        # significativo, entao vai preenchido e hachurado para nao sumir.
        eixo.fill_between(x, 0, y, where=extremo, color=COR_PVALOR, alpha=0.95,
                          label=rot_pvalor if com_rotulo else None)
        for sinal in (-1, 1):
            eixo.axvline(sinal * T_CRITICO, color=COR_REJEICAO, ls="--", lw=1.2)
        eixo.axvline(t_obs, color="#264653", lw=2, label=rot_t if com_rotulo else None)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    desenhar(ax, com_rotulo=True)
    ax.set_xlim(-limite, limite)
    ax.set_ylim(0, stats.t.pdf(0, GL) * 1.26)
    ax.set_title(f"G2: o exemplo cai na região de rejeição (p = {p_obs:.4f} < 0,05)".replace(".", ","),
                 fontweight="bold")
    ax.set_xlabel(f"Estatística t do teste de Pearson (adimensional, {GL} graus de liberdade)")
    ax.set_ylabel("Densidade de probabilidade sob H₀")
    ax.legend(loc="upper left", fontsize=8)

    # As caudas sao finas demais na escala da densidade: o zoom e o que torna
    # a area do p-valor visivel, que e o ponto do G2.
    zoom = ax.inset_axes([0.68, 0.42, 0.30, 0.46])
    desenhar(zoom, com_rotulo=False)
    zoom.set_xlim(1.6, limite)
    zoom.set_ylim(0, float(stats.t.pdf(1.6, GL)) * 1.08)
    zoom.set_title("zoom da cauda direita", fontsize=8.5)
    zoom.tick_params(labelsize=7.5)
    zoom.grid(alpha=0.15)
    zoom.annotate("2,5%", xy=(T_CRITICO + 0.12, 0.012), fontsize=8, color=COR_REJEICAO)
    ax.indicate_inset_zoom(zoom, edgecolor="#8d99ae", alpha=0.6)

    fig.tight_layout()
    return fig


if __name__ == "__main__":
    ex = exemplo_do_g2()
    print(f"conjunto de exemplo (Issue #188): {ex['conjunto']}, n = {ex['n']}")
    print(f"Pearson  r = {ex['r']:+.4f}  t = {ex['t']:+.4f}  p = {ex['p']:.4f}")
    print(f"Spearman r = {ex['r_spearman']:+.4f}              p = {ex['p_spearman']:.4f}")
    print(f"t critico t({ex['gl']}) bicaudal 5% = +-{ex['t_critico']:.4f}")
    saida = params.RAIZ / "results" / "g2.png"
    figura_g2().savefig(saida, bbox_inches="tight")
    print("gravado:", saida)
