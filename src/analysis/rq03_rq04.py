"""Analise e graficos de RQ03 (releases) e RQ04 (atualizacao)."""

from src.analysis.base import data_referencia, histograma, imprimir_resumo, load_repos


RELEASES_API_CAP = 1000


def analisar_rq03(repos: list[dict]) -> None:
    releases = [repo["releases"] for repo in repos]
    sem_releases = sum(value == 0 for value in releases)
    truncados = sum(value >= RELEASES_API_CAP for value in releases)

    print("=== RQ03 - releases publicadas ===")
    imprimir_resumo("releases", releases, casas=0)
    print(f"  repositorios sem release: {sem_releases}")
    print(f"  repositorios no teto da API ({RELEASES_API_CAP}): {truncados}")

    caminho = histograma(
        [value for value in releases if value > 0],
        f"RQ03 — releases publicadas ({sem_releases} repositorios com zero; "
        f"{truncados} no teto da API)",
        "Releases publicadas",
        "rq03_releases.png",
        bins=30,
        log_x=True,
    )
    print(f"  grafico: {caminho}")


def analisar_rq04(repos: list[dict]) -> None:
    dias = [repo["diasSemPush"] for repo in repos]

    print("=== RQ04 - tempo ate a ultima atualizacao ===")
    imprimir_resumo("dias sem push", dias, casas=0)
    print(f"  repositorios atualizados no dia da coleta: {sum(value == 0 for value in dias)}")

    caminho = histograma(
        dias,
        "RQ04 — tempo ate a ultima atualizacao",
        "Dias desde o ultimo push",
        "rq04_dias_sem_push.png",
        bins=30,
    )
    print(f"  grafico: {caminho}")


if __name__ == "__main__":
    repos = load_repos()
    print(f"repositorios: {len(repos)}")
    print(f"data de referencia: {data_referencia(repos).date()}\n")
    analisar_rq03(repos)
    print()
    analisar_rq04(repos)