"""Dashboard do Lab04: Pearson x Spearman em LOC x defeitos (KC1).

Comando unico (ver README.md):

    streamlit run app.py

As secoes 1 a 3 sao da S01. As secoes 4 a 7 entram na S02 e na entrega final.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ))  # dashboard_demo e analysis importam "src.<modulo>"

import dados_reais
import dashboard_demo
import dashboard_alfa
import dashboard_g3
import g1
import graficos
import params
from src.analise_alfa import comparar_alfa

URL_REPO = "https://github.com/henriqjmelo/lab-expe-01"
URL_PROJECTS = "https://github.com/users/henriqjmelo/projects/1"
URL_DASHBOARD = None  # publicar na entrega final e preencher aqui

st.set_page_config(page_title="Lab04 — Pearson × Spearman", layout="wide")


@st.cache_data
def resumo_real() -> dict:
    return params.estimar()


@st.cache_data
def testar_reais() -> pd.DataFrame:
    return dados_reais.testar_dados_reais()


@st.cache_data
def exemplo_g2() -> dict:
    return graficos.exemplo_do_g2()


@st.cache_resource
def figura_g1():
    return g1.figura_g1()


@st.cache_resource
def figura_g2():
    return graficos.figura_g2()


@st.cache_data
def simulacoes():
    return graficos.carregar_simulacoes()


@st.cache_resource
def figura_g4():
    return graficos.figura_g4()


SITUACOES = graficos.situacoes_disponiveis()


def num(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


p = resumo_real()
ex = exemplo_g2()

# ---------------------------------------------------------------- topo
st.title("Lab04 — Testes de hipótese por dentro")
st.markdown(
    f"**Par P5: Pearson × Spearman** &nbsp;·&nbsp; tamanho da classe (LOC) × nº de defeitos "
    f"&nbsp;·&nbsp; semente fixa `{params.SEED}`"
)
st.markdown(f"[Repositório]({URL_REPO}) &nbsp;·&nbsp; [GitHub Projects]({URL_PROJECTS})")
st.divider()

# ------------------------------------------------------------ seção 1
st.header("1. Cenário")
st.subheader("A pergunta")
st.markdown("> **Classes maiores concentram mais defeitos?**")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        "**H₀ —** não existe associação entre o tamanho da classe (LOC) e o número de "
        "defeitos: ρ = 0.\n\n"
        "**H₁ —** existe associação: ρ ≠ 0."
    )
with col_b:
    st.markdown(
        "**Teste bicaudal.** A literatura prevê associação positiva, mas uma associação "
        "*negativa* também seria relevante. Como não fixamos previamente a direção, dividimos "
        "α = 0,05 em 2,5% para cada cauda."
    )

st.subheader("De onde vieram os dados reais")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Classes (n)", p["n"])
c2.metric("Mediana de LOC", num(p["mediana_loc"], 0))
c3.metric("Assimetria de LOC", num(p["assimetria_loc"]))
c4.metric("Classes sem defeito", f'{p["classes_sem_defeito"]} ({num(p["prop_sem_defeito"] * 100, 1)}%)')
st.markdown(
    "Dataset **KC1 (NASA), nível de classe**, 145 classes, originado de Koru & Liu (2005) / "
    "repositório PROMISE. A cópia usada, a URL com commit fixo e a ressalva sobre a origem "
    "estão em [`data/README.md`](https://github.com/henriqjmelo/lab-expe-01/blob/main/lab-expe-04/data/README.md)."
)

st.subheader("O que seria errar, aqui")
st.markdown(
    f"""
| | O que é | O que custa no cenário |
| :--- | :--- | :--- |
| **Erro tipo I** | Concluir que LOC e defeitos andam juntos quando não andam | O time passa a priorizar revisão e refatoração por tamanho — esforço gasto num critério que não prevê nada |
| **Erro tipo II** | Existir a associação e o teste não detectar | Descarta-se um indicador de risco barato: o LOC já está medido, não custa nada usar |

**Qual é mais grave:** o **tipo I**. Ele cria uma política de priorização custosa e difícil de
reverter, enquanto o tipo II apenas mantém o time onde já está.
"""
)

st.subheader("O que o grupo espera, antes de rodar a S02")
st.info(
    f"""
**Expectativa registrada:** o **Spearman** deve se sair melhor na situação B.

