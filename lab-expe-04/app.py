"""Dashboard do Lab04: Pearson x Spearman em LOC x defeitos (KC1).

Comando unico (ver README.md):

    streamlit run app.py

As secoes 1 a 3 sao da S01. As secoes 4 a 7 entram na S02 e na entrega final.
"""
import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

import g1
import graficos
import params

URL_REPO = "https://github.com/henriqjmelo/lab-expe-01"
URL_PROJECTS = "https://github.com/users/henriqjmelo/projects/1"
URL_DASHBOARD = None  # publicar na entrega final e preencher aqui

st.set_page_config(page_title="Lab04 — Pearson × Spearman", layout="wide")


@st.cache_data
def resumo_real() -> dict:
    return params.estimar()


@st.cache_data
def exemplo_g2() -> dict:
    return graficos.exemplo_do_g2()


@st.cache_resource
def figura_g1():
    return g1.figura_g1()


@st.cache_resource
def figura_g2():
    return graficos.figura_g2()


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
link_dash = f"[Dashboard publicado]({URL_DASHBOARD})" if URL_DASHBOARD else "Dashboard: roda local (`streamlit run app.py`)"
st.markdown(f"[Repositório]({URL_REPO}) &nbsp;·&nbsp; [GitHub Projects]({URL_PROJECTS}) &nbsp;·&nbsp; {link_dash}")
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
        "*negativa* seria um achado relevante — indicaria que classes grandes recebem mais "
        "revisão. Fixar a direção antes de olhar os dados gastaria os 5% numa cauda só, "
        "então mantemos 2,5% em cada uma."
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

**O p-valor do exemplo.** Num conjunto da situação B com r latente {num(ex["r_latente"], 1)},
saiu r = {num(ex["r"], 3)}, t = {num(ex["t"], 3)} e p = {num(ex["p"], 4)} — a área amarela.
Esse p diz que, **se H₀ fosse verdadeira**, um t tão ou mais extremo apareceria em
{num(ex["p"] * 100, 2)}% das amostras. Ele **não** diz que há {num(ex["p"] * 100, 2)}% de chance
de H₀ ser verdadeira, nem mede o tamanho do efeito.
"""
)
st.divider()

# ------------------------------------- seções 4 a 7 (S02 e entrega final)
for titulo, issue, texto in [
    ("4. Erro tipo I", "#195", "Q1 e Q3: erro tipo I dos dois testes em cada situação, com a linha de 5% (G3)."),
    ("5. Poder", "#197", "Q2 e Q3: curvas de poder dos dois testes × tamanho do efeito (G4)."),
    ("6. Dados reais", "#199", "Estatística, p-valor, tamanho do efeito e conclusão de cada teste nas 145 classes do KC1."),
    ("7. Conclusão", "#200", "O que esperávamos × o que encontramos, e qual teste recomendamos."),
]:
    st.header(titulo)
    st.caption(f"Entra na Issue {issue}. {texto}")
