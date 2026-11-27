#!/usr/bin/env python3
"""Gera clean.csv a partir de um CSV válido, sem modificar dados brutos.

Por padrão, falhas registradas são excluídas do conjunto analítico. A saída só
é criada se o desenho continuar balanceado (16 células e N observações/célula).
Use --allow-unbalanced apenas para diagnóstico exploratório, nunca para a
análise confirmatória pré-registrada.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONFIG = ROOT / "env" / "benchmarks.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_schema as schema  # noqa: E402


def project_path(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def expected_cells() -> set[tuple[str, float, str]]:
    import json

    with CONFIG.open(encoding="utf-8") as stream:
        config = json.load(stream)
    return {
        (gc, float(heap), benchmark["name"])
        for benchmark in config["benchmarks"]
        for heap in config["heap_multipliers"]
        for gc in ("G1", "ZGC")
    }


def clean_frame(
    frame: pd.DataFrame,
    *,
    base_dir: Path | None = None,
    expected_n: int | None = None,
    allow_unbalanced: bool = False,
) -> tuple[pd.DataFrame, int, list[schema.Problema]]:
    if expected_n is not None and expected_n < 1:
        raise ValueError("N esperado deve ser inteiro positivo")

    problems = schema.validar(frame, base_dir=base_dir)
    errors = [problem for problem in problems if problem.gravidade == "erro"]
    if errors:
        summary = "; ".join(str(problem) for problem in errors[:8])
        raise ValueError(f"CSV de entrada não passou no contrato: {summary}")

    failed = frame["failed"].astype(str).str.strip() == "1"
    clean = frame.loc[~failed, schema.COLUNAS].copy().reset_index(drop=True)
    if clean.empty:
        raise ValueError("não há runs bem-sucedidos para análise")

    observed: dict[tuple[str, float, str], int] = {}
    for (gc, heap, benchmark), group in clean.groupby(["gc", "heap_mult", "benchmark"], dropna=False):
        try:
            key = (str(gc).strip(), float(str(heap).replace(",", ".")), str(benchmark).strip())
        except ValueError as exc:
            raise ValueError(f"chave de célula inválida: {(gc, heap, benchmark)!r}") from exc
        observed[key] = len(group)

    required = expected_cells()
    unexpected = set(observed) - required
    missing = required - set(observed)
    if unexpected:
        raise ValueError(f"CSV contém células fora de env/benchmarks.json: {sorted(unexpected)}")
    if not allow_unbalanced:
        if missing:
            raise ValueError(f"faltam {len(missing)} células depois de excluir falhas: {sorted(missing)}")
        counts = set(observed.values())
        if len(counts) != 1:
            raise ValueError(f"número de runs bem-sucedidos não balanceado entre células: {sorted(counts)}")
        if expected_n is not None and counts != {expected_n}:
            raise ValueError(
                f"cada célula precisa de N={expected_n} runs bem-sucedidos; encontrados {sorted(counts)}"
            )
    elif expected_n is not None and any(count > expected_n for count in observed.values()):
        raise ValueError(f"há células com mais runs que N={expected_n}")

    return clean, int(failed.sum()), [problem for problem in problems if problem.gravidade == "aviso"]


def write_csv_atomic(frame: pd.DataFrame, output: Path, *, force: bool = False) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not force:
        raise FileExistsError(f"saída já existe; use --force para substituir apenas o derivado: {output}")
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", encoding="utf-8", dir=output.parent,
            prefix=f".{output.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temp_name = stream.name
            frame.to_csv(stream, index=False, columns=schema.COLUNAS)
            stream.flush()
            os.fsync(stream.fileno())
        if output.exists() and not force:
            raise FileExistsError(f"saída surgiu durante a gravação; não substituída: {output}")
        os.replace(temp_name, output)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida e deriva um CSV analítico do Lab05")
    parser.add_argument("input", nargs="?", type=Path, default=DATA / "full.csv")
    parser.add_argument("--output", type=Path, default=DATA / "processed" / "clean.csv")
    parser.add_argument("--base-dir", type=Path, default=DATA / "raw")
    parser.add_argument("--n", type=int, help="N esperado de runs bem-sucedidos por célula")
    parser.add_argument(
        "--allow-unbalanced", action="store_true",
        help="permite derivado incompleto apenas para diagnóstico exploratório",
    )
    parser.add_argument("--force", action="store_true", help="substitui somente o arquivo derivado de saída")
    args = parser.parse_args(argv)

    source = project_path(args.input)
    output = project_path(args.output)
    base_dir = project_path(args.base_dir)
    try:
        if source == output:
            raise ValueError("entrada e saída não podem ser o mesmo arquivo")
        processed_dir = (DATA / "processed").resolve()
        if not output.is_relative_to(processed_dir):
            raise ValueError(f"a saída deve ficar sob {processed_dir}; arquivos brutos são somente leitura")
        frame = schema.ler_csv(source)
        clean, excluded, warnings = clean_frame(
            frame,
            base_dir=base_dir,
            expected_n=args.n,
            allow_unbalanced=args.allow_unbalanced,
        )
        for warning in warnings:
            print(warning, file=sys.stderr)
        write_csv_atomic(clean, output, force=args.force)
    except (OSError, ValueError, pd.errors.EmptyDataError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    print(
        f"CSV limpo gravado: {output}; linhas mantidas={len(clean)}; "
        f"falhas excluídas={excluded}; modo={'exploratório não balanceado' if args.allow_unbalanced else 'balanceado'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
