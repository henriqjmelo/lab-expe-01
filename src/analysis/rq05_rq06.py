"""
Analise e graficos de RQ05 e RQ06.

RQ05 — Sistemas populares sao escritos nas linguagens mais populares?
        Metrica: linguagem primaria do repositorio.

RQ06 — Sistemas populares possuem alto percentual de issues fechadas?
        Metrica: razao entre issues fechadas e total de issues.
"""

from src.analysis.base import (
    barras,
    contar_por,
    data_referencia,
    histograma,
    imprimir_resumo,
    load_repos,
)

# Quantas linguagens entram no grafico de barras. O dataset tem 43
# linguagens distintas e a cauda e formada por categorias com pouquissimos
# repositorios, que so poluiriam o eixo.
TOP_N_GRAFICO = 15

# Fonte de referencia declarada no README, usada para responder o que a RQ
# de fato pergunta: se as linguagens do dataset coincidem com as "mais
# populares" do ecossistema. As listas ficam fixas no codigo, com a data da
# consulta, pra que a analise continue reproduzivel mesmo depois que os
# rankings mudarem.
OCTOVERSE_TOP10 = [
    "TypeScript",
    "Python",
    "JavaScript",
    "Java",
    "C#",
    "PHP",
    "Shell",
    "C++",
    "HCL",
    "Go",
]
OCTOVERSE_FONTE = "GitHub Octoverse 2025 (por contribuidores ativos, agosto/2025)"

TIOBE_TOP10 = [
    "Python",
    "C",
    "C++",
    "Java",
    "C#",
    "JavaScript",
    "Visual Basic",
    "SQL",
    "R",
    "Rust",
]
TIOBE_FONTE = "TIOBE Index, agosto/2026"

# Faixas usadas na contagem por categoria da RQ06.
FAIXAS_RAZAO = [
    ("abaixo de 0,50", 0.0, 0.50),
    ("0,50 a 0,75", 0.50, 0.75),
    ("0,75 a 0,90", 0.75, 0.90),
    ("0,90 ou mais", 0.90, 1.01),
]


def _posicao(ranking: list[str], linguagem: str) -> str:
    """Posicao da linguagem no ranking de referencia, ou '-' se estiver fora."""
    if linguagem in ranking:
        return str(ranking.index(linguagem) + 1)
    return "-"


def analisar_rq05(repos: list[dict]) -> None:
    contagem = contar_por(repos, "primaryLanguage")
    sem_linguagem = contagem.pop(None, 0)
    com_linguagem = sum(contagem.values())

    print("=== RQ05 - linguagem primaria ===")
    print(f"  repositorios: {len(repos)}")
    print(f"  sem linguagem primaria informada: {sem_linguagem}")
    print(f"  com linguagem primaria: {com_linguagem}")
    print(f"  linguagens distintas: {len(contagem)}")

    print("  linguagens mais frequentes:")
    for linguagem, n in contagem.most_common(10):
        print(f"    {linguagem}: {n} ({n / com_linguagem * 100:.1f}%)")

    ranking = contagem.most_common(TOP_N_GRAFICO)
    # Os 85 repositorios sem linguagem primaria ficam fora do grafico: eles
    # nao formam uma linguagem, e coloca-los como barra num ranking de
    # linguagens sugeriria uma categoria que nao existe. O numero continua
    # reportado acima e no titulo do grafico, entao nada some da analise.
    caminho = barras(
        [linguagem for linguagem, _ in ranking],
        [n for _, n in ranking],
        f"RQ05 — linguagens primarias mais frequentes "
        f"({sem_linguagem} repositorios sem linguagem ficaram fora)",
        "Linguagem primaria",
        "rq05_linguagens.png",
    )
    print(f"  grafico: {caminho}")

    comparar_com_referencia(contagem, com_linguagem)


