"""
Analise e graficos da RQ07 (bonus).

RQ07 — Sistemas escritos em linguagens mais populares recebem mais
        contribuicao externa, lancam mais releases e sao atualizados com
        mais frequencia?

A RQ nao tem metrica propria: ela cruza as metricas ja definidas em RQ02
(PRs aceitas), RQ03 (releases) e RQ04 (tempo ate a ultima atualizacao),
agrupadas pela linguagem primaria da RQ05.

Duas leituras sao produzidas aqui:

1. mediana das tres metricas por linguagem, com boxplot comparativo;
2. repositorios em linguagens do top 10 das fontes de referencia contra os
   demais, que e o que a pergunta de fato compara.
"""

from statistics import median, quantiles

from src.analysis.base import contar_por, data_referencia, load_repos
from src.analysis.base import boxplot as grafico_boxplot
from src.analysis.rq05_rq06 import (
    OCTOVERSE_FONTE,
    OCTOVERSE_TOP10,
    TIOBE_FONTE,
    TIOBE_TOP10,
)

# Corte minimo de repositorios por linguagem.
#
# O dataset tem 43 linguagens primarias distintas e uma cauda longa: 24
# delas aparecem em menos de 5 repositorios, e 12 aparecem em um unico
# repositorio. Comparar a mediana de uma linguagem com 2 repositorios
# contra a de Python, com 227, nao diz nada sobre a linguagem — diz sobre
# os dois projetos especificos que cairam ali.
#
# O corte foi fixado em 10 porque abaixo disso a mediana se apoia em menos
# de cinco observacoes de cada lado e um unico repositorio a desloca. O
# valor tambem cai num intervalo vazio da distribuicao (Swift tem 10,
# Kotlin tem 9), entao nao parte um grupo de linguagens equivalentes ao
# meio. Com esse corte sobram 13 linguagens, que cobrem 819 dos 905
# repositorios com linguagem informada (90,5%).
CORTE_MINIMO = 10

# Teto de releases.totalCount da API do GitHub, ja documentado em
# src/validate/rq03_rq04.py. Repositorios nesse valor tiveram a contagem
# truncada e o total real deles e maior.
RELEASES_API_CAP = 1000

# As tres metricas cruzadas pela RQ07. "maior_melhor" registra o sentido de
# leitura: em PRs e releases, mais e mais; em dias sem push, menos dias
# significa atualizacao mais frequente, entao a leitura se inverte.
METRICAS = [
    {
        "chave": "pullRequests",
        "rotulo": "PRs aceitas (RQ02)",
        "ylabel": "PRs aceitas (escala symlog)",
        "arquivo": "rq07_pull_requests.png",
        "titulo": "RQ07 — PRs aceitas por linguagem primaria",
        "casas": 0,
        "maior_melhor": True,
    },
    {
        "chave": "releases",
        "rotulo": "releases (RQ03)",
        "ylabel": "Releases publicadas (escala symlog)",
        "arquivo": "rq07_releases.png",
        "titulo": "RQ07 — releases publicadas por linguagem primaria",
        "casas": 0,
        "maior_melhor": True,
    },
    {
        "chave": "diasSemPush",
        "rotulo": "dias sem push (RQ04)",
        "ylabel": "Dias desde o ultimo push (escala symlog)",
        "arquivo": "rq07_dias_sem_push.png",
        "titulo": (
            "RQ07 — dias desde o ultimo push por linguagem primaria "
            "(menos dias = atualizacao mais frequente)"
        ),
        "casas": 0,
        "maior_melhor": False,
    },
]


def linguagens_analisadas(repos: list[dict]) -> list[tuple[str, int]]:
    """Linguagens acima do corte, da mais frequente para a menos frequente."""
    contagem = contar_por(repos, "primaryLanguage")
    contagem.pop(None, None)
    return [(ling, n) for ling, n in contagem.most_common() if n >= CORTE_MINIMO]