Os dados reais são muito assimétricos (assimetria de {num(p["assimetria_loc"])} em LOC e
{num(p["assimetria_def"])} em defeitos) e o Pearson mede associação **linear sobre os valores
brutos** — um punhado de classes gigantes pesa desproporcionalmente no r. O Spearman trabalha
com postos: o posto da maior classe é só "a maior", não um valor 20× maior. Esperamos, então,
erro tipo I mais perto de 5% e curva de poder acima para o Spearman na situação B, com empate
ou leve vantagem do Pearson na situação A.

**Sinal contrário que já vimos.** Na subamostra de 30 classes reais (semente {params.SEED}),
o Pearson deu r = {num(p["sub30_pearson"], 3)} e o Spearman ρ = {num(p["sub30_spearman"], 3)}:
o Pearson achou *mais* associação. A relação é quase linear na escala log, e a lognormal
preserva a monotonicidade. Se a simulação confirmar essa direção, erramos a previsão — e o
motivo é este.
"""
)
st.divider()

# ------------------------------------------------------------ seção 2
st.header("2. Os dados")
st.pyplot(figura_g1(), width="stretch")
st.markdown(
    f"""
As marginais simuladas acompanham a forma dos dados reais: as duas variáveis são fortemente
assimétricas à direita, com a maioria das classes pequena e uma cauda longa de classes grandes
(assimetria {num(p["assimetria_loc"])} em LOC e {num(p["assimetria_def"])} em defeitos). Os
parâmetros da situação B saem do **log** das {p["n"]} classes reais — por isso lognormal, e não
normal. A diferença que sobra está nos defeitos: {p["classes_sem_defeito"]} das {p["n"]} classes
reais ({num(p["prop_sem_defeito"] * 100, 1)}%) têm zero defeito, e a lognormal nunca gera zero.
É a principal limitação do gerador, e ela empurra a simulação para um cenário um pouco mais
fácil que o real.
"""
)
st.divider()

# ------------------------------------------------------------ seção 3
st.header("3. Como os testes funcionam")
st.pyplot(figura_g2(), width="stretch")
st.markdown(
    f"""
**O que cada teste compara.** O Pearson compara o quanto LOC e defeitos variam juntos *em
valor*: a estatística é t = r·√(n−2)/√(1−r²), que sob H₀ segue uma t de Student com
{ex["gl"]} graus de liberdade quando n = {ex["n"]}. O Spearman faz a mesma conta, mas depois de
trocar cada valor pelo seu **posto** — ele enxerga ordem, não distância.

**Onde fica a região de rejeição.** São os {num(params.ALFA * 100, 1)}% mais extremos da curva,
divididos em {num(params.ALFA * 50, 1)}% por cauda, além de ±{num(ex["t_critico"], 3)}. Fica nas
pontas porque esses são os valores de t improváveis caso não houvesse associação nenhuma.

**O p-valor do exemplo.** É o conjunto da tabela abaixo ({ex["conjunto"]}, n = {ex["n"]},
correlação latente 0,3, semente {params.SEED}): o Pearson deu r = {num(ex["r"], 3)},
t = {num(ex["t"], 3)} e p = {num(ex["p"], 4)} — a área amarela do gráfico. Esse p diz que,
**se H₀ fosse verdadeira**, um t tão ou mais extremo apareceria em {num(ex["p"] * 100, 2)}% das
amostras. Ele **não** diz que há {num(ex["p"] * 100, 2)}% de chance de H₀ ser verdadeira, nem
mede o tamanho do efeito.
"""
)

dashboard_demo.renderizar_exemplo(st)

st.markdown(
    f"""
