from __future__ import annotations

import random
from collections import deque
from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date

from pipeline.github_client import GitHubAPIError, GitHubClient

MOTIVO_SEM_ACTIONS = "sem_actions"
MOTIVO_POUCAS_RELEASES = "menos_de_5_releases"
MOTIVO_POUCOS_RUNS = "menos_de_50_runs_validos"
MOTIVO_ERRO_API = "erro_api"
MOTIVO_ERRO_INESPERADO = "erro_inesperado"

_LINK_LAST = "rel=\"last\""


@dataclass
class Avaliacao:

    candidato: dict
    motivo: str | None
    etapa: str | None = None
    detalhe: str = ""
    linha: dict | None = None


ETAPAS = (
    ("com_actions", "actions/workflows com total_count = 0"),
    ("min_5_releases", "menos de 5 releases publicadas (sem pre-release) na janela"),
    ("min_50_runs", "menos de 50 workflow runs validos (push no default branch) na janela"),
    ("amostra_final", "falha ao calcular as metricas"),
)


@dataclass
class Funil:
    candidatos: int = 0
    excluidos: int = 0
    avaliados: int = 0
    descartes: list[dict] = field(default_factory=list)
    aceitos: int = 0

    def descartar(self, candidato: dict, etapa: str, motivo: str, detalhe: str = "") -> None:
        self.descartes.append(
            {"full_name": candidato["full_name"], "etapa": etapa, "motivo": motivo, "detalhe": detalhe}
        )

    def linhas(self) -> list[dict]:
        linhas = [
            {"etapa": "candidatos_busca", "restantes": self.candidatos + self.excluidos, "descartados": 0, "motivo": ""},
            {
                "etapa": "avaliados",
                "restantes": self.avaliados,
                "descartados": self.candidatos - self.avaliados,
                "motivo": "nao avaliados: alvo da amostra ja atingido",
            },
        ]
        if self.excluidos:
            linhas.insert(1, {
                "etapa": "fora_de_amostra_anterior",
                "restantes": self.candidatos,
                "descartados": self.excluidos,
                "motivo": "ja estavam numa amostra anterior (amostras independentes)",
            })
        restantes = self.avaliados
        for etapa, descricao in ETAPAS:
            da_etapa = [d for d in self.descartes if d["etapa"] == etapa]
            restantes -= len(da_etapa)
            erros = sum(1 for d in da_etapa if d["motivo"] == MOTIVO_ERRO_API)
            inesperados = sum(1 for d in da_etapa if d["motivo"] == MOTIVO_ERRO_INESPERADO)
            notas = [f"{erros} por erro da API"] if erros else []
            notas += [f"{inesperados} por erro inesperado"] if inesperados else []
            motivo = descricao + (f" (inclui {'; '.join(notas)})" if notas else "")
            linhas.append(
                {"etapa": etapa, "restantes": restantes, "descartados": len(da_etapa), "motivo": motivo}
            )
        return linhas


def consulta_busca(faixa: tuple[int, int | None], ativo_desde: date) -> str:
    minimo, maximo = faixa
    estrelas = f"stars:{minimo}..{maximo}" if maximo else f"stars:>={minimo}"
    return f"{estrelas} archived:false pushed:>={ativo_desde.isoformat()}"


def buscar_candidatos(
    cliente: GitHubClient, faixas: Iterable[tuple[int, int | None]], ativo_desde: date
) -> list[dict]:
    vistos: dict[str, dict] = {}
    for faixa in faixas:
        params = {"q": consulta_busca(faixa, ativo_desde), "sort": "stars", "order": "desc"}
        for item in cliente.paginar("search/repositories", params, chave="items"):
            vistos.setdefault(item["full_name"], {
                "full_name": item["full_name"],
                "owner": item["owner"]["login"],
                "repo": item["name"],
                "estrelas": item["stargazers_count"],
                "linguagem": item.get("language") or "",
                "default_branch": item["default_branch"],
                "criado_em": item["created_at"],
            })
    return sorted(vistos.values(), key=lambda c: c["full_name"])


def embaralhar(candidatos: list[dict], semente: int) -> list[dict]:
    ordem = list(candidatos)
    random.Random(semente).shuffle(ordem)
    return ordem


def tem_actions(cliente: GitHubClient, owner: str, repo: str) -> bool:
    dados = cliente.get(f"repos/{owner}/{repo}/actions/workflows", {"per_page": 1})
    return (dados or {}).get("total_count", 0) > 0


def contar_contribuidores(cliente: GitHubClient, owner: str, repo: str) -> int | None:
    try:
        dados, headers = cliente.requisitar(
            f"repos/{owner}/{repo}/contributors", {"per_page": 1, "anon": "true"}
        )
    except GitHubAPIError:
        return None
    link = headers.get("Link") or ""
    for parte in link.split(","):
        if _LINK_LAST in parte:
            url = parte.split(";")[0].strip(" <>")
            for par in url.split("?", 1)[-1].split("&"):
                chave, _, valor = par.partition("=")
                if chave == "page":
                    return int(valor)
    return len(dados or [])


def avaliar_candidatos(
    candidatos: list[dict],
    alvo: int,
    funil: Funil,
    avaliar: Callable[[dict], Avaliacao],
    registrar: Callable[[Avaliacao], None],
    log: Callable[[str], None] = lambda _: None,
    workers: int = 1,
    adiantar: int | None = None,
) -> None:
    funil.candidatos = len(candidatos)
    fila = iter(candidatos)
    em_voo: deque[tuple[dict, Future]] = deque()
    adiantar = adiantar or max(1, workers) * 2
    executor = ThreadPoolExecutor(max_workers=max(1, workers), thread_name_prefix="coleta")

    def encher() -> None:
        while len(em_voo) < adiantar:
            candidato = next(fila, None)
            if candidato is None:
                return
            em_voo.append((candidato, executor.submit(avaliar, candidato)))

    try:
        encher()
        while em_voo and funil.aceitos < alvo:
            candidato, futuro = em_voo.popleft()
            avaliacao = futuro.result()
            funil.avaliados += 1
            if avaliacao.motivo is None:
                funil.aceitos += 1
                registrar(avaliacao)
            else:
                funil.descartar(candidato, avaliacao.etapa, avaliacao.motivo, avaliacao.detalhe)
            log(
                f"[{funil.avaliados}/{funil.candidatos}] {candidato['full_name']}: "
                f"{avaliacao.motivo or 'aceito'} (amostra {funil.aceitos}/{alvo})"
            )
            if funil.aceitos < alvo:
                encher()
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
