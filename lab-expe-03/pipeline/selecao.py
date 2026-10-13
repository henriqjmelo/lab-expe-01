"""Selecao de repositorios e funil (secao 7 do ENUNCIADO.md), usada na coleta completa da #139.

1. Candidatos: GET /search/repositories, fatiado por faixa de estrelas porque
   cada consulta devolve no maximo 1.000 resultados.
2. Os candidatos sao embaralhados com semente fixa e avaliados nessa ordem ate
   a amostra atingir o alvo - assim a amostra nao fica so com os mais
   estrelados de cada faixa.
3. Filtros na ordem do mais barato pro mais caro: tem Actions? >= 5 releases
   na janela? >= 50 workflow runs validos na janela?

Cada descarte e registrado com o motivo; o funil sai dessas contagens.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date

from pipeline.github_client import GitHubAPIError, GitHubClient

MOTIVO_SEM_ACTIONS = "sem_actions"
MOTIVO_POUCAS_RELEASES = "menos_de_5_releases"
MOTIVO_POUCOS_RUNS = "menos_de_50_runs_validos"
MOTIVO_ERRO_API = "erro_api"

_LINK_LAST = "rel=\"last\""


ETAPAS = (
    ("com_actions", "actions/workflows com total_count = 0"),
    ("min_5_releases", "menos de 5 releases publicadas (sem pre-release) na janela"),
    ("min_50_runs", "menos de 50 workflow runs validos (push no default branch) na janela"),
    ("amostra_final", "falha ao calcular as metricas"),
)


@dataclass
class Funil:
    candidatos: int = 0
    avaliados: int = 0
    descartes: list[dict] = field(default_factory=list)
    aceitos: int = 0

    def descartar(self, candidato: dict, etapa: str, motivo: str, detalhe: str = "") -> None:
        self.descartes.append(
            {"full_name": candidato["full_name"], "etapa": etapa, "motivo": motivo, "detalhe": detalhe}
        )

    def linhas(self) -> list[dict]:
        linhas = [
            {"etapa": "candidatos_busca", "restantes": self.candidatos, "descartados": 0, "motivo": ""},
            {
                "etapa": "avaliados",
                "restantes": self.avaliados,
                "descartados": self.candidatos - self.avaliados,
                "motivo": "nao avaliados: alvo da amostra ja atingido",
            },
        ]
        restantes = self.avaliados
        for etapa, descricao in ETAPAS:
            da_etapa = [d for d in self.descartes if d["etapa"] == etapa]
            restantes -= len(da_etapa)
            erros = sum(1 for d in da_etapa if d["motivo"] == MOTIVO_ERRO_API)
            motivo = descricao + (f" (inclui {erros} por erro da API)" if erros else "")
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
    """Candidatos unicos de todas as faixas, com os campos que a selecao e o dataset usam."""
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
    """per_page=1 + numero da ultima pagina no Link = total de contribuidores (com anonimos)."""
    try:
        dados, headers = cliente.requisitar(
            f"repos/{owner}/{repo}/contributors", {"per_page": 1, "anon": "true"}
        )
    except GitHubAPIError:
        # Repositorios muito grandes respondem 403 "history or contributor list is too large".
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
    filtros: Callable[[dict], tuple[str | None, object]],
    ao_aceitar: Callable[[dict, object], bool],
    log: Callable[[str], None] = lambda _: None,
) -> None:
    """Percorre os candidatos ate `alvo` aceitos. `filtros(c)` devolve (motivo, contexto):
    motivo None = passou nos filtros; o contexto (dados ja coletados) segue para
    `ao_aceitar`, que calcula as metricas e devolve False se nao conseguiu (o
    descarte da etapa amostra_final fica por conta dela)."""
    funil.candidatos = len(candidatos)
    for candidato in candidatos:
        if funil.aceitos >= alvo:
            break
        funil.avaliados += 1
        motivo, contexto = filtros(candidato)
        if motivo is None:
            if ao_aceitar(candidato, contexto):
                funil.aceitos += 1
            else:
                motivo = "falha_metricas"
        log(
            f"[{funil.avaliados}/{funil.candidatos}] {candidato['full_name']}: "
            f"{motivo or 'aceito'} (amostra {funil.aceitos}/{alvo})"
        )