def _valores(repos: list[dict], linguagem: str, chave: str) -> list[float]:
    return [r[chave] for r in repos if r["primaryLanguage"] == linguagem]


def descrever_corte(repos: list[dict], linguagens: list[tuple[str, int]]) -> None:
    contagem = contar_por(repos, "primaryLanguage")
    sem_linguagem = contagem.pop(None, 0)
    com_linguagem = sum(contagem.values())
    cobertos = sum(n for _, n in linguagens)
    descartadas = len(contagem) - len(linguagens)

    print("=== RQ07 - recorte de linguagens ===")
    print(f"  repositorios: {len(repos)}")
    print(f"  sem linguagem primaria (fora da analise): {sem_linguagem}")
    print(f"  linguagens distintas no dataset: {len(contagem)}")
    print(f"  corte minimo adotado: {CORTE_MINIMO} repositorios por linguagem")
    print(f"  linguagens mantidas: {len(linguagens)}  descartadas: {descartadas}")
    print(
        f"  cobertura: {cobertos}/{com_linguagem} repositorios com linguagem "
        f"({cobertos / com_linguagem * 100:.1f}%)"
    )

    # O corte e defensavel do ponto de vista estatistico, mas tem um custo
    # que precisa ficar explicito: ele derruba linguagens que as proprias
    # fontes de referencia colocam no top 10. Sem isso, a leitura de que
    # "linguagem popular tem mais contribuicao" ficaria apoiada num
    # conjunto de populares menor do que a fonte declara.
    mantidas = {ling for ling, _ in linguagens}
    for nome, ranking in (("Octoverse", OCTOVERSE_TOP10), ("TIOBE", TIOBE_TOP10)):
        abaixo = [
            f"{ling} (n={contagem[ling]})"
            for ling in ranking
            if ling in contagem and ling not in mantidas
        ]
        fora = [ling for ling in ranking if ling not in contagem]
        print(f"  {nome} — top 10 que o corte deixou de fora: {abaixo or 'nenhuma'}")
        print(f"  {nome} — top 10 ausentes do dataset: {fora or 'nenhuma'}")


def analisar_metrica(repos: list[dict], linguagens: list[tuple[str, int]], metrica: dict) -> None:
    """Mediana e quartis da metrica por linguagem, mais o boxplot comparativo."""
    chave = metrica["chave"]
    casas = metrica["casas"]

    grupos = {}
    linhas = []
    for linguagem, n in linguagens:
        valores = _valores(repos, linguagem, chave)
        q1, _, q3 = quantiles(valores, n=4)
        grupos[f"{linguagem}\n(n={n})"] = valores
        linhas.append((linguagem, n, q1, median(valores), q3))

    print(f"=== RQ07 - {metrica['rotulo']} por linguagem ===")
    sentido = "maior = mais" if metrica["maior_melhor"] else "menor = atualizacao mais recente"
    print(f"  leitura: {sentido}")
    print(f"    {'linguagem':<20}{'n':>5}{'Q1':>12}{'mediana':>12}{'Q3':>12}")
    for linguagem, n, q1, med, q3 in sorted(linhas, key=lambda x: x[3], reverse=True):
        print(f"    {linguagem:<20}{n:>5}{q1:>12.{casas}f}{med:>12.{casas}f}{q3:>12.{casas}f}")

    # O boxplot mantem a ordem de frequencia das linguagens (a mesma da
    # RQ05) em vez da ordem da mediana, pra que os tres graficos possam ser
    # lidos lado a lado com as colunas nas mesmas posicoes.
    caminho = grafico_boxplot(
        grupos,
        metrica["titulo"],
        metrica["ylabel"],
        metrica["arquivo"],
        xlabel=(
            f"Linguagem primaria (apenas linguagens com ao menos "
            f"{CORTE_MINIMO} repositorios; outliers omitidos)"
        ),
        symlog_y=True,
    )
    print(f"  grafico: {caminho}")


