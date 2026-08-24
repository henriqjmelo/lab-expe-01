"""
Base compartilhada da analise da S03.

Carrega o dataset com os tipos ja convertidos, calcula as metricas
derivadas que mais de uma RQ usa, e concentra o estilo dos graficos pra
que os PNG das 7 RQs saiam no mesmo padrao.
"""

import csv
import os
import statistics
from collections import Counter
from datetime import datetime

import matplotlib

matplotlib.use("Agg")  # so salva arquivo, nao abre janela
import matplotlib.pyplot as plt  # noqa: E402

DATA_PATH = "data/repositorios.csv"
GRAFICOS_DIR = "graficos"

DIAS_POR_ANO = 365.25


def _parse_data(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def load_repos(path: str = DATA_PATH) -> list[dict]:
    """
    Le o CSV com os tipos convertidos e adiciona as metricas derivadas.

    A data de referencia usada para idade e tempo sem push e o pushedAt
    mais recente do proprio dataset, que corresponde ao momento da coleta.
    Usar a data de hoje faria os numeros mudarem a cada execucao e as
    secoes do relatorio deixariam de bater entre si.
    """
    with open(path, newline="", encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))

    repos = []
    for linha in linhas:
        repos.append(
            {
                "nameWithOwner": linha["nameWithOwner"],
                "stargazerCount": int(linha["stargazerCount"]),
                "createdAt": _parse_data(linha["createdAt"]),
                "pullRequests": int(linha["pullRequests"]),
                "releases": int(linha["releases"]),
                "pushedAt": _parse_data(linha["pushedAt"]),
                "primaryLanguage": linha["primaryLanguage"] or None,
                "closedIssues": int(linha["closedIssues"]),
                "totalIssues": int(linha["totalIssues"]),
            }
        )

    referencia = max(r["pushedAt"] for r in repos)
    for r in repos:
        # RQ01: idade em anos
        r["idadeAnos"] = (referencia - r["createdAt"]).days / DIAS_POR_ANO
        # RQ04: tempo ate a ultima atualizacao, em dias
        r["diasSemPush"] = (referencia - r["pushedAt"]).days
        # RQ06: razao de issues fechadas. Fica None quando o repositorio nao
        # tem issue nenhuma, porque nesse caso a razao nao existe.
        total = r["totalIssues"]
        r["razaoIssues"] = r["closedIssues"] / total if total > 0 else None

    return repos


def data_referencia(repos: list[dict]) -> datetime:
    """Data usada como base para idade e tempo sem push."""
    return max(r["pushedAt"] for r in repos)


def resumo(valores: list[float]) -> dict:
    """Estatisticas basicas que todas as RQs precisam reportar."""
    ordenados = sorted(valores)
    quartis = statistics.quantiles(ordenados, n=4)
    return {
        "n": len(ordenados),
        "min": ordenados[0],
        "max": ordenados[-1],
        "mediana": statistics.median(ordenados),
        "media": statistics.fmean(ordenados),
        "q1": quartis[0],
        "q3": quartis[2],
    }


def imprimir_resumo(titulo: str, valores: list[float], casas: int = 1) -> None:
    r = resumo(valores)
    print(f"{titulo}")
    print(f"  n={r['n']}  min={r['min']:.{casas}f}  max={r['max']:.{casas}f}")
    print(f"  mediana={r['mediana']:.{casas}f}  media={r['media']:.{casas}f}")
    print(f"  Q1={r['q1']:.{casas}f}  Q3={r['q3']:.{casas}f}")


def contar_por(repos: list[dict], campo: str) -> Counter:
    """Contagem por categoria, usada na RQ05."""
    return Counter(r[campo] for r in repos)


def _nova_figura(figsize=(9, 5)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    return fig, ax


def salvar(fig, nome: str) -> str:
    """Salva o grafico em graficos/ e devolve o caminho."""
    os.makedirs(GRAFICOS_DIR, exist_ok=True)
    caminho = os.path.join(GRAFICOS_DIR, nome)
    fig.tight_layout()
    fig.savefig(caminho, dpi=120)
    plt.close(fig)
    return caminho


def histograma(valores, titulo, xlabel, nome, bins=30, log_y=False) -> str:
    fig, ax = _nova_figura()
    ax.hist(valores, bins=bins, color="#4878a8", edgecolor="white")
    if log_y:
        ax.set_yscale("log")
        ax.set_ylabel("Repositorios (escala log)")
    else:
        ax.set_ylabel("Repositorios")
    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    return salvar(fig, nome)


def barras(rotulos, valores, titulo, xlabel, nome) -> str:
    fig, ax = _nova_figura()
    ax.bar(rotulos, valores, color="#4878a8")
    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Repositorios")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return salvar(fig, nome)


def boxplot(grupos: dict, titulo, ylabel, nome, log_y=False) -> str:
    """grupos: {rotulo: [valores]}. Usado na RQ07."""
    fig, ax = _nova_figura()
    ax.boxplot(grupos.values(), tick_labels=list(grupos.keys()), showfliers=False)
    if log_y:
        ax.set_yscale("log")
    ax.set_title(titulo)
    ax.set_ylabel(ylabel)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return salvar(fig, nome)
