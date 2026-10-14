from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

HORIZONTE_REVERT = timedelta(days=30)


@dataclass
class CommitDeRelease:
    sha: str
    tag_name: str
    reverte: list[str] = field(default_factory=list)


@dataclass
class ReleaseAvaliavel:
    tag_name: str
    published_at: str
    avaliavel: bool = True


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def _release_do_sha(alvo: str, sha_para_tag: dict[str, str]) -> str | None:
    if alvo in sha_para_tag:
        return sha_para_tag[alvo]
    if len(alvo) < 7:
        return None
    for sha, tag in sha_para_tag.items():
        if sha.startswith(alvo):
            return tag
    return None


def releases_revertidas(
    releases: list[ReleaseAvaliavel],
    commits: list[CommitDeRelease],
    horizonte: timedelta = HORIZONTE_REVERT,
) -> dict[str, timedelta]:
    publicacao = {r.tag_name: _parse(r.published_at) for r in releases}
    sha_para_tag = {c.sha: c.tag_name for c in commits}
    revertidas: dict[str, timedelta] = {}
    for commit in commits:
        for alvo in commit.reverte:
            tag_original = _release_do_sha(alvo, sha_para_tag)
            if tag_original is None or tag_original == commit.tag_name:
                continue
            atraso = publicacao[commit.tag_name] - publicacao[tag_original]
            if timedelta(0) < atraso <= horizonte:
                revertidas[tag_original] = min(atraso, revertidas.get(tag_original, atraso))
    return revertidas


def cfr_revert(
    releases: list[ReleaseAvaliavel],
    commits: list[CommitDeRelease],
    fim: str,
    horizonte: timedelta = HORIZONTE_REVERT,
) -> dict:
    revertidas = releases_revertidas(releases, commits, horizonte)
    limite = _parse(fim) - horizonte
    avaliadas = falharam = censuradas = 0
    for release in releases:
        if not release.avaliavel:
            continue
        if _parse(release.published_at) >= limite:
            censuradas += 1
            continue
        avaliadas += 1
        falharam += release.tag_name in revertidas
    return {
        "n_avaliadas": avaliadas,
        "n_revertidas": falharam,
        "n_censuradas": censuradas,
        "cfr": falharam / avaliadas if avaliadas else None,
    }