def comparar_com_referencia(contagem, com_linguagem: int) -> None:
    """
    Confronta o ranking do dataset com a fonte de referencia do README.

    A RQ nao pergunta quais linguagens aparecem no dataset, e sim se elas
    sao as mais populares segundo uma fonte externa. Sem esse cruzamento a
    resposta seria so uma contagem.
    """
    print("=== RQ05 - comparacao com a fonte de referencia ===")
    print(f"  referencias: {OCTOVERSE_FONTE}; {TIOBE_FONTE}")

    print("  posicao das linguagens do dataset nos rankings de referencia:")
    print("    linguagem            dataset  repos  octoverse  tiobe")
    for posicao, (linguagem, n) in enumerate(contagem.most_common(10), start=1):
        octo = _posicao(OCTOVERSE_TOP10, linguagem)
        tiobe = _posicao(TIOBE_TOP10, linguagem)
        print(f"    {linguagem:<20} {posicao:>7}  {n:>5}  {octo:>9}  {tiobe:>5}")

    for rotulo, ranking in (("Octoverse", OCTOVERSE_TOP10), ("TIOBE", TIOBE_TOP10)):
        no_top10 = [linguagem for linguagem in contagem if linguagem in ranking]
        repos_no_top10 = sum(contagem[linguagem] for linguagem in no_top10)
        ausentes = [linguagem for linguagem in ranking if linguagem not in contagem]
        print(f"  {rotulo}:")
        print(
            f"    repositorios em linguagens do top 10: {repos_no_top10} "
            f"({repos_no_top10 / com_linguagem * 100:.1f}% dos que tem linguagem)"
        )
        print(f"    linguagens do top 10 ausentes do dataset: {ausentes or 'nenhuma'}")

    # As duas listas discordam entre si, entao vale registrar onde elas se
    # sobrepoem: as linguagens que aparecem nas duas sao o nucleo mais
    # seguro de "linguagem popular" pra discussao no relatorio.
    comuns = [linguagem for linguagem in OCTOVERSE_TOP10 if linguagem in TIOBE_TOP10]
    repos_comuns = sum(contagem[linguagem] for linguagem in comuns if linguagem in contagem)
    print(f"  linguagens presentes nos dois rankings: {comuns}")
    print(
        f"    repositorios nessas linguagens: {repos_comuns} "
        f"({repos_comuns / com_linguagem * 100:.1f}%)"
    )


def analisar_rq06(repos: list[dict]) -> None:
    # Os repositorios sem nenhuma issue entram no CSV com totalIssues igual
    # a zero. A razao entre fechadas e total nao existe pra eles (divisao
    # por zero), entao ficam fora de todo o calculo, e nao contados como
    # zero, o que puxaria a mediana pra baixo sem motivo.
    razoes = [r["razaoIssues"] for r in repos if r["razaoIssues"] is not None]
    sem_issues = len(repos) - len(razoes)

    print("=== RQ06 - percentual de issues fechadas ===")
    print(f"  repositorios sem nenhuma issue (fora do calculo): {sem_issues}")
    imprimir_resumo("razao issues fechadas/total", razoes, casas=4)

    print("  distribuicao por faixa:")
    for rotulo, minimo, maximo in FAIXAS_RAZAO:
        n = sum(1 for razao in razoes if minimo <= razao < maximo)
        print(f"    {rotulo}: {n} ({n / len(razoes) * 100:.1f}%)")

    totalmente_fechadas = sum(1 for razao in razoes if razao == 1.0)
    print(f"  repositorios com 100% das issues fechadas: {totalmente_fechadas}")

    caminho = histograma(
        razoes,
        f"RQ06 — distribuicao da razao de issues fechadas "
        f"({sem_issues} repositorios sem issues ficaram fora)",
        "Issues fechadas / total de issues",
        "rq06_razao_issues.png",
        bins=20,
    )
    print(f"  grafico: {caminho}")


def analisar_relacao(repos: list[dict]) -> None:
    """
    A hipotese da issue #12 junta as duas RQs. Aqui a mediana da razao de
    issues e quebrada por linguagem primaria pra mostrar se o percentual de
    fechamento depende do ecossistema ou se e parecido em todos eles.
    """
    from statistics import median

    print("=== RQ05 x RQ06 - razao de issues fechadas por linguagem ===")
    contagem = contar_por(repos, "primaryLanguage")
    contagem.pop(None, None)

    for linguagem, _ in contagem.most_common(10):
        grupo = [
            r["razaoIssues"]
            for r in repos
            if r["primaryLanguage"] == linguagem and r["razaoIssues"] is not None
        ]
        if not grupo:
            continue
        print(f"    {linguagem:<20} n={len(grupo):>4}  mediana={median(grupo):.4f}")


if __name__ == "__main__":
    repos = load_repos()
    print(f"repositorios: {len(repos)}")
    print(f"data de referencia: {data_referencia(repos).date()}\n")

    analisar_rq05(repos)
    print()
    analisar_rq06(repos)
    print()
    analisar_relacao(repos)
