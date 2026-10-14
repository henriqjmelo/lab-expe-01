from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from datetime import datetime

_PRODUCAO = re.compile(r"prod|production|live|release|main|master|pages", re.IGNORECASE)
_NAO_PRODUCAO = re.compile(r"preview|staging|stage|test|dev|pr-|pull|review|sandbox|canary|qa", re.IGNORECASE)

SUCESSO_DEPLOY = frozenset({"SUCCESS", "INACTIVE", "ACTIVE"})
FALHA_DEPLOY = frozenset({"FAILURE", "ERROR"})


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def _horas(inicio: str, fim: str) -> float:
    return (_parse(fim) - _parse(inicio)).total_seconds() / 3600


def _mediana(valores: list[float]) -> float | None:
    return statistics.median(valores) if valores else None


@dataclass
class PullRequest:
    estado: str
    created_at: str
    merged_at: str = ""
    closed_at: str = ""
    primeira_resposta_at: str = ""


def metricas_prs(prs: list[PullRequest], semanas: float) -> dict:
    mergeados = [p for p in prs if p.estado == "merged" and p.merged_at]
    fechados = [p for p in prs if p.estado == "closed"]
    respondidos = [p for p in prs if p.primeira_resposta_at]
    decididos = len(mergeados) + len(fechados)
    return {
        "n_prs_mergeados": len(mergeados),
        "prs_mergeados_semana": len(mergeados) / semanas if semanas else None,
        "lt_pr_mediana_horas": _mediana([_horas(p.created_at, p.merged_at) for p in mergeados]),
        "primeira_resposta_mediana_horas": _mediana(
            [max(_horas(p.created_at, p.primeira_resposta_at), 0.0) for p in respondidos]
        ),
        "prop_prs_sem_resposta": 1 - len(respondidos) / len(prs) if prs else None,
        "taxa_aceitacao_pr": len(mergeados) / decididos if decididos else None,
    }


def metricas_bugs(issues: list[tuple[str, str, bool]]) -> dict:
    bugs = [(criada, fechada) for criada, fechada, eh_bug in issues if eh_bug]
    return {
        "n_bugs_fechados": len(bugs),
        "resolucao_bug_mediana_horas": _mediana([_horas(c, f) for c, f in bugs]),
    }


@dataclass
class Deployment:
    created_at: str
    environment: str
    state: str
    status: str = ""


def eh_producao(ambiente: str) -> bool:
    return bool(_PRODUCAO.search(ambiente or "")) and not _NAO_PRODUCAO.search(ambiente or "")


def resultado_deploy(d: Deployment) -> str | None:
    final = d.status or d.state
    if final in FALHA_DEPLOY or d.state in FALHA_DEPLOY:
        return "falha"
    if final in SUCESSO_DEPLOY:
        return "sucesso"
    return None


def metricas_deploys(deploys: list[Deployment], semanas: float, minimo: int = 5) -> dict:
    producao = sorted((d for d in deploys if eh_producao(d.environment)), key=lambda d: d.created_at)
    resultados = [(d, resultado_deploy(d)) for d in producao]
    validos = [(d, r) for d, r in resultados if r is not None]
    falhas = sum(1 for _, r in validos if r == "falha")

    recuperacoes: list[float] = []
    por_ambiente: dict[str, list[tuple[Deployment, str]]] = {}
    for d, r in validos:
        por_ambiente.setdefault(d.environment, []).append((d, r))
    for lista in por_ambiente.values():
        inicio = None
        for d, r in lista:
            if r == "falha" and inicio is None:
                inicio = d.created_at
            elif r == "sucesso" and inicio is not None:
                recuperacoes.append(_horas(inicio, d.created_at))
                inicio = None

    coberto = len(producao) >= minimo
    return {
        "n_deploys_producao": len(producao),
        "usa_deployments": coberto,
        "df_deploy_semana": len(producao) / semanas if coberto and semanas else None,
        "cfr_d_deploy": falhas / len(validos) if coberto and validos else None,
        "recuperacao_deploy_mediana_horas": _mediana(recuperacoes) if coberto else None,
    }
