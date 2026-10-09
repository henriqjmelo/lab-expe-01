"""Lead time for changes (RQ 02), variantes (a) por release e (b) por commit.

Issue #135, secao 3 do ENUNCIADO.md:
    (a) por release: data de publicacao de R - commit mais antigo de R;
        valor do repositorio = mediana entre releases.
    (b) por commit: data de publicacao de R - data de cada commit de R;
        valor do repositorio = mediana de todos os commits de todas as releases.

Estas funcoes so calculam: nao fazem chamada de rede. Quem monta a lista de
ReleaseComCommits e o pipeline/coleta_releases.py, a partir da API do GitHub.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReleaseComCommits:
    """Uma release publicada e as datas dos commits incluidos desde a anterior.

    ignorada=True cobre os dois casos que o enunciado tira do calculo: a
    primeira release da historia do repositorio (sem release anterior para
    comparar) e uma comparacao que devolveu 404 (tag apagada ou reescrita).
    """

    tag_name: str
    published_at: str
    commits_datas: list[str] = field(default_factory=list)
    ignorada: bool = False


def _parse(data: str) -> datetime:
    # API do GitHub devolve ISO 8601 com sufixo "Z" (UTC).
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def lead_time_por_release(releases: list[ReleaseComCommits]) -> dict:
    """Variante (a). Pula releases ignoradas e releases sem commit novo (nao ha
    'commit mais antigo' para comparar nesse caso), mas conta as duas coisas."""
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
    """Variante (b): um valor por commit, nao um por release."""
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
