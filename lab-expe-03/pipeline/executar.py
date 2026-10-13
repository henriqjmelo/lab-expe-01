"""Coleta completa: selecao + metricas de todos os repositorios + CSVs (issue #139).

Chamado por `python -m pipeline --config config.yaml`. Toda chamada a API passa
pelo cache em disco: interromper e rodar de novo retoma de onde parou, e uma
segunda execucao completa so le o cache (reproduz o dataset sem gastar cota).
"""

from __future__ import annotations

import csv
import http.client
import signal
import sys
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from metricas.cfr import FALHA, SUCESSO, classificar_conclusao
from metricas.frequencia import na_janela
from pipeline.cache import CacheDisco
from pipeline.coleta_releases import listar_releases
from pipeline.coleta_runs import coletar_runs
from pipeline.coleta_tags import listar_tags_graphql
from pipeline.github_client import GitHubAPIError, GitHubClient
from pipeline.repositorio import (
    UNIDADES,
    Janela,
    deploys_por_unidade,
    metricas_da_unidade,
    metricas_dos_runs,
)
from pipeline.selecao import (
    MOTIVO_ERRO_API,
    MOTIVO_ERRO_INESPERADO,
    MOTIVO_POUCAS_RELEASES,
    MOTIVO_POUCOS_RUNS,
    MOTIVO_SEM_ACTIONS,
    Funil,
    avaliar_candidatos,
    buscar_candidatos,
    contar_contribuidores,
    embaralhar,
    tem_actions,
)

CAMPOS_METADADOS = (
    "owner",
    "repo",
    "estrelas",
    "linguagem",
    "default_branch",
    "criado_em",
    "idade_anos",
    "contribuidores",
)


@dataclass
class Config:
    janela: Janela
    alvo: int
    semente: int
    faixas: list[tuple[int, int | None]]
    min_releases: int
    min_runs: int
    max_compares: int
    cache: Path
    saida: dict[str, Path]
    max_tentativas_chamada: int = 8
    retentativas_repositorio: int = 3
    espera_retentativa: float = 30.0
    gravar_parcial_a_cada: int = 10


def _data(valor: Any) -> date:
    return valor if isinstance(valor, date) else date.fromisoformat(str(valor))


def ler_config(caminho: Path) -> Config:
    bruto = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    base = caminho.resolve().parent
    faixas = [(int(f[0]), int(f[1]) if f[1] is not None else None) for f in bruto["busca"]["faixas_estrelas"]]
    return Config(
        janela=Janela(_data(bruto["janela"]["inicio"]), _data(bruto["janela"]["fim"])),
        alvo=int(bruto["amostra"]["alvo"]),
        semente=int(bruto["amostra"]["semente"]),
        faixas=faixas,
        min_releases=int(bruto["inclusao"]["min_releases"]),
        min_runs=int(bruto["inclusao"]["min_runs_validos"]),
        max_compares=int(bruto["coleta"]["max_compares_por_unidade"]),
        cache=base / bruto["coleta"]["cache"],
        saida={nome: base / rel for nome, rel in bruto["saida"].items()},
        max_tentativas_chamada=int(bruto["coleta"].get("max_tentativas_chamada", 8)),
        retentativas_repositorio=int(bruto["coleta"].get("retentativas_repositorio", 3)),
        espera_retentativa=float(bruto["coleta"].get("espera_retentativa_s", 30)),
        gravar_parcial_a_cada=int(bruto["coleta"].get("gravar_parcial_a_cada", 10)),
    )


def colunas_dataset() -> list[str]:
    colunas = list(CAMPOS_METADADOS)
    for u in UNIDADES:
        colunas += [
            f"n_{u}",
            f"df_{u}_semana",
            f"lt_a_{u}_dias",
            f"lt_b_{u}_dias",
            f"lt_{u}_n_avaliadas",
            f"lt_{u}_compare_404",
            f"lt_{u}_compare_grande",
            f"lt_{u}_omitido",
            f"cfr_b_{u}",
            f"cfr_b_{u}_n_avaliadas",
            f"cfr_b_{u}_n_censuradas",
            f"n_corretivas_{u}",
        ]
    colunas += [
        "n_runs_validos",
        "n_runs_sucesso",
        "n_runs_falha",
        "n_runs_ignorados",
        "cfr_a",
        "recuperacao_mediana_horas",
        "n_episodios",
        "n_episodios_censurados",
        "prop_episodios_censurados",
        "meses_no_teto_runs",
        "dias_truncados_runs",
    ]
    return colunas


