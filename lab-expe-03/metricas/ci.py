from __future__ import annotations

import statistics
from datetime import datetime

from metricas.cfr import FALHA, SUCESSO, classificar_conclusao
from metricas.recuperacao import Run


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def cfr_ci_com_reexecucoes(runs: list[Run]) -> dict:
    sucessos = falhas = reexecutados_sucesso = reexecutados_falha = 0
    for run in runs:
        classe = classificar_conclusao(run.conclusion)
        reexecutado = (run.run_attempt or 1) > 1
        if classe == SUCESSO:
            sucessos += 1
            reexecutados_sucesso += reexecutado
        elif classe == FALHA:
            falhas += 1
            reexecutados_falha += reexecutado
    validos = sucessos + falhas
    return {
        "n_validos": validos,
        "n_reexecutados_sucesso": reexecutados_sucesso,
        "n_reexecutados_falha": reexecutados_falha,
        "cfr": falhas / validos if validos else None,
        "cfr_com_reexecucoes": (falhas + reexecutados_sucesso) / validos if validos else None,
        "taxa_reexecucao": (reexecutados_sucesso + reexecutados_falha) / validos if validos else None,
    }


def tempo_feedback(runs: list[Run]) -> dict:
    minutos = [
        (_parse(r.updated_at) - _parse(r.run_started_at)).total_seconds() / 60
        for r in runs
        if classificar_conclusao(r.conclusion) in (SUCESSO, FALHA)
    ]
    minutos = [m for m in minutos if m >= 0]
    return {
        "n_runs": len(minutos),
        "mediana_minutos": statistics.median(minutos) if minutos else None,
    }
