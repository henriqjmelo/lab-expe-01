from __future__ import annotations

import argparse
import csv
import gzip
import io
import os
import re
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.cache import CacheDisco
from pipeline.executar import ler_config
from pipeline.github_client import GitHubAPIError, GitHubClient
from pipeline.repositorio import Janela

TAMANHOS_PAGINA = (100, 50, 25)
MAX_PAGINAS = 50
MAX_PAGINAS_DEPLOYMENTS = 20

_BUG = re.compile(r"(^|[^a-z])(bug|defect|regression)([^a-z]|$)", re.IGNORECASE)

CONSULTA_PRS = """
query($owner: String!, $name: String!, $base: String!, $estados: [PullRequestState!], $n: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: $estados, baseRefName: $base, first: $n, after: $cursor,
                 orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number createdAt updatedAt mergedAt closedAt
        author { login }
        reviews(first: 2) { nodes { createdAt author { login } } }
        comments(first: 3) { nodes { createdAt author { login } } }
      }
    }
  }
}
"""

CONSULTA_ISSUES = """
query($owner: String!, $name: String!, $n: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(states: CLOSED, first: $n, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes { number createdAt updatedAt closedAt labels(first: 10) { nodes { name } } }
    }
  }
}
"""

CONSULTA_DEPLOYMENTS = """
query($owner: String!, $name: String!, $n: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    deployments(first: $n, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { createdAt environment state latestStatus { state createdAt } }
    }
  }
}
"""

CAMPOS_PRS = ("owner", "repo", "number", "estado", "created_at", "merged_at", "closed_at", "primeira_resposta_at")
CAMPOS_ISSUES = ("owner", "repo", "number", "created_at", "closed_at", "labels", "eh_bug")
CAMPOS_DEPLOYMENTS = ("owner", "repo", "created_at", "environment", "state", "status", "status_at")
CAMPOS_RESUMO = (
    "owner", "repo", "prs_mergeados", "prs_fechados", "issues_fechadas", "issues_bug", "deployments",
    "deployments_total", "truncado_prs", "truncado_issues", "truncado_deployments",
)


class ErroGraphQL(RuntimeError):
    pass


@dataclass
class Conexao:
    nos: list[dict] = field(default_factory=list)
    truncado: bool = False
    total: int | None = None


def _conexao(resposta: Any, caminho: tuple[str, ...]) -> dict | None:
    if not isinstance(resposta, dict):
        raise ErroGraphQL("resposta vazia")
    if resposta.get("errors") and not resposta.get("data"):
        raise ErroGraphQL(str(resposta["errors"])[:300])
    no = resposta.get("data") or {}
    for chave in caminho:
        if no is None:
            return None
        no = no.get(chave)
    return no


def paginar_graphql(
    cliente: Any,
    consulta: str,
    variaveis: dict,
    caminho: tuple[str, ...],
    parar: Callable[[dict], bool],
    max_paginas: int = MAX_PAGINAS,
) -> Conexao:
    resultado = Conexao()
    cursor = None
    for _ in range(max_paginas):
        pagina = None
        for tamanho in TAMANHOS_PAGINA:
            try:
                resposta = cliente.graphql(consulta, {**variaveis, "n": tamanho, "cursor": cursor})
                pagina = _conexao(resposta, caminho)
                break
            except (ErroGraphQL, GitHubAPIError) as erro:
                if isinstance(erro, GitHubAPIError) and erro.status not in (0, 502, 503, 504):
                    raise
                if tamanho == TAMANHOS_PAGINA[-1]:
                    raise
        if pagina is None:
            return resultado
        if resultado.total is None and "totalCount" in pagina:
            resultado.total = pagina["totalCount"]
        for no in pagina.get("nodes") or []:
            if parar(no):
                return resultado
            resultado.nos.append(no)
        if not pagina["pageInfo"]["hasNextPage"]:
            return resultado
        cursor = pagina["pageInfo"]["endCursor"]
    resultado.truncado = True
    return resultado


def primeira_resposta(pr: dict) -> str | None:
    autor = (pr.get("author") or {}).get("login")
    datas = [
        n["createdAt"]
        for conexao in ("reviews", "comments")
        for n in ((pr.get(conexao) or {}).get("nodes") or [])
        if (n.get("author") or {}).get("login") not in (autor, None)
    ]
    return min(datas) if datas else None


def eh_bug(labels: list[str]) -> bool:
    return any(_BUG.search(nome) for nome in labels)


