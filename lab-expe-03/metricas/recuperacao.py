from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from metricas.cfr import FALHA, SUCESSO, classificar_conclusao


@dataclass
class Run:
    workflow_id: int
    conclusion: str | None
    run_started_at: str
    updated_at: str
    run_attempt: int = 1
    head_sha: str = ""


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def episodios_do_workflow(runs: list[Run]) -> tuple[list[float], int, int]:
    duracoes: list[float] = []
    houve_sucesso = False
    inicio_episodio: datetime | None = None
    falhas_iniciais = 0

    for run in sorted(runs, key=lambda r: r.run_started_at):
        classe = classificar_conclusao(run.conclusion)
        if classe == FALHA:
            if not houve_sucesso:
                falhas_iniciais += 1
            elif inicio_episodio is None:
                inicio_episodio = _parse(run.run_started_at)
        elif classe == SUCESSO:
            if inicio_episodio is not None:
                duracoes.append((_parse(run.updated_at) - inicio_episodio).total_seconds() / 3600)
                inicio_episodio = None
            houve_sucesso = True

    censurados = 1 if inicio_episodio is not None else 0
    return duracoes, censurados, falhas_iniciais


def tempo_recuperacao(runs: list[Run]) -> dict:
    por_workflow: dict[int, list[Run]] = defaultdict(list)
    for run in runs:
        por_workflow[run.workflow_id].append(run)

    duracoes: list[float] = []
    censurados = falhas_iniciais = 0
    for runs_wf in por_workflow.values():
        d, c, f = episodios_do_workflow(runs_wf)
        duracoes.extend(d)
        censurados += c
        falhas_iniciais += f

    total = len(duracoes) + censurados
    return {
        "n_episodios": total,
        "n_censurados": censurados,
        "prop_censurados": censurados / total if total else None,
        "mediana_horas": statistics.median(duracoes) if duracoes else None,
        "falhas_sem_sucesso_anterior": falhas_iniciais,
    }
