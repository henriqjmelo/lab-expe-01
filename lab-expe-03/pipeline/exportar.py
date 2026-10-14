from __future__ import annotations

import argparse
import csv
import gzip
import io
import os
import re
import statistics
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

from metricas.cfr import FALHA, SUCESSO, classificar_conclusao
from metricas.frequencia import na_janela
from pipeline.cache import CacheDisco
from pipeline.coleta_releases import listar_releases
from pipeline.coleta_runs import coletar_runs
from pipeline.executar import ler_config
from pipeline.github_client import GitHubAPIError, GitHubClient
from pipeline.repositorio import COMMITS_POR_PAGINA, MAX_COMMITS_COMPARE, deploys_por_unidade, montar_com_commits
from pipeline.selecao import buscar_candidatos

CAMPOS_CANDIDATOS = ("full_name", "owner", "repo", "estrelas", "linguagem", "default_branch", "criado_em")
CAMPOS_RELEASES = ("owner", "repo", "tag_name", "published_at", "prerelease", "na_janela")
CAMPOS_LEAD_TIME = (
    "owner", "repo", "tag_name", "published_at", "n_commits", "lt_a_dias", "lt_b_mediana_dias", "ignorada",
)
CAMPOS_COMMITS = ("owner", "repo", "tag_name", "sha", "data", "mensagem", "reverte_sha")