def idade_anos(criado_em: str, referencia: date) -> float:
    criado = date.fromisoformat(criado_em[:10])
    return round((referencia - criado).days / 365.25, 2)


class ColetaInterrompida(RuntimeError):
    """Erro transitorio que nao passou nem com as retentativas: a coleta para sem
    descartar o repositorio, e a proxima execucao retoma dele pelo cache."""


def erro_transitorio(erro: BaseException) -> bool:
    """Erros que podem passar sozinhos (rede, 5xx, limite de taxa) - nunca viram descarte."""
    if isinstance(erro, GitHubAPIError):
        if erro.status == 0 or erro.status >= 500:
            return True
        return erro.status in (403, 429) and "rate limit" in str(erro).lower()
    return isinstance(erro, (http.client.HTTPException, OSError))


class Coleta:
    def __init__(
        self,
        cliente: GitHubClient,
        config: Config,
        log=print,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self.cliente = cliente
        self.config = config
        self.funil = Funil()
        self.linhas: list[dict] = []
        self.log = log
        self._dormir = dormir

    def _com_retentativas(self, c: dict, etapa_erro: str, funcao: Callable[[], Any], falha: Any) -> Any:
        """Roda `funcao` ate `retentativas_repositorio` vezes.

        - erro transitorio: espera (30 s, 60 s, 120 s...) e tenta de novo; se nao
          passar, levanta ColetaInterrompida (o repositorio NAO e descartado);
        - erro inesperado (dado estranho, bug): registra o traceback no log, tenta
          de novo e, se repetir, descarta com motivo erro_inesperado em vez de
          derrubar a coleta inteira.
        """
        tentativas = self.config.retentativas_repositorio
        espera = self.config.espera_retentativa
        for tentativa in range(1, tentativas + 1):
            try:
                return funcao()
            except Exception as erro:
                ultima = tentativa == tentativas
                if erro_transitorio(erro):
                    self.log(f"  {c['full_name']}: erro transitorio ({erro}); tentativa {tentativa}/{tentativas}")
                    if ultima:
                        raise ColetaInterrompida(f"{c['full_name']}: {erro}") from erro
                else:
                    self.log(f"  {c['full_name']}: erro inesperado; tentativa {tentativa}/{tentativas}")
                    self.log(traceback.format_exc())
                    if ultima:
                        self.funil.descartar(c, etapa_erro, MOTIVO_ERRO_INESPERADO, repr(erro)[:200])
                        return falha
                self._dormir(espera)
                espera *= 2
        return falha

    def filtros(self, c: dict) -> tuple[str | None, Any]:
        return self._com_retentativas(
            c, "com_actions", lambda: self._filtros(c), (MOTIVO_ERRO_INESPERADO, None)
        )

    def ao_aceitar(self, c: dict, contexto: Any) -> bool:
        ok = self._com_retentativas(c, "amostra_final", lambda: self._ao_aceitar(c, contexto), False)
        a_cada = self.config.gravar_parcial_a_cada
        if ok and a_cada and len(self.linhas) % a_cada == 0:
            gravar_saidas(self)
        return ok

    def _filtros(self, c: dict) -> tuple[str | None, Any]:
        cfg, janela = self.config, self.config.janela
        owner, repo = c["owner"], c["repo"]
        etapa = "com_actions"
        try:
            if not tem_actions(self.cliente, owner, repo):
                self.funil.descartar(c, etapa, MOTIVO_SEM_ACTIONS)
                return MOTIVO_SEM_ACTIONS, None

            etapa = "min_5_releases"
            releases = listar_releases(self.cliente, owner, repo)
            n_rel = sum(
                1
                for r in releases
                if not r.get("draft")
                and not r.get("prerelease")
                and na_janela(r.get("published_at"), janela.inicio_iso, janela.fim_iso)
            )
            if n_rel < cfg.min_releases:
                self.funil.descartar(c, etapa, MOTIVO_POUCAS_RELEASES, str(n_rel))
                return MOTIVO_POUCAS_RELEASES, None

            etapa = "min_50_runs"
            runs = coletar_runs(self.cliente, owner, repo, c["default_branch"], janela.inicio, janela.fim)
            validos = sum(1 for r in runs.runs if classificar_conclusao(r.conclusion) in (SUCESSO, FALHA))
            if validos < cfg.min_runs:
                self.funil.descartar(c, etapa, MOTIVO_POUCOS_RUNS, str(validos))
                return MOTIVO_POUCOS_RUNS, None
        except GitHubAPIError as erro:
            if erro_transitorio(erro):
                raise
            # Permanente (404 apagado, 451 bloqueado, 409 vazio...): descarta.
            self.funil.descartar(c, etapa, MOTIVO_ERRO_API, str(erro)[:200])
            return MOTIVO_ERRO_API, None
        return None, (releases, runs)

    def _ao_aceitar(self, c: dict, contexto: Any) -> bool:
        releases, runs = contexto
        owner, repo = c["owner"], c["repo"]
        janela = self.config.janela
        try:
            tags = listar_tags_graphql(self.cliente, owner, repo)
            linha = {
                "owner": owner,
                "repo": repo,
                "estrelas": c["estrelas"],
                "linguagem": c["linguagem"],
                "default_branch": c["default_branch"],
                "criado_em": c["criado_em"],
                "idade_anos": idade_anos(c["criado_em"], janela.fim),
                "contribuidores": contar_contribuidores(self.cliente, owner, repo),
            }
            for unidade, deploys in deploys_por_unidade(releases, tags).items():
                linha.update(
                    metricas_da_unidade(
                        self.cliente, owner, repo, unidade, deploys, janela, self.config.max_compares
                    )
                )
            linha.update(metricas_dos_runs(runs))
        except GitHubAPIError as erro:
            if erro_transitorio(erro):
                raise
            self.funil.descartar(c, "amostra_final", MOTIVO_ERRO_API, str(erro)[:200])
            return False
        self.linhas.append(linha)
        return True

    def rodar(self) -> None:
        cfg = self.config
        self.log(f"Buscando candidatos em {len(cfg.faixas)} faixas de estrelas...")
        candidatos = buscar_candidatos(self.cliente, cfg.faixas, cfg.janela.inicio)
        ordem = embaralhar(candidatos, cfg.semente)
        avaliar_candidatos(ordem, cfg.alvo, self.funil, self.filtros, self.ao_aceitar, self.log)


def gravar_csv(caminho: Path, linhas: list[dict], campos: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)


def gravar_saidas(coleta: Coleta) -> None:
    saida = coleta.config.saida
    linhas = sorted(coleta.linhas, key=lambda l: (l["owner"].lower(), l["repo"].lower()))
    gravar_csv(saida["dataset"], linhas, colunas_dataset())
    gravar_csv(saida["repositorios"], linhas, ["owner", "repo"])
    gravar_csv(saida["funil"], coleta.funil.linhas(), ["etapa", "restantes", "descartados", "motivo"])
    gravar_csv(
        saida["descartes"],
        sorted(coleta.funil.descartes, key=lambda d: d["full_name"].lower()),
        ["full_name", "etapa", "motivo", "detalhe"],
    )


# Codigos de saida lidos por scripts/coletar.sh.
SAIDA_OK = 0
SAIDA_TRANSITORIA = 75  # EX_TEMPFAIL: tentar de novo mais tarde
SAIDA_INTERROMPIDA = 130


def _sigterm_vira_interrupcao(signum, frame) -> None:
    raise KeyboardInterrupt


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="python -m pipeline", description="Coleta DORA do Lab03.")
    ap.add_argument("--config", type=Path, default=Path("config.yaml"))
    args = ap.parse_args(argv)

    config = ler_config(args.config)
    cache = CacheDisco(config.cache)
    cliente = GitHubClient(cache=cache, max_tentativas=config.max_tentativas_chamada)

    def log(mensagem: str) -> None:
        print(mensagem, file=sys.stderr, flush=True)

    signal.signal(signal.SIGTERM, _sigterm_vira_interrupcao)
    coleta = Coleta(cliente, config, log)
    try:
        coleta.rodar()
    except KeyboardInterrupt:
        gravar_saidas(coleta)
        log("Interrompido. CSVs parciais gravados; o cache ficou salvo: rode o mesmo comando para continuar.")
        return SAIDA_INTERROMPIDA
    except (ColetaInterrompida, GitHubAPIError, OSError, http.client.HTTPException) as erro:
        if isinstance(erro, GitHubAPIError) and not erro_transitorio(erro):
            raise
        gravar_saidas(coleta)
        log(f"Erro transitorio persistente ({erro}). CSVs parciais gravados; rode de novo para retomar.")
        return SAIDA_TRANSITORIA
    gravar_saidas(coleta)
    log(
        f"Amostra final: {coleta.funil.aceitos} repositorios -> {config.saida['dataset']} "
        f"(cache: {cache.acertos} acertos, {cache.faltas} chamadas novas)"
    )
    return SAIDA_OK
