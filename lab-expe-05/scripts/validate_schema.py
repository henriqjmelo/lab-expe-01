"""Validador de esquema dos dados do Lab05 (contrato: docs/00-contrato.md, secao 3).

Vale para data/pilot.csv, data/full.csv, data/processed/clean.csv e data/sintetico.csv.

Uso:
    python scripts/validate_schema.py data/pilot.csv
    python scripts/validate_schema.py data/full.csv --n 30
    python scripts/validate_schema.py data/pilot.csv --base-dir data/raw/pilot

Saida: um problema por linha (CSV linha N, coluna, regra) e codigo de saida 1 se houver ERRO.
Avisos (por exemplo, mais de um digest de imagem no mesmo arquivo) nao reprovam.
Como biblioteca: `validar(df, n=None, base_dir=None)` devolve a lista de `Problema`.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

COLUNAS = [
    "run_id", "rep", "timestamp", "host", "jdk_version", "image_digest", "gc", "cpus",
    "heap_mult", "heap_mb", "benchmark", "iterations", "exec_ms", "lat_p99_ms",
    "gc_pause_max_ms", "cpu_s", "rss_peak_mb", "failed", "failure_reason", "seed",
    "raw_file", "gc_log_file",
]
OBRIGATORIAS = [
    "run_id", "rep", "timestamp", "host", "jdk_version", "image_digest", "gc", "cpus",
    "heap_mult", "heap_mb", "benchmark", "iterations", "failed", "seed", "raw_file", "gc_log_file",
]
# Obrigatorias so quando o run nao falhou (um OOM nao tem tempo nem CPU).
METRICAS = ["exec_ms", "gc_pause_max_ms", "cpu_s", "rss_peak_mb"]
COLETORES = {"G1", "ZGC"}

# Marcas que o log de GC (-Xlog:gc*) escreve na inicializacao.
_MARCA_G1 = re.compile(r"Using G1")
_MARCA_ZGC = re.compile(r"Z Garbage Collector|Using ZGC")


@dataclass(frozen=True)
class Problema:
    gravidade: str  # "erro" ou "aviso"
    regra: str
    mensagem: str
    linha: int | None = None  # numero da linha no CSV (cabecalho = 1)
    coluna: str | None = None

    def __str__(self) -> str:
        onde = f"linha {self.linha}" if self.linha else "arquivo"
        col = f", coluna {self.coluna}" if self.coluna else ""
        return f"[{self.gravidade}] {onde}{col}: {self.regra} - {self.mensagem}"


def _int(v: str) -> int | None:
    try:
        return int(v.strip())
    except ValueError:
        return None


def _num(v: str) -> float | None:
    try:
        x = float(v.strip().replace(",", "."))
    except ValueError:
        return None
    return x if x == x and abs(x) != float("inf") else None


def _data_iso_utc(v: str) -> bool:
    """ISO 8601 completo (data e hora) em UTC, com Z ou +00:00, como pede o contrato."""
    try:
        d = datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return d.tzinfo is not None and d.utcoffset().total_seconds() == 0 and "T" in v


def coletor_no_log(texto: str) -> str | None:
    """Coletor que o log de GC diz ter sido usado, ou None se nao der para saber."""
    g1, zgc = bool(_MARCA_G1.search(texto)), bool(_MARCA_ZGC.search(texto))
    if g1 and not zgc:
        return "G1"
    if zgc and not g1:
        return "ZGC"
    return None


def _checar_linha(i: int, r: dict[str, str], ps: list[Problema]) -> None:
    def erro(regra: str, msg: str, col: str | None = None) -> None:
        ps.append(Problema("erro", regra, msg, i, col))

    for c in OBRIGATORIAS:
        if r[c].strip() == "":
            erro("obrigatoria", "valor vazio", c)

    if r["gc"].strip() and r["gc"].strip() not in COLETORES:
        erro("dominio", f"gc deve ser G1 ou ZGC, veio {r['gc']!r}", "gc")
    if r["timestamp"].strip() and not _data_iso_utc(r["timestamp"]):
        erro("tipo", f"timestamp deve ser ISO 8601 em UTC (ex.: 2026-11-20T12:00:00Z), veio {r['timestamp']!r}", "timestamp")

    for c in ("rep", "cpus", "heap_mb", "iterations"):
        if r[c].strip():
            v = _int(r[c])
            if v is None or v < 1:
                erro("tipo", f"{c} deve ser inteiro >= 1, veio {r[c]!r}", c)
    if r["seed"].strip() and _int(r["seed"]) is None:
        erro("tipo", f"seed deve ser inteiro, veio {r['seed']!r}", "seed")
    if r["heap_mult"].strip():
        v = _num(r["heap_mult"])
        if v is None or v <= 0:
            erro("tipo", f"heap_mult deve ser decimal > 0, veio {r['heap_mult']!r}", "heap_mult")

    falhou = r["failed"].strip()
    if falhou and falhou not in {"0", "1"}:
        erro("dominio", f"failed deve ser 0 ou 1, veio {r['failed']!r}", "failed")
    for c in METRICAS:
        vazio = r[c].strip() == ""
        if vazio and falhou == "0":
            erro("obrigatoria", "metrica vazia num run que nao falhou", c)
        if not vazio:
            v = _num(r[c])
            minimo_ok = v is not None and (v > 0 if c == "exec_ms" else v >= 0)
            if not minimo_ok:
                erro("tipo", f"{c} invalida: {r[c]!r}", c)
    if r["lat_p99_ms"].strip():
        v = _num(r["lat_p99_ms"])
        if v is None or v < 0:
            erro("tipo", f"lat_p99_ms invalida: {r['lat_p99_ms']!r}", "lat_p99_ms")

    motivo = r["failure_reason"].strip()
    if falhou == "0" and motivo:
        erro("coerencia", "failure_reason preenchido num run que nao falhou", "failure_reason")
    if falhou == "1" and not motivo:
        erro("coerencia", "failed = 1 exige failure_reason", "failure_reason")


def validar(df: pd.DataFrame, n: int | None = None, base_dir: Path | None = None) -> list[Problema]:
    """Aplica as regras do contrato. `df` deve ter sido lido com dtype=str e sem NaN."""
    ps: list[Problema] = []
    faltam = [c for c in COLUNAS if c not in df.columns]
    sobram = [c for c in df.columns if c not in COLUNAS]
    if faltam:
        ps.append(Problema("erro", "colunas", f"faltam colunas: {', '.join(faltam)}"))
    if sobram:
        ps.append(Problema("erro", "colunas", f"colunas fora do contrato: {', '.join(sobram)}"))
    if faltam:
        return ps  # sem as colunas nao da para checar as linhas
    if df.empty:
        ps.append(Problema("erro", "vazio", "o arquivo nao tem nenhuma linha de dados"))
        return ps

    linhas = df.to_dict("records")
    for k, r in enumerate(linhas):
        _checar_linha(k + 2, r, ps)

    # run_id unico
    vistos: dict[str, int] = {}
    for k, r in enumerate(linhas):
        rid = r["run_id"].strip()
        if rid and rid in vistos:
            ps.append(Problema("erro", "duplicata", f"run_id repetido (primeira vez na linha {vistos[rid]})", k + 2, "run_id"))
        vistos.setdefault(rid, k + 2)

    # celulas (gc, heap_mult, benchmark): rep unico e, se pedido, N linhas
    celulas: dict[tuple, list[tuple[int, str]]] = defaultdict(list)
    for k, r in enumerate(linhas):
        celulas[(r["gc"].strip(), r["heap_mult"].strip(), r["benchmark"].strip())].append((k + 2, r["rep"].strip()))
    for chave, itens in celulas.items():
        reps = [rep for _, rep in itens]
        if n is not None:
            for linha_csv, rep in itens:
                if _int(rep) is not None and not 1 <= _int(rep) <= n:
                    ps.append(Problema("erro", "intervalo", f"rep {rep} fora de 1..{n}", linha_csv, "rep"))
        for rep in {x for x in reps if reps.count(x) > 1}:
            ps.append(Problema("erro", "duplicata", f"rep {rep} repetido na celula {chave}", itens[0][0], "rep"))
        if n is not None and len(itens) != n:
            ps.append(Problema("erro", "contagem", f"celula {chave} tem {len(itens)} linhas, esperado {n}"))

    # cada par (benchmark, heap_mult) precisa dos dois coletores
    pares: dict[tuple, set] = defaultdict(set)
    for (gc, heap, bench) in celulas:
        pares[(bench, heap)].add(gc)
    for (bench, heap), gcs in pares.items():
        if gcs != COLETORES:
            ps.append(Problema("erro", "pareamento", f"par benchmark={bench}, heap_mult={heap} so tem {sorted(gcs)}; faltam {sorted(COLETORES - gcs)}"))

    # p99 vazio so em benchmark sem metrica de latencia (todo vazio ou todo preenchido)
    lat: dict[str, set] = defaultdict(set)
    for r in linhas:
        if r["failed"].strip() != "1":
            lat[r["benchmark"].strip()].add(r["lat_p99_ms"].strip() != "")
    for bench, estados in lat.items():
        if estados == {True, False}:
            ps.append(Problema("erro", "latencia", f"benchmark {bench}: lat_p99_ms preenchida em algumas linhas e vazia em outras", coluna="lat_p99_ms"))

    # variaveis que deveriam ser unicas no arquivo
    for c in ("jdk_version", "image_digest"):
        valores = {r[c].strip() for r in linhas if r[c].strip()}
        if len(valores) > 1:
            ps.append(Problema("aviso", "controlada", f"{c} tem {len(valores)} valores no mesmo arquivo", coluna=c))

    # coletor registrado x log de GC (so se houver diretorio base)
    if base_dir is not None:
        for k, r in enumerate(linhas):
            for c in ("raw_file", "gc_log_file"):
                if r[c].strip() and not (base_dir / r[c].strip()).is_file():
                    ps.append(Problema("erro", "arquivo", f"{c} nao existe: {r[c]}", k + 2, c))
            caminho = base_dir / r["gc_log_file"].strip() if r["gc_log_file"].strip() else None
            if caminho and caminho.is_file() and r["gc"].strip() in COLETORES:
                visto = coletor_no_log(caminho.read_text(encoding="utf-8", errors="replace")[:20000])
                if visto is None:
                    ps.append(Problema("aviso", "log", f"nao deu para identificar o coletor no log {r['gc_log_file']}", k + 2, "gc_log_file"))
                elif visto != r["gc"].strip():
                    ps.append(Problema("erro", "log", f"linha diz {r['gc'].strip()} mas o log mostra {visto}", k + 2, "gc"))
    return ps


def ler_csv(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(caminho, dtype=str, keep_default_na=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Valida um CSV do Lab05 contra o contrato.")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--n", type=int, help="linhas esperadas por celula (coletor, heap, benchmark)")
    ap.add_argument("--base-dir", type=Path, help="pasta de onde raw_file e gc_log_file sao resolvidos")
    ap.add_argument("--max", type=int, default=50, help="maximo de problemas impressos")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        df = ler_csv(args.csv)
    except FileNotFoundError:
        print(f"[erro] arquivo nao encontrado: {args.csv}")
        return 2
    except pd.errors.EmptyDataError:
        print(f"[erro] arquivo vazio, sem cabecalho: {args.csv}")
        return 2
    ps = validar(df, n=args.n, base_dir=args.base_dir)
    erros = [p for p in ps if p.gravidade == "erro"]
    for p in ps[: args.max]:
        print(p)
    if len(ps) > args.max:
        print(f"... e mais {len(ps) - args.max} problema(s)")
    print(f"{len(erros)} erro(s), {len(ps) - len(erros)} aviso(s) em {args.csv}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
