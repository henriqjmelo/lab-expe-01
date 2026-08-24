"""
Analise e graficos de RQ01 e RQ02.

RQ01 — Sistemas populares sao maduros/antigos?
        Metrica: idade do repositorio, em anos, a partir de createdAt.

RQ02 — Sistemas populares recebem muita contribuicao externa?
        Metrica: total de pull requests aceitas (MERGED).
"""

import numpy as np

from src.analysis.base import (
    data_referencia,
    histograma,
    imprimir_resumo,
    load_repos,
    resumo,
)

# Faixas de idade usadas na contagem por categoria da RQ01.
FAIXAS_IDADE = [
    ("menos de 5 anos", 0, 5),
    ("5 a 10 anos", 5, 10),
    ("10 a 15 anos", 10, 15),
    ("15 anos ou mais", 15, float("inf")),
]


def analisar_rq01(repos: list[dict]) -> None:
    idades = [r["idadeAnos"] for r in repos]

    print("=== RQ01 - idade dos repositorios ===")
    imprimir_resumo("idade (anos)", idades)

    print("  distribuicao por faixa:")
    for rotulo, minimo, maximo in FAIXAS_IDADE:
        n = sum(1 for i in idades if minimo <= i < maximo)
        print(f"    {rotulo}: {n} ({n / len(idades) * 100:.1f}%)")

    caminho = histograma(
        idades,
        "RQ01 — distribuicao da idade dos repositorios",
        "Idade em anos",
        "rq01_idade.png",
        bins=25,
    )
    print(f"  grafico: {caminho}")


def analisar_rq02(repos: list[dict]) -> None:
    prs = [r["pullRequests"] for r in repos]
    sem_pr = [p for p in prs if p == 0]
    com_pr = [p for p in prs if p > 0]

    print("=== RQ02 - pull requests aceitas ===")
    imprimir_resumo("PRs aceitas", prs, casas=0)
    print(f"  repositorios sem nenhuma PR aceita: {len(sem_pr)}")

    # A distribuicao e muito assimetrica: mediana em 768 e maximo acima de
    # 100 mil. Num histograma de escala linear quase tudo cai na primeira
    # barra. Por isso os intervalos sao espacados em escala logaritmica.
    # Os repositorios com zero PR ficam fora do grafico, porque log de zero
    # nao existe, mas continuam contados no texto acima.
    bins = np.logspace(0, np.log10(max(com_pr)), 30)
    caminho = histograma(
        com_pr,
        f"RQ02 — distribuicao de PRs aceitas ({len(sem_pr)} repositorios com zero ficaram fora)",
        "PRs aceitas (escala log)",
        "rq02_pull_requests.png",
        bins=bins,
        log_x=True,
    )
    print(f"  grafico: {caminho}")


def analisar_relacao(repos: list[dict]) -> None:
    """
    A hipotese da issue #10 liga as duas RQs: repositorios mais antigos
    teriam mais PRs aceitas por terem tido mais tempo de receber
    contribuicao. Aqui a mediana de PRs e quebrada por faixa de idade pra
    dar base a essa discussao no relatorio.
    """
    print("=== RQ01 x RQ02 - PRs aceitas por faixa de idade ===")
    for rotulo, minimo, maximo in FAIXAS_IDADE:
        grupo = [r["pullRequests"] for r in repos if minimo <= r["idadeAnos"] < maximo]
        if not grupo:
            continue
        r = resumo(grupo)
        print(f"  {rotulo}: n={r['n']}  mediana={r['mediana']:.0f}")


if __name__ == "__main__":
    repos = load_repos()
    print(f"repositorios: {len(repos)}")
    print(f"data de referencia: {data_referencia(repos).date()}\n")

    analisar_rq01(repos)
    print()
    analisar_rq02(repos)
    print()
    analisar_relacao(repos)