_REVERTE = re.compile(r"This reverts commit ([0-9a-f]{7,40})")
CAMPOS_RUNS = (
    "owner", "repo", "workflow_id", "conclusion", "classe", "run_started_at", "updated_at", "run_attempt", "head_sha",
)


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def _gravar(caminho: Path, linhas: list[dict], campos: tuple[str, ...]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.suffix == ".gz":
        with open(caminho, "wb") as bruto, gzip.GzipFile(filename="", fileobj=bruto, mode="wb", mtime=0) as comprimido, \
                io.TextIOWrapper(comprimido, encoding="utf-8", newline="") as f:
            _escrever(f, linhas, campos)
    else:
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            _escrever(f, linhas, campos)


def _escrever(f, linhas: list[dict], campos: tuple[str, ...]) -> None:
    w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
    w.writeheader()
    w.writerows(linhas)


def linhas_lead_time(owner: str, repo: str, montadas) -> list[dict]:
    linhas = []
    for r in montadas:
        dias = [(_parse(r.published_at) - _parse(d)).total_seconds() / 86400 for d in r.commits_datas]
        linhas.append({
            "owner": owner,
            "repo": repo,
            "tag_name": r.tag_name,
            "published_at": r.published_at,
            "n_commits": len(r.commits_datas),
            "lt_a_dias": max(dias) if dias and not r.ignorada else None,
            "lt_b_mediana_dias": statistics.median(dias) if dias and not r.ignorada else None,
            "ignorada": r.ignorada,
        })
    return linhas


def commits_do_compare(cliente: GitHubClient, owner: str, repo: str, base: str, head: str) -> list[dict]:
    caminho = f"repos/{owner}/{repo}/compare/{urllib.parse.quote(base, safe='/')}...{urllib.parse.quote(head, safe='/')}"
    commits: list[dict] = []
    pagina = 1
    while True:
        try:
            resultado = cliente.get(caminho, {"per_page": COMMITS_POR_PAGINA, "page": pagina})
        except GitHubAPIError:
            return []
        if pagina == 1 and (resultado.get("total_commits") or 0) > MAX_COMMITS_COMPARE:
            return []
        lote = resultado.get("commits") or []
        commits.extend(lote)
        if len(lote) < COMMITS_POR_PAGINA:
            return commits
        pagina += 1


def linhas_commits(owner: str, repo: str, tag_name: str, commits: list[dict]) -> list[dict]:
    return [
        {
            "owner": owner,
            "repo": repo,
            "tag_name": tag_name,
            "sha": c["sha"],
            "data": c["commit"]["author"]["date"],
            "mensagem": (c["commit"]["message"] or "").splitlines()[0][:300] if c["commit"]["message"] else "",
            "reverte_sha": ";".join(_REVERTE.findall(c["commit"]["message"] or "")),
        }
        for c in commits
    ]


def exportar(caminho_config: Path, destino: Path, candidatos_csv: Path | None, log=print) -> None:
    config = ler_config(caminho_config)
    cliente = GitHubClient(os.environ.get("GITHUB_TOKEN", "sem-token"), cache=CacheDisco(config.cache))
    janela = config.janela

    if candidatos_csv is not None:
        candidatos = buscar_candidatos(cliente, config.faixas, janela.inicio)
        _gravar(candidatos_csv, candidatos, CAMPOS_CANDIDATOS)
        log(f"{len(candidatos)} candidatos")

    with config.saida["dataset"].open(newline="", encoding="utf-8") as f:
        repos = [(l["owner"], l["repo"], l["default_branch"]) for l in csv.DictReader(f)]

    releases, lead_time, commits, runs = [], [], [], []
    for i, (owner, repo, branch) in enumerate(repos, start=1):
        brutas = listar_releases(cliente, owner, repo)
        for r in brutas:
            if r.get("draft") or not r.get("published_at"):
                continue
            releases.append({
                "owner": owner, "repo": repo, "tag_name": r["tag_name"], "published_at": r["published_at"],
                "prerelease": bool(r.get("prerelease")),
                "na_janela": na_janela(r["published_at"], janela.inicio_iso, janela.fim_iso),
            })
        deploys = deploys_por_unidade(brutas, [])["release"]
        n_janela = sum(1 for d in deploys if na_janela(d.published_at, janela.inicio_iso, janela.fim_iso))
        if n_janela <= config.max_compares:
            montadas, _, _ = montar_com_commits(cliente, owner, repo, deploys, janela)
            lead_time.extend(linhas_lead_time(owner, repo, montadas))
            for k, d in enumerate(deploys):
                if k == 0 or not na_janela(d.published_at, janela.inicio_iso, janela.fim_iso):
                    continue
                lote = commits_do_compare(cliente, owner, repo, deploys[k - 1].tag_name, d.tag_name)
                commits.extend(linhas_commits(owner, repo, d.tag_name, lote))
        resultado = coletar_runs(cliente, owner, repo, branch, janela.inicio, janela.fim)
        for run in resultado.runs:
            classe = classificar_conclusao(run.conclusion)
            runs.append({
                "owner": owner, "repo": repo, "workflow_id": run.workflow_id, "conclusion": run.conclusion or "",
                "classe": classe if classe in (SUCESSO, FALHA) else "ignorado",
                "run_started_at": run.run_started_at, "updated_at": run.updated_at,
                "run_attempt": run.run_attempt, "head_sha": run.head_sha,
            })
        log(f"[{i}/{len(repos)}] {owner}/{repo}")

    _gravar(destino / "releases.csv", releases, CAMPOS_RELEASES)
    _gravar(destino / "lead_time_releases.csv", lead_time, CAMPOS_LEAD_TIME)
    _gravar(destino / "commits_releases.csv.gz", commits, CAMPOS_COMMITS)
    _gravar(destino / "runs.csv.gz", runs, CAMPOS_RUNS)
    log(f"{len(releases)} releases, {len(lead_time)} releases com lead time, {len(commits)} commits, "
        f"{len(runs)} runs -> {destino}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pipeline.exportar",
                                 description="Exporta do cache os eventos por repositorio de uma amostra.")
    ap.add_argument("--config", type=Path, default=Path("config.yaml"))
    ap.add_argument("--saida", type=Path, default=Path("data/eventos"))
    ap.add_argument("--candidatos", type=Path, help="grava tambem os metadados de todos os candidatos da busca")
    args = ap.parse_args(argv)
    exportar(args.config, args.saida, args.candidatos, log=lambda m: print(m, file=sys.stderr, flush=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
