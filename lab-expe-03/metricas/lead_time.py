from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReleaseComCommits:

    tag_name: str
    published_at: str
    commits_datas: list[str] = field(default_factory=list)
    ignorada: bool = False


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def lead_time_por_release(releases: list[ReleaseComCommits]) -> dict:
    validas = [r for r in releases if not r.ignorada]
    sem_commits_novos = sum(1 for r in validas if not r.commits_datas)
    dias = [
        (_parse(r.published_at) - min(_parse(d) for d in r.commits_datas)).total_seconds() / 86400
        for r in validas
        if r.commits_datas
    ]
    return {
        "n_releases": len(dias),
        "mediana_dias": statistics.median(dias) if dias else None,
        "releases_sem_commits_novos": sem_commits_novos,
        "releases_ignoradas": sum(1 for r in releases if r.ignorada),
    }


def lead_time_por_commit(releases: list[ReleaseComCommits]) -> dict:
    dias = [
        (_parse(r.published_at) - _parse(d)).total_seconds() / 86400
        for r in releases
        if not r.ignorada
        for d in r.commits_datas
    ]
    return {
        "n_commits": len(dias),
        "mediana_dias": statistics.median(dias) if dias else None,
    }
