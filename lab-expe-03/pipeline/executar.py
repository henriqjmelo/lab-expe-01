from __future__ import annotations

import csv
import http.client
import os
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
from pipeline.watchdog import Watchdog
from pipeline.repositorio import (
    UNIDADES,
    Janela,
    deploys_por_unidade,
    metricas_da_unidade,
    metricas_dos_runs,
)
from pipeline.selecao import (
    MOTIVO_ERRO_API,
    Avaliacao,
    MOTIVO_ERRO_INESPERADO,
    SemProgresso,
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
    threads: int = 1
    threads_runs: int = 1
    adiantar: int = 0
    watchdog_minutos: float = 10.0
    sem_progresso_minutos: float = 60.0
    excluir: tuple[Path, ...] = ()


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
        threads=int(bruto["coleta"].get("threads", 1)),
        threads_runs=int(bruto["coleta"].get("threads_runs", 1)),
        adiantar=int(bruto["coleta"].get("adiantar", 0)),
        watchdog_minutos=float(bruto["coleta"].get("watchdog_minutos", 10)),
        sem_progresso_minutos=float(bruto["coleta"].get("sem_progresso_minutos", 60)),
        excluir=tuple(base / c for c in bruto["amostra"].get("excluir") or []),
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


def repositorios_excluidos(caminhos: tuple[Path, ...]) -> set[str]:
    fora: set[str] = set()
    for caminho in caminhos:
        with caminho.open(newline="", encoding="utf-8") as f:
            fora.update(f"{l['owner']}/{l['repo']}".lower() for l in csv.DictReader(f))
    return fora


def idade_anos(criado_em: str, referencia: date) -> float:
    criado = date.fromisoformat(criado_em[:10])
    return round((referencia - criado).days / 365.25, 2)


class ColetaInterrompida(RuntimeError):
    pass


def erro_transitorio(erro: BaseException) -> bool:
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

    def avaliar(self, c: dict) -> Avaliacao:
        tentativas = self.config.retentativas_repositorio
        espera = self.config.espera_retentativa
        for tentativa in range(1, tentativas + 1):
            estado = {"etapa": "com_actions"}
            try:
                return self._avaliar(c, estado)
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
                        return Avaliacao(c, MOTIVO_ERRO_INESPERADO, estado["etapa"], repr(erro)[:200])
                self._dormir(espera)
                espera *= 2
        raise AssertionError("inalcancavel")

    def registrar(self, avaliacao: Avaliacao) -> None:
        self.linhas.append(avaliacao.linha)
        a_cada = self.config.gravar_parcial_a_cada
        if a_cada and len(self.linhas) % a_cada == 0:
            gravar_saidas(self)

    def _avaliar(self, c: dict, estado: dict) -> Avaliacao:
        cfg, janela = self.config, self.config.janela
        owner, repo = c["owner"], c["repo"]
        try:
            if not tem_actions(self.cliente, owner, repo):
                return Avaliacao(c, MOTIVO_SEM_ACTIONS, estado["etapa"])

            estado["etapa"] = "min_5_releases"
            releases = listar_releases(self.cliente, owner, repo)
            n_rel = sum(
                1
                for r in releases
                if not r.get("draft")
                and not r.get("prerelease")
                and na_janela(r.get("published_at"), janela.inicio_iso, janela.fim_iso)
            )
            if n_rel < cfg.min_releases:
                return Avaliacao(c, MOTIVO_POUCAS_RELEASES, estado["etapa"], str(n_rel))

            estado["etapa"] = "min_50_runs"
            runs = coletar_runs(
                self.cliente, owner, repo, c["default_branch"], janela.inicio, janela.fim, threads=cfg.threads_runs
            )
            validos = sum(1 for r in runs.runs if classificar_conclusao(r.conclusion) in (SUCESSO, FALHA))
            if validos < cfg.min_runs:
                return Avaliacao(c, MOTIVO_POUCOS_RUNS, estado["etapa"], str(validos))

            estado["etapa"] = "amostra_final"
            return Avaliacao(c, None, linha=self._linha(c, releases, runs))
        except GitHubAPIError as erro:
            if erro_transitorio(erro):
                raise
            return Avaliacao(c, MOTIVO_ERRO_API, estado["etapa"], str(erro)[:200])

    def _linha(self, c: dict, releases: list[dict], runs: Any) -> dict:
        owner, repo = c["owner"], c["repo"]
        janela = self.config.janela
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
                metricas_da_unidade(self.cliente, owner, repo, unidade, deploys, janela, self.config.max_compares)
            )
        linha.update(metricas_dos_runs(runs))
        return linha

    def rodar(self) -> None:
        cfg = self.config
        self.log(f"Buscando candidatos em {len(cfg.faixas)} faixas de estrelas...")
        candidatos = buscar_candidatos(self.cliente, cfg.faixas, cfg.janela.inicio)
        if cfg.excluir:
            fora = repositorios_excluidos(cfg.excluir)
            antes = len(candidatos)
            candidatos = [c for c in candidatos if c["full_name"].lower() not in fora]
            self.funil.excluidos = antes - len(candidatos)
            self.log(f"Excluidos {self.funil.excluidos} candidatos de amostras anteriores.")
        ordem = embaralhar(candidatos, cfg.semente)
        avaliar_candidatos(
            ordem,
            cfg.alvo,
            self.funil,
            self.avaliar,
            self.registrar,
            self.log,
            workers=cfg.threads,
            adiantar=cfg.adiantar or None,
            sem_progresso=cfg.sem_progresso_minutos * 60 if cfg.sem_progresso_minutos > 0 else None,
        )


def gravar_csv(caminho: Path, linhas: list[dict], campos: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    with temporario.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)
    temporario.replace(caminho)


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


SAIDA_OK = 0
SAIDA_TRANSITORIA = 75
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

    def travou(parado: float) -> None:
        log(f"Watchdog: nenhuma chamada concluida ha {parado / 60:.0f} min; encerrando para reiniciar.")
        os._exit(SAIDA_TRANSITORIA)

    if config.watchdog_minutos > 0:
        Watchdog(cliente, config.watchdog_minutos * 60, travou).iniciar()
    try:
        coleta.rodar()
    except KeyboardInterrupt:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        gravar_saidas(coleta)
        log("Interrompido. CSVs parciais gravados; o cache ficou salvo: rode o mesmo comando para continuar.")
        return SAIDA_INTERROMPIDA
    except SemProgresso as erro:
        gravar_saidas(coleta)
        log(f"Fila parada ({erro}). CSVs parciais gravados; encerrando para reiniciar.")
        sys.stderr.flush()
        os._exit(SAIDA_TRANSITORIA)
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