**Os dois testes discordam neste conjunto.** Com os mesmos {ex["n"]} pares, o Pearson rejeita H₀
(p = {num(ex["p"], 3)}) e o Spearman não (p = {num(ex["p_spearman"], 3)}). Não é erro de nenhum
dos dois: eles medem coisas diferentes, e com n = {ex["n"]} a distância entre medir valores e
medir postos já basta para cair em lados opostos de 0,05. Qual dos dois é mais confiável aqui é
exatamente o que a S02 vai medir.
"""
)
st.divider()

# ------------------------------------------------------------ seção 4
st.header("4. Erro tipo I")
erro_i = dashboard_g3.renderizar(st, graficos, num)
dashboard_alfa.renderizar(st, graficos, comparar_alfa, num)
st.divider()

# ------------------------------------------------------------ seção 5
st.header("5. Poder")
if not SITUACOES:
    st.caption("Entra na Issue #197. Rode `python src/simulate.py` para gerar os resultados.")
else:
    st.pyplot(figura_g4(), width="stretch")
    sim = simulacoes()
    repeticoes = f'{int(sim["repeticoes"].iloc[0]):,}'.replace(",", " ")
    st.markdown(f"**O que a curva é.** Cada linha mostra a proporção de rejeições em {repeticoes} repetições.")
    efeitos = sorted(sim.loc[sim["r_latente"] > 0, "r_latente"].unique())
    teto = max(efeitos)
    sem_efeito = sim.loc[sim["r_latente"] == 0].set_index(["situacao", "teste"])["taxa_005"]
    frases = []
    for situacao, bloco in sim.loc[sim["r_latente"] > 0].groupby("situacao", sort=True):
        poder = bloco.pivot(index="r_latente", columns="teste", values="taxa_005").sort_index()
        diferenca = poder["Pearson"] - poder["Spearman"]
        if (diferenca > 0).all():
            leitura = "Pearson teve maior poder em todos os efeitos avaliados"
        elif (diferenca < 0).all():
            leitura = "Spearman teve maior poder em todos os efeitos avaliados"
        else:
            ultimo_pearson = diferenca.index[diferenca > 0].max()
            primeiro_spearman = diferenca.index[diferenca < 0].min()
            leitura = (
                f"Pearson foi maior até r={num(ultimo_pearson, 1)}; Spearman foi maior "
                f"a partir de r={num(primeiro_spearman, 1)}"
            )
        final = poder.loc[teto]
        frases.append(
            f"Na situação {situacao}, {leitura}; em r={num(teto, 1)}, Pearson = "
            f"{num(final['Pearson'] * 100, 1)}% e Spearman = {num(final['Spearman'] * 100, 1)}%."
        )
    erro_i_g4 = "; ".join(
        f"{situacao}/{teste}: {num(taxa * 100, 2)}%"
        for (situacao, teste), taxa in sem_efeito.items()
    )
    st.markdown(
        f"Em r=0, as curvas representam erro tipo I: {erro_i_g4}. Para r>0, mostram poder. "
        + " ".join(frases)
        + f" Com n={int(sim['n'].iloc[0])}, efeitos pequenos continuam difíceis de detectar; o teste mais potente depende da distribuição."
    )

# ------------------------------------------------------------ seção 6
st.header("6. Dados reais")
real = testar_reais()
pe = real.set_index("teste").loc["Pearson"]
sp = real.set_index("teste").loc["Spearman"]


def fmt_p(valor: float) -> str:
    return "< 0,001" if valor < 0.001 else num(valor, 3)


def fmt_ic(linha) -> str:
    return f"[{num(linha['ic95_inf'], 2)}; {num(linha['ic95_sup'], 2)}]"


st.markdown(
    f"Os dois testes aplicados às **{int(pe['n'])} classes reais** do KC1: LOC × número de defeitos, "
    f"bicaudal, α = {num(params.ALFA, 2)}, {int(pe['gl'])} graus de liberdade."
)
tabela_real = pd.DataFrame({
    "Teste": real["teste"],
    "n": real["n"],
    "Estatística (r ou ρ)": real["estatistica"].map(lambda v: num(v, 3)),
    "t": real["t"].map(lambda v: num(v, 2)),
    "p-valor": real["p_valor"].map(fmt_p),
    "IC 95%": [fmt_ic(l) for _, l in real.iterrows()],
    "r² (variância compartilhada)": real["r2"].map(lambda v: f"{num(v * 100, 1)}%"),
    "Tamanho do efeito": real["tamanho_efeito"],
    "Decisão (α = 0,05)": real["decisao"],
})
st.dataframe(tabela_real, hide_index=True, width="stretch")
st.markdown(
    f"""
**Conclusão.** Os dois testes rejeitam H₀ com folga: há associação positiva entre o tamanho da
classe e o número de defeitos (Pearson r = {num(pe["estatistica"], 2)}, Spearman
ρ = {num(sp["estatistica"], 2)}, ambos com p {fmt_p(max(pe["p_valor"], sp["p_valor"]))}). O efeito é
**{pe["tamanho_efeito"]}** pelos dois critérios (|r| ≥ 0,5, rótulos de Cohen), mas não é
determinístico: o LOC explica cerca de {num(pe["r2"] * 100, 0)}% da variação dos defeitos pelo Pearson
e {num(sp["r2"] * 100, 0)}% da variação dos postos pelo Spearman; o resto vem de outros fatores.

