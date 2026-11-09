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
import pandas as pd
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


# ------------------------------------------------------------------ G4
PASTA_RESULTADOS = params.RAIZ / "results"
COR_TESTE = {"Pearson": estilo.COR_PEARSON, "Spearman": estilo.COR_SPEARMAN}
TRACO_SITUACAO = {"A": "-", "B": "--"}
NOME_SITUACAO = {"A": "situação A (normal)", "B": "situação B (lognormal)"}


def carregar_simulacoes(situacoes=("A", "B")) -> pd.DataFrame:
    """Le e concatena os CSVs de simulação existentes para as situações pedidas."""
    quadros = [pd.read_csv(caminho)
               for s in situacoes
               if (caminho := PASTA_RESULTADOS / f"situacao_{s}.csv").exists()]
    if not quadros:
        raise FileNotFoundError(
            f"Nenhum results/situacao_*.csv em {PASTA_RESULTADOS}. Rode python src/simulate.py.")
    return pd.concat(quadros, ignore_index=True)


def situacoes_disponiveis() -> list[str]:
    return [s for s in ("A", "B") if (PASTA_RESULTADOS / f"situacao_{s}.csv").exists()]


def tabela_erro_tipo_i(dados: pd.DataFrame | None = None) -> pd.DataFrame:
    dados = carregar_simulacoes() if dados is None else dados
    nulo = dados[dados["r_latente"] == 0.0]
    return nulo[["situacao", "teste", "repeticoes", "taxa_005", "taxa_001"]].sort_values(
        ["situacao", "teste"]
    ).reset_index(drop=True)


