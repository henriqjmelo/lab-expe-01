"""Coleta de workflow runs do default branch (issues #136 e #139).

GET /repos/{owner}/{repo}/actions/runs?branch=...&event=push&created=A..B
devolve no maximo 1.000 resultados por consulta. A janela e consultada mes a
mes; um mes com mais de 1.000 runs e dividido ao meio recursivamente ate caber
(conta como "mes no teto"). Um unico dia ainda acima do teto fica truncado e e
contado a parte - nesse caso os dados daquele dia estao incompletos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from metricas.recuperacao import Run
from pipeline.github_client import GitHubClient, proxima_pagina

TETO_RESULTADOS = 1000


@dataclass
class ResultadoRuns:
    runs: list[Run] = field(default_factory=list)
    meses_no_teto: int = 0
    dias_truncados: int = 0


def intervalos_mensais(inicio: date, fim: date) -> list[tuple[date, date]]:
    """Fatias [primeiro dia, ultimo dia] de cada mes entre inicio e fim (inclusive)."""
    fatias = []
    atual = inicio
    while atual <= fim:
        proximo_mes = (atual.replace(day=1) + timedelta(days=32)).replace(day=1)
        ultimo = min(proximo_mes - timedelta(days=1), fim)
        fatias.append((atual, ultimo))
        atual = ultimo + timedelta(days=1)
    return fatias


def _para_run(bruto: dict) -> Run:
    return Run(
        workflow_id=bruto["workflow_id"],
        conclusion=bruto.get("conclusion"),
        run_started_at=bruto.get("run_started_at") or bruto["created_at"],
        updated_at=bruto["updated_at"],
    )


def _coletar_intervalo(
    cliente: GitHubClient,
    caminho: str,
    branch: str,
    ini: date,
    fim: date,
    resultado: ResultadoRuns,
) -> tuple[list[Run], int]:
    params = {"branch": branch, "event": "push", "created": f"{ini}..{fim}", "per_page": 100}
    dados, headers = cliente.requisitar(caminho, params)
    total = dados.get("total_count", 0)

    if total > TETO_RESULTADOS and ini < fim:
        meio = ini + (fim - ini) // 2
        a, _ = _coletar_intervalo(cliente, caminho, branch, ini, meio, resultado)
        b, _ = _coletar_intervalo(cliente, caminho, branch, meio + timedelta(days=1), fim, resultado)
        return a + b, total
    if total > TETO_RESULTADOS:
        resultado.dias_truncados += 1

    brutos = list(dados.get("workflow_runs") or [])
    url = proxima_pagina(headers.get("Link"))
    while url:
        dados, headers = cliente.requisitar(url)
        brutos.extend(dados.get("workflow_runs") or [])
        url = proxima_pagina(headers.get("Link"))
    return [_para_run(r) for r in brutos], total


def coletar_runs(
    cliente: GitHubClient, owner: str, repo: str, branch: str, inicio: date, fim: date
) -> ResultadoRuns:
    resultado = ResultadoRuns()
    caminho = f"repos/{owner}/{repo}/actions/runs"
    for ini, ult in intervalos_mensais(inicio, fim):
        runs, total = _coletar_intervalo(cliente, caminho, branch, ini, ult, resultado)
        if total > TETO_RESULTADOS:
            resultado.meses_no_teto += 1
        resultado.runs.extend(runs)
    return resultado
