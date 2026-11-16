"""Leitura, validacao e regra de exclusao.

O pipeline nunca inventa nome de coluna: tudo vem do contrato, atraves do
validador que o papel A escreveu (scripts/validate_schema.py). Se o arquivo
nao bate com o contrato, a analise para aqui em vez de produzir numero errado.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import validate_schema as contrato  # noqa: E402

NUMERICAS = ["exec_ms", "lat_p99_ms", "gc_pause_max_ms", "cpu_s", "rss_peak_mb"]
INTEIRAS = ["rep", "cpus", "heap_mb", "iterations", "failed", "seed"]
METRICAS_CONFIRMATORIAS = ["exec_ms", "lat_p99_ms"]
METRICAS_EXPLORATORIAS = ["gc_pause_max_ms", "cpu_s", "rss_peak_mb"]
# Motivos aceitos pela regra de exclusao (plano de analise, secao 10).
MOTIVOS_DE_EXCLUSAO = {"oom", "validacao_benchmark", "erro_container", "interrupcao_so"}


class DadosInvalidos(RuntimeError):
    """O CSV nao cumpre o contrato."""


def carregar(caminho: Path, n: int | None = None) -> pd.DataFrame:
    """Le o CSV, valida contra o contrato e converte os tipos."""
    bruto = contrato.ler_csv(Path(caminho))
    problemas = contrato.validar(bruto, n=n)
    erros = [p for p in problemas if p.gravidade == "erro"]
    if erros:
        detalhe = "\n".join(str(p) for p in erros[:20])
        raise DadosInvalidos(f"{len(erros)} erro(s) de contrato em {caminho}:\n{detalhe}")

    df = bruto.copy()
    for c in NUMERICAS:
        df[c] = pd.to_numeric(df[c].replace("", pd.NA), errors="coerce")
    for c in INTEIRAS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    df["heap_mult"] = pd.to_numeric(df["heap_mult"], errors="coerce")
    return df


def aplicar_exclusao(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa o que entra na analise do que foi excluido.

    A regra esta escrita no plano antes dos dados: exclui-se se e somente se
    `failed` = 1. Nunca por valor extremo - o outlier de latencia e justamente
    o que este experimento quer medir.
    """
    falhas = df[df["failed"] == 1].copy()
    desconhecidos = set(falhas["failure_reason"].dropna()) - MOTIVOS_DE_EXCLUSAO
    if desconhecidos:
        raise DadosInvalidos(
            f"motivo de falha fora do plano de analise: {sorted(desconhecidos)}. "
            f"Aceitos: {sorted(MOTIVOS_DE_EXCLUSAO)}"
        )
    return df[df["failed"] == 0].copy(), falhas


def metricas_presentes(df: pd.DataFrame, metricas: list[str]) -> list[str]:
    """Metricas que de fato tem valor neste arquivo (p99 so existe em alguns benchmarks)."""
    return [m for m in metricas if df[m].notna().any()]


def benchmarks_com_latencia(df: pd.DataFrame) -> list[str]:
    com = df.groupby("benchmark")["lat_p99_ms"].apply(lambda s: s.notna().any())
    return sorted(com[com].index)


def pares(df: pd.DataFrame, metrica: str) -> list[tuple[str, float]]:
    """Pares (benchmark, heap_mult) em que a metrica existe. Cada par = 1 teste."""
    com_valor = df[df[metrica].notna()]
    chaves = com_valor[["benchmark", "heap_mult"]].drop_duplicates()
    return sorted((str(r.benchmark), float(r.heap_mult)) for r in chaves.itertuples())