def comparar_populares(repos: list[dict], linguagens: list[tuple[str, int]]) -> None:
    """
    Compara repositorios em linguagens do top 10 de referencia com os demais.

    A pergunta da RQ07 nao e "qual linguagem lidera cada metrica", e sim se
    linguagem popular anda junto com mais contribuicao, mais releases e
    atualizacao mais frequente. Isso so aparece agrupando as linguagens em
    populares e nao populares segundo a mesma fonte externa que a RQ05 usa,
    e nao olhando o ranking interno do dataset.
    """
    mantidas = [ling for ling, _ in linguagens]
    comuns = [ling for ling in OCTOVERSE_TOP10 if ling in TIOBE_TOP10]

    print("=== RQ07 - linguagens populares contra as demais ===")
    print(f"  referencias: {OCTOVERSE_FONTE}; {TIOBE_FONTE}")
    print(f"  apenas linguagens acima do corte de {CORTE_MINIMO} repositorios")

    for nome, ranking in (
        ("Octoverse top 10", OCTOVERSE_TOP10),
        ("TIOBE top 10", TIOBE_TOP10),
        ("nos dois rankings", comuns),
    ):
        populares = [ling for ling in mantidas if ling in ranking]
        demais = [ling for ling in mantidas if ling not in ranking]
        print(f"  {nome}:")
        print(f"    populares: {populares}")
        print(f"    demais:    {demais}")
        for metrica in METRICAS:
            chave, casas = metrica["chave"], metrica["casas"]
            dentro = [r[chave] for r in repos if r["primaryLanguage"] in populares]
            fora = [r[chave] for r in repos if r["primaryLanguage"] in demais]
            print(
                f"    {metrica['rotulo']:<22} "
                f"populares (n={len(dentro)}) mediana={median(dentro):.{casas}f}  |  "
                f"demais (n={len(fora)}) mediana={median(fora):.{casas}f}"
            )


def vies_releases(repos: list[dict], linguagens: list[tuple[str, int]]) -> None:
    """
    Onde o truncamento de releases da API se concentra.

    Essa contagem precisa acompanhar o grafico de releases: os
    repositorios no teto de 1000 aparecem com um valor menor que o real, e
    se eles se concentram em poucas linguagens, a comparacao entre
    linguagens fica enviesada justamente nas mais afetadas.
    """
    truncados = [r for r in repos if r["releases"] >= RELEASES_API_CAP]

    print("=== RQ07 - vies do truncamento de releases (RQ03) ===")
    print(
        f"  repositorios no teto de {RELEASES_API_CAP} releases da API: "
        f"{len(truncados)} de {len(repos)} ({len(truncados) / len(repos) * 100:.1f}%)"
    )
    print(f"    {'linguagem':<20}{'n':>5}{'truncados':>11}{'% da linguagem':>16}")
    for linguagem, n in linguagens:
        capados = sum(1 for r in truncados if r["primaryLanguage"] == linguagem)
        if capados == 0:
            continue
        print(f"    {linguagem:<20}{n:>5}{capados:>11}{capados / n * 100:>15.1f}%")

    js_ts = sum(1 for r in truncados if r["primaryLanguage"] in ("TypeScript", "JavaScript"))
    print(
        f"  TypeScript + JavaScript concentram {js_ts} dos {len(truncados)} truncados "
        f"({js_ts / len(truncados) * 100:.1f}%)"
    )
    print(
        "  efeito: a mediana de releases dessas linguagens esta subestimada "
        "em relacao ao valor real, entao a vantagem observada nelas e um piso, nao um teto."
    )


if __name__ == "__main__":
    repos = load_repos()
    print(f"repositorios: {len(repos)}")
    print(f"data de referencia: {data_referencia(repos).date()}\n")

    linguagens = linguagens_analisadas(repos)

    descrever_corte(repos, linguagens)
    for metrica in METRICAS:
        print()
        analisar_metrica(repos, linguagens, metrica)
    print()
    comparar_populares(repos, linguagens)
    print()
    vies_releases(repos, linguagens)