def figura_g3(dados: pd.DataFrame | None = None):
    """Erro tipo I por teste e situação, com IC aproximado de ±0,4 p.p."""
    estilo.aplicar()
    taxas = tabela_erro_tipo_i(dados)
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    situacoes = [s for s in ("A", "B") if s in set(taxas["situacao"])]
    centros = np.arange(len(situacoes), dtype=float)
    largura = 0.30
    yerr = 0.004
    for indice, teste in enumerate(("Pearson", "Spearman")):
        bloco = taxas[taxas["teste"] == teste].set_index("situacao").reindex(situacoes)
        posicoes = centros + (indice - 0.5) * largura
        valores = bloco["taxa_005"].to_numpy(dtype=float)
        ax.bar(
            posicoes, valores, width=largura * 0.9, color=COR_TESTE[teste], label=teste,
            yerr=np.full(len(valores), yerr), capsize=4, edgecolor="white", linewidth=0.7,
        )
        for x, valor in zip(posicoes, valores):
            ax.annotate(f"{valor:.2%}".replace(".", ","), (x, valor), xytext=(0, 7),
                        textcoords="offset points", ha="center", fontsize=8)
    ax.axhline(params.ALFA, color="#c44536", linestyle="--", linewidth=1.5,
               label="α nominal = 5%")
    ax.set_xticks(centros, [f"Situação {s}\n({'normal' if s == 'A' else 'lognormal'})" for s in situacoes])
    ax.set_ylim(0, max(0.075, float(taxas["taxa_005"].max()) + 0.015))
    ax.set_ylabel("Proporção de rejeições quando r = 0")
    ax.set_xlabel("Distribuição usada para simular os dados")
    ax.set_title("G3: erro tipo I fica próximo do nível nominal de 5%", loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper left", ncols=3, fontsize=8.5)
    ax.text(0.99, 0.02, "Barras de erro: ±0,4 ponto percentual", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8, color="#5c6672")
    fig.tight_layout()
    return fig


def vantagem_por_situacao(dados: pd.DataFrame, coluna: str = "taxa_005") -> dict[str, str]:
    """Quem tem mais poder em cada situacao, olhando so os efeitos maiores que zero."""
    resumo = {}
    com_efeito = dados[dados["r_latente"] > 0]
    for situacao, bloco in com_efeito.groupby("situacao"):
        tabela = bloco.pivot_table(index="r_latente", columns="teste", values=coluna)
        if {"Pearson", "Spearman"} - set(tabela.columns):
            continue
        diferenca = tabela["Pearson"] - tabela["Spearman"]
        if (diferenca > 0).all():
            resumo[situacao] = "Pearson acima em todos os efeitos"
        elif (diferenca < 0).all():
            resumo[situacao] = "Spearman acima em todos os efeitos"
        else:
            troca = float(diferenca.abs().idxmin())
            resumo[situacao] = f"a vantagem troca perto de r = {troca:.1f}".replace(".", ",")
    return resumo


def curvas_do_g4(dados: pd.DataFrame, coluna: str = "taxa_005") -> list[dict]:
    """Monta as curvas do G4, juntando numa so as que forem numericamente iguais.

    O Spearman cai nesse caso: a situacao B apenas aplica exp() aos valores latentes da A,
    e exp() nao muda a ordem dos valores, entao os postos — e com eles a decisao do teste —
    sao os mesmos nas duas. Desenhar duas linhas sobrepostas esconderia uma delas e deixaria
    a legenda prometendo uma curva que nao aparece no grafico.
    """
    curvas = []
    for teste, bloco_teste in dados.groupby("teste"):
        por_situacao = {s: b.sort_values("r_latente")
                        for s, b in bloco_teste.groupby("situacao")}
        situacoes = sorted(por_situacao)
        valores = [por_situacao[s][coluna].to_numpy(dtype=float) for s in situacoes]
        iguais = len(situacoes) > 1 and all(np.allclose(valores[0], v) for v in valores[1:])
        if iguais:
            bloco = por_situacao[situacoes[0]]
            curvas.append({
                "teste": teste, "situacoes": situacoes, "traco": "-",
                "x": bloco["r_latente"].to_numpy(dtype=float), "y": valores[0],
                "rotulo": f"{teste} — situações {' e '.join(situacoes)} (curvas idênticas)",
            })
            continue
        for situacao, y in zip(situacoes, valores):
            bloco = por_situacao[situacao]
            curvas.append({
                "teste": teste, "situacoes": [situacao],
                "traco": TRACO_SITUACAO.get(situacao, ":"),
                "x": bloco["r_latente"].to_numpy(dtype=float), "y": y,
                "rotulo": f"{teste} — {NOME_SITUACAO.get(situacao, situacao)}",
            })
    return curvas


def troca_de_vantagem(dados: pd.DataFrame, situacao: str, coluna: str = "taxa_005"):
    """Primeiro efeito positivo em que o Spearman passa o Pearson, ou None se nao passa."""
    bloco = dados[(dados["situacao"] == situacao) & (dados["r_latente"] > 0)]
    tabela = bloco.pivot_table(index="r_latente", columns="teste", values=coluna).sort_index()
    if {"Pearson", "Spearman"} - set(tabela.columns):
        return None
    virou = tabela.index[tabela["Spearman"] > tabela["Pearson"]]
    return float(virou.min()) if len(virou) else None


def figura_g4(coluna: str = "taxa_005"):
    """Curvas de poder: proporcao de rejeicoes x tamanho do efeito, por teste e situacao."""
    estilo.aplicar()
    dados = carregar_simulacoes()
    alfa = params.ALFA if coluna == "taxa_005" else params.ALFA_EXTRA

    fig, ax = plt.subplots(figsize=(9.8, 5.6))
    for curva in curvas_do_g4(dados, coluna):
        ax.plot(curva["x"], curva["y"],
                color=COR_TESTE.get(curva["teste"], "#555555"),
                ls=curva["traco"], marker="o", ms=4.5, lw=2, label=curva["rotulo"])

    ax.axhline(alfa, color="#8d99ae", ls=":", lw=1.2)
    ax.text(0.015, alfa - 0.042, f"α = {alfa:.0%} — em r = 0 a curva é o erro tipo I".replace(".", ","),
            fontsize=8, color="#5c6672", ha="left", transform=ax.get_yaxis_transform())
    ax.axhline(0.80, color="#8d99ae", ls=":", lw=1.2)
    ax.text(0.015, 0.815, "poder de 80%, a referência usual", fontsize=8, color="#5c6672",
            ha="left", transform=ax.get_yaxis_transform())

    # Marca onde o Spearman passa o Pearson: e a virada que decide a recomendacao do grupo.
    for situacao in situacoes_disponiveis():
        r_virada = troca_de_vantagem(dados, situacao, coluna)
        if r_virada is None:
            continue
        ax.axvline(r_virada, color="#6a4c93", ls="-.", lw=1.1, alpha=0.7)
        ax.annotate(f"situação {situacao}: daqui em diante\no Spearman detecta mais",
                    xy=(r_virada, 0.60), xytext=(7, 0), textcoords="offset points",
                    fontsize=8.5, color="#6a4c93", va="center")

    detalhe = "; ".join(f"situação {s}: {t}" for s, t in vantagem_por_situacao(dados, coluna).items())
    repeticoes = int(dados["repeticoes"].iloc[0])
    ax.set_title("G4: qual teste detecta mais depende da distribuição dos dados",
                 fontweight="bold", fontsize=12, loc="left", pad=22)
    ax.text(0, 1.015, detalhe, transform=ax.transAxes, fontsize=9, color="#5c6672")
    ax.set_xlabel("Correlação latente usada para gerar os dados (r, adimensional)")
    ax.set_ylabel(f"Proporção de rejeições em {repeticoes:_} repetições".replace("_", " "))
    ax.set_ylim(0, 1.04)
    ax.set_xticks(sorted(dados["r_latente"].unique()))
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    ex = exemplo_do_g2()
    print(f"conjunto de exemplo (Issue #188): {ex['conjunto']}, n = {ex['n']}")
    print(f"Pearson  r = {ex['r']:+.4f}  t = {ex['t']:+.4f}  p = {ex['p']:.4f}")
    print(f"Spearman r = {ex['r_spearman']:+.4f}              p = {ex['p_spearman']:.4f}")
    print(f"t critico t({ex['gl']}) bicaudal 5% = +-{ex['t_critico']:.4f}")
    saida = PASTA_RESULTADOS / "g2.png"
    figura_g2().savefig(saida, bbox_inches="tight")
    print("gravado:", saida)

    disponiveis = situacoes_disponiveis()
    if disponiveis:
        saida_g3 = PASTA_RESULTADOS / "g3.png"
        figura_g3().savefig(saida_g3, bbox_inches="tight")
        print("gravado:", saida_g3)
        print(f"\nG4 com as situacoes {', '.join(disponiveis)}", end="")
        print(" (falta a B, Issue #194)" if "B" not in disponiveis else "")
        for s, t in vantagem_por_situacao(carregar_simulacoes()).items():
            print(f"  situacao {s}: {t}")
        saida_g4 = PASTA_RESULTADOS / "g4.png"
        figura_g4().savefig(saida_g4, bbox_inches="tight")
        print("gravado:", saida_g4)
    else:
        print("\nG4 pulado: nenhum results/situacao_*.csv ainda")
