from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from datetime import date

from metricas.cfr import Deploy, cfr_ci, cfr_entrega
from metricas.frequencia import frequencia_semanal, na_janela
from metricas.lead_time import ReleaseComCommits, lead_time_por_commit, lead_time_por_release
from metricas.recuperacao import tempo_recuperacao
from pipeline.coleta_runs import ResultadoRuns
from pipeline.github_client import GitHubAPIError, GitHubClient

UNIDADES = ("release", "release_pre", "tag")

COMMITS_POR_PAGINA = 100
MAX_COMMITS_COMPARE = 1000

TRUNCADO = "truncado"


@dataclass
class Janela:
    inicio: date
    fim: date

    @property
    def inicio_iso(self) -> str:
        return f"{self.inicio.isoformat()}T00:00:00Z"

    @property
    def fim_iso(self) -> str:
        return f"{date.fromordinal(self.fim.toordinal() + 1).isoformat()}T00:00:00Z"


def deploys_por_unidade(releases: list[dict], tags: list[dict]) -> dict[str, list[Deploy]]:
    publicadas = sorted(
        (r for r in releases if not r.get("draft") and r.get("published_at")),
        key=lambda r: r["published_at"],
    )
    return {
        "release": [Deploy(r["tag_name"], r["published_at"]) for r in publicadas if not r.get("prerelease")],
        "release_pre": [Deploy(r["tag_name"], r["published_at"]) for r in publicadas],
        "tag": [Deploy(t["name"], t["data"]) for t in tags],
    }


def comparar(
    cliente: GitHubClient, owner: str, repo: str, base: str, head: str, max_commits: int = MAX_COMMITS_COMPARE
) -> list[str] | None | str:
    caminho = f"repos/{owner}/{repo}/compare/{base}...{head}"
    datas: list[str] = []
    pagina = 1
    while True:
        try:
            resultado = cliente.get(caminho, {"per_page": COMMITS_POR_PAGINA, "page": pagina})
        except GitHubAPIError as erro:
            if erro.status == 404:
                return None
            if erro.status == 422 and "too long" in str(erro).lower():
                return TRUNCADO
            raise
        if pagina == 1 and (resultado.get("total_commits") or 0) > max_commits:
            return TRUNCADO
        commits = resultado.get("commits") or []
        datas.extend(c["commit"]["author"]["date"] for c in commits)
        if len(commits) < COMMITS_POR_PAGINA:
            return datas
        pagina += 1


def montar_com_commits(
    cliente: GitHubClient,
    owner: str,
    repo: str,
    deploys: list[Deploy],
    janela: Janela,
) -> tuple[list[ReleaseComCommits], int, int]:
    montadas: list[ReleaseComCommits] = []
    n_404 = n_truncados = 0
    for i, deploy in enumerate(deploys):
        if not na_janela(deploy.published_at, janela.inicio_iso, janela.fim_iso):
            continue
        if i == 0:
            montadas.append(ReleaseComCommits(deploy.tag_name, deploy.published_at, ignorada=True))
            continue
        base = urllib.parse.quote(deploys[i - 1].tag_name, safe="/")
        head = urllib.parse.quote(deploy.tag_name, safe="/")
        datas = comparar(cliente, owner, repo, base, head)
        if datas is None or datas == TRUNCADO:
            n_404 += datas is None
            n_truncados += datas == TRUNCADO
            montadas.append(ReleaseComCommits(deploy.tag_name, deploy.published_at, ignorada=True))
        else:
            montadas.append(ReleaseComCommits(deploy.tag_name, deploy.published_at, datas))
    return montadas, n_404, n_truncados


def metricas_da_unidade(
    cliente: GitHubClient,
    owner: str,
    repo: str,
    unidade: str,
    deploys: list[Deploy],
    janela: Janela,
    max_compares: int,
) -> dict:
    ini, fim = janela.inicio_iso, janela.fim_iso
    n_janela = sum(1 for d in deploys if na_janela(d.published_at, ini, fim))
    linha = {
        f"n_{unidade}": n_janela,
        f"df_{unidade}_semana": frequencia_semanal([d.published_at for d in deploys], ini, fim),
    }

    if n_janela > max_compares:
        linha.update({
            f"lt_a_{unidade}_dias": None,
            f"lt_b_{unidade}_dias": None,
            f"lt_{unidade}_n_avaliadas": 0,
            f"lt_{unidade}_compare_404": 0,
            f"lt_{unidade}_compare_grande": 0,
            f"lt_{unidade}_omitido": True,
        })
    else:
        montadas, n_404, n_grandes = montar_com_commits(cliente, owner, repo, deploys, janela)
        a = lead_time_por_release(montadas)
        b = lead_time_por_commit(montadas)
        linha.update({
            f"lt_a_{unidade}_dias": a["mediana_dias"],
            f"lt_b_{unidade}_dias": b["mediana_dias"],
            f"lt_{unidade}_n_avaliadas": a["n_releases"],
            f"lt_{unidade}_compare_404": n_404,
            f"lt_{unidade}_compare_grande": n_grandes,
            f"lt_{unidade}_omitido": False,
        })

    cfr = cfr_entrega(deploys, ini, fim)
    linha.update({
        f"cfr_b_{unidade}": cfr["cfr"],
        f"cfr_b_{unidade}_n_avaliadas": cfr["n_avaliadas"],
        f"cfr_b_{unidade}_n_censuradas": cfr["n_censuradas"],
        f"n_corretivas_{unidade}": cfr["n_corretivas"],
    })
    return linha


def metricas_dos_runs(resultado: ResultadoRuns) -> dict:
    ci = cfr_ci([r.conclusion for r in resultado.runs])
    rec = tempo_recuperacao(resultado.runs)
    return {
        "n_runs_validos": ci["n_validos"],
        "n_runs_sucesso": ci["n_sucessos"],
        "n_runs_falha": ci["n_falhas"],
        "n_runs_ignorados": ci["n_ignorados"],
        "cfr_a": ci["cfr"],
        "recuperacao_mediana_horas": rec["mediana_horas"],
        "n_episodios": rec["n_episodios"],
        "n_episodios_censurados": rec["n_censurados"],
        "prop_episodios_censurados": rec["prop_censurados"],
        "meses_no_teto_runs": resultado.meses_no_teto,
        "dias_truncados_runs": resultado.dias_truncados,
    }