**Por que os dois números diferem.** O Pearson ({num(pe["estatistica"], 2)}) fica acima do Spearman
({num(sp["estatistica"], 2)}), e os intervalos de confiança se sobrepõem em boa parte
({fmt_ic(pe)} contra {fmt_ic(sp)}). A explicação mais provável é a assimetria: poucas classes
enormes com muitos defeitos puxam o r de Pearson, enquanto o Spearman só enxerga a ordem. Há
ainda {p["classes_sem_defeito"]} classes ({num(p["prop_sem_defeito"] * 100, 1)}%) empatadas em zero
defeito, o que reduz a resolução dos postos e deixa o p-valor do Spearman aproximado. Com n = {int(pe["n"])}
a decisão não muda por nenhum dos dois caminhos; o que muda é a magnitude estimada.

**Correlação não é causa.** Classes grandes têm mais código onde errar, e o KC1 não separa esse
efeito de outros, como complexidade ou idade da classe.
"""
)
st.divider()

# ------------------------------------------------------------ seção 7
st.header("7. Conclusão")
b = sim[sim["situacao"] == "B"].pivot(index="r_latente", columns="teste", values="taxa_005").sort_index()
a = sim[sim["situacao"] == "A"].pivot(index="r_latente", columns="teste", values="taxa_005").sort_index()
r_spearman_maior = b.index[(b.index > 0) & (b["Spearman"] > b["Pearson"])].to_numpy(dtype=float)
faixa_spearman_b = (
    f"a partir de r={num(float(r_spearman_maior.min()), 1)}"
    if len(r_spearman_maior) else "em nenhum efeito positivo testado"
)
pearson_b_r01 = b.loc[0.1]
spearman_b_rmax = float(b.loc[b.index.max(), "Spearman"])
pearson_b_rmax = float(b.loc[b.index.max(), "Pearson"])
pearson_a_superior = bool((a.loc[a.index > 0, "Pearson"] > a.loc[a.index > 0, "Spearman"]).all())
erro_min, erro_max = float(erro_i["taxa_005"].min()), float(erro_i["taxa_005"].max())

st.subheader("Expectativa × resultado")
st.markdown(
    f"A expectativa registrada antes da S02 era que Spearman fosse mais robusto na situação B assimétrica. "
    f"Os resultados confirmam isso {faixa_spearman_b}: em r máximo, Spearman alcança "
    f"{num(spearman_b_rmax * 100, 1)}% de poder contra {num(pearson_b_rmax * 100, 1)}% do Pearson. "
    f"Em r=0,1, porém, Pearson tem {num(pearson_b_r01['Pearson'] * 100, 1)}% e Spearman "
    f"{num(pearson_b_r01['Spearman'] * 100, 1)}%. Na situação A normal, "
    f"{'Pearson tem maior poder em todos os efeitos avaliados' if pearson_a_superior else 'a vantagem de poder depende do efeito'}. "
    f"Com α=0,05, as taxas de erro tipo I ficaram entre {num(erro_min * 100, 2)}% e {num(erro_max * 100, 2)}%."
)

st.subheader("Recomendação para este cenário")
st.markdown(
    f"Como o KC1 real é bastante assimétrico e a pergunta busca uma associação monotônica entre LOC e defeitos, "
    f"recomendamos **Spearman como análise principal**, acompanhado de Pearson como análise complementar da relação linear. "
    f"A simulação mostra a troca relevante: Pearson é mais eficiente sob a normalidade simulada, enquanto Spearman detecta "
    f"melhor a associação moderada/forte na situação lognormal. Se a pergunta exigisse especificamente uma associação linear, "
    f"os dados fossem aproximadamente normais e não houvesse outliers influentes, Pearson seria a escolha preferível. "
    f"A decisão deve considerar a forma e o significado da relação, não apenas qual p-valor é menor."
)

st.subheader("Limitações")
st.markdown(
    f"A situação B usa uma transformação lognormal de uma normal bivariada latente; ela preserva os postos, mas não reproduz "
    f"os {p['classes_sem_defeito']} zeros ({num(p['prop_sem_defeito'] * 100, 1)}%) observados no KC1. Por isso, ela não representa "
    f"integralmente a distribuição real de defeitos. Além disso, n=30 é uma amostra pequena, a simulação controla uma relação "
    f"sintética e mede desempenho apenas para os efeitos de r=0 a r=0,5 escolhidos; não prova causalidade nem garante que "
    f"a recomendação se generalize a outros sistemas ou tamanhos amostrais."
)