def coletar_repositorio(cliente: Any, owner: str, repo: str, branch: str, janela: Janela) -> dict:
    ini, fim = janela.inicio_iso, janela.fim_iso
    base = {"owner": owner, "name": repo}
    fora = lambda no, campo: no[campo] < ini  # noqa: E731

    prs, truncado_prs = [], False
    for estado in ("MERGED", "CLOSED"):
        conexao = paginar_graphql(
            cliente, CONSULTA_PRS, {**base, "base": branch, "estados": [estado]},
            ("repository", "pullRequests"), lambda no: fora(no, "updatedAt"),
        )
        truncado_prs |= conexao.truncado
        campo = "mergedAt" if estado == "MERGED" else "closedAt"
        for no in conexao.nos:
            if no.get(campo) and ini <= no[campo] < fim:
                prs.append({
                    "owner": owner, "repo": repo, "number": no["number"], "estado": estado.lower(),
                    "created_at": no["createdAt"], "merged_at": no.get("mergedAt") or "",
                    "closed_at": no.get("closedAt") or "",
                    "primeira_resposta_at": primeira_resposta(no) or "",
                })

    conexao = paginar_graphql(cliente, CONSULTA_ISSUES, base, ("repository", "issues"),
                              lambda no: fora(no, "updatedAt"))
    issues = []
    for no in conexao.nos:
        if no.get("closedAt") and ini <= no["closedAt"] < fim:
            labels = [l["name"] for l in (no.get("labels") or {}).get("nodes") or []]
            issues.append({
                "owner": owner, "repo": repo, "number": no["number"], "created_at": no["createdAt"],
                "closed_at": no["closedAt"], "labels": ";".join(labels), "eh_bug": eh_bug(labels),
            })
    truncado_issues = conexao.truncado

    conexao = paginar_graphql(cliente, CONSULTA_DEPLOYMENTS, base, ("repository", "deployments"),
                              lambda no: fora(no, "createdAt"), max_paginas=MAX_PAGINAS_DEPLOYMENTS)
    deployments = [
        {
            "owner": owner, "repo": repo, "created_at": no["createdAt"], "environment": no.get("environment") or "",
            "state": no.get("state") or "", "status": (no.get("latestStatus") or {}).get("state") or "",
            "status_at": (no.get("latestStatus") or {}).get("createdAt") or "",
        }
        for no in conexao.nos
        if no["createdAt"] < fim
    ]
    resumo = {
        "owner": owner, "repo": repo,
        "prs_mergeados": sum(1 for p in prs if p["estado"] == "merged"),
        "prs_fechados": sum(1 for p in prs if p["estado"] == "closed"),
        "issues_fechadas": len(issues), "issues_bug": sum(1 for i in issues if i["eh_bug"]),
        "deployments": len(deployments), "deployments_total": conexao.total or 0,
        "truncado_prs": truncado_prs, "truncado_issues": truncado_issues, "truncado_deployments": conexao.truncado,
    }
    return {"prs": prs, "issues": issues, "deployments": deployments, "resumo": resumo}


def _gravar(caminho: Path, linhas: list[dict], campos: tuple[str, ...]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.suffix == ".gz":
        with open(caminho, "wb") as bruto, gzip.GzipFile(filename="", fileobj=bruto, mode="wb", mtime=0) as comp, \
                io.TextIOWrapper(comp, encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            w.writeheader()
            w.writerows(linhas)
    else:
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            w.writeheader()
            w.writerows(linhas)


def coletar_amostra(caminho_config: Path, destino: Path, threads: int = 3, log=print) -> None:
    config = ler_config(caminho_config)
    cliente = GitHubClient(cache=CacheDisco(config.cache), max_tentativas=config.max_tentativas_chamada, registrar=log)
    with config.saida["dataset"].open(newline="", encoding="utf-8") as f:
        repos = [(l["owner"], l["repo"], l["default_branch"]) for l in csv.DictReader(f)]

    def um(item: tuple[str, str, str]) -> dict:
        return coletar_repositorio(cliente, *item, config.janela)

    resultados: list[dict] = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for i, resultado in enumerate(executor.map(um, repos), start=1):
            resultados.append(resultado)
            r = resultado["resumo"]
            log(f"[{i}/{len(repos)}] {r['owner']}/{r['repo']}: {r['prs_mergeados']} PRs, "
                f"{r['issues_bug']} bugs, {r['deployments']} deployments")

    _gravar(destino / "prs.csv.gz", [l for r in resultados for l in r["prs"]], CAMPOS_PRS)
    _gravar(destino / "issues.csv.gz", [l for r in resultados for l in r["issues"]], CAMPOS_ISSUES)
    _gravar(destino / "deployments.csv.gz", [l for r in resultados for l in r["deployments"]], CAMPOS_DEPLOYMENTS)
    _gravar(destino / "resumo.csv", [r["resumo"] for r in resultados], CAMPOS_RESUMO)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pipeline.coleta_graphql",
                                 description="Coleta PRs, issues e deployments via GraphQL para uma amostra.")
    ap.add_argument("--config", type=Path, default=Path("config.yaml"))
    ap.add_argument("--saida", type=Path, default=Path("data/graphql"))
    ap.add_argument("--threads", type=int, default=3)
    args = ap.parse_args(argv)
    coletar_amostra(args.config, args.saida, args.threads, log=lambda m: print(m, file=sys.stderr, flush=True))
    return 0


if __name__ == "__main__":
    codigo = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(codigo)
