#!/usr/bin/env python3
"""Coleta DaCapo em blocos; nenhum run acontece sem --execute.

A configuração e a interface CSV seguem docs/00-contrato.md. O script não
calcula nem cria resultados: sem o JAR e os mínimos de heap medidos no alvo,
--execute falha antes de iniciar qualquer benchmark.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "env" / "benchmarks.json"
DOCKERFILE = ROOT / "env" / "Dockerfile"
COMPOSE = ROOT / "env" / "compose.yaml"
FLAGS_DIFF = ROOT / "env" / "flags.diff"
ARTIFACTS = ROOT / "env" / "artifacts"
DATA = ROOT / "data"
VALIDATOR = ROOT / "scripts" / "validate_schema.py"
CSV_COLUMNS = [
    "run_id", "rep", "timestamp", "host", "jdk_version", "image_digest", "gc", "cpus",
    "heap_mult", "heap_mb", "benchmark", "iterations", "exec_ms", "lat_p99_ms",
    "gc_pause_max_ms", "cpu_s", "rss_peak_mb", "failed", "failure_reason", "seed",
    "raw_file", "gc_log_file",
]


def load_config(path: Path = CONFIG) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def make_cells(config: dict[str, Any]) -> list[dict[str, Any]]:
    cells = []
    for benchmark in config["benchmarks"]:
        for heap_mult in config["heap_multipliers"]:
            for gc in ("G1", "ZGC"):
                cells.append({
                    "benchmark": benchmark["name"],
                    "gc": gc,
                    "heap_mult": float(heap_mult),
                })
    return cells


def order_block(cells: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    ordered = [dict(cell) for cell in cells]
    random.Random(seed).shuffle(ordered)
    return ordered


def run_id(mode: str, rep: int, cell: dict[str, Any]) -> str:
    return f"{mode}-b{rep:02d}-{cell['gc']}-h{cell['heap_mult']:g}-{cell['benchmark']}"


def parse_exec_ms(output: str, benchmark: str) -> float | None:
    pat = re.compile(
        rf"(?m)^===== DaCapo [^\r\n]*\s{re.escape(benchmark)}\s+PASSED in "
        r"([0-9]+(?:\.[0-9]+)?) msec\s+=====$"
    )
    matches = pat.findall(output)
    return float(matches[-1]) if len(matches) == 1 else None


def count_warmups(output: str, benchmark: str) -> list[int]:
    pat = re.compile(
        rf"(?m)^===== DaCapo [^\r\n]*\s{re.escape(benchmark)}\s+completed warmup "
        r"([0-9]+)\s+=====$"
    )
    return [int(n) for n in pat.findall(output)]


def parse_simple_p99_ms(output: str) -> float | None:
    pat = re.compile(
        r"tail latency,\s*simple:[^\r\n]*?\b99%\s+([0-9]+(?:\.[0-9]+)?)\s+usec",
        re.IGNORECASE,
    )
    values = pat.findall(output)
    return float(values[-1]) / 1000.0 if values else None


def parse_gc_pause_max_ms(output: str) -> float:
    pauses: list[float] = []
    for line in output.splitlines():
        # O prefixo do Unified Logging inclui [uptime]s; somente durações após
        # o evento Pause são pausas de GC e devem entrar nesta métrica.
        match = re.search(r"\bPause\b[^\r\n]*?\b([0-9]+(?:\.[0-9]+)?)(ms|s)\b", line)
        if match:
            value, unit = match.groups()
            pauses.append(float(value) * (1000.0 if unit == "s" else 1.0))
    return max(pauses, default=0.0)


def parse_marker(output: str, key: str) -> str | None:
    values = re.findall(rf"(?m)^__LAB05_{re.escape(key)}__=([^\r\n]*)$", output)
    return values[-1].strip() if values else None


def parse_jdk_version(output: str) -> str:
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^(?:openjdk|java) version ", line, re.IGNORECASE):
            return "\n".join(lines[i : i + 3]).strip()
    return ""


def parse_jdk_major(output: str) -> int | None:
    match = re.search(r'(?m)^(?:openjdk|java) version "([0-9]+)(?:\.|")', output, re.IGNORECASE)
    return int(match.group(1)) if match else None


def collector_from_log(text: str) -> str | None:
    g1 = bool(re.search(r"Using G1", text))
    zgc = bool(re.search(r"Z Garbage Collector|Using ZGC", text))
    if g1 != zgc:
        return "G1" if g1 else "ZGC"
    return None


def append_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="raise")
        if new_file:
            writer.writeheader()
        writer.writerow(row)
        f.flush()
        os.fsync(f.fileno())


def load_existing(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != CSV_COLUMNS:
            raise ValueError(f"Cabeçalho incompatível em {path}; esperado o contrato do Lab05")
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            rid = row.get("run_id", "")
            if not rid or rid in rows:
                raise ValueError(f"run_id vazio ou duplicado em {path}: {rid!r}")
            rows[rid] = row
        return rows


def image_digest() -> str:
    text = DOCKERFILE.read_text(encoding="utf-8")
    match = re.search(r"@(?P<digest>sha256:[0-9a-f]{64})", text)
    if not match:
        raise ValueError("Não encontrei digest SHA-256 pinado em env/Dockerfile")
    return match.group("digest")


def docker_image_name() -> str:
    text = COMPOSE.read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*image:\s*([^\s#]+)", text)
    if not match:
        raise ValueError("Não encontrei o nome da imagem local em env/compose.yaml")
    return match.group(1)


def discover_jar(pattern: str) -> Path:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    jars = sorted(ARTIFACTS.glob(pattern))
    if len(jars) != 1:
        raise ValueError(
            f"Esperava exatamente um JAR em {ARTIFACTS} que correspondesse a {pattern!r}; "
            f"encontrei {len(jars)}. Extraia e identifique a distribuição oficial antes da coleta."
        )
    return jars[0]


def parse_memory_mb(value: str) -> int:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([kmg])\s*", value, re.IGNORECASE)
    if not match:
        raise ValueError(f"memory_limit não entendido: {value!r}; use, por exemplo, 6g")
    scale = {"k": 1 / 1024, "m": 1, "g": 1024}[match.group(2).lower()]
    return int(float(match.group(1)) * scale)


def heap_minima(config: dict[str, Any]) -> dict[str, int]:
    minima: dict[str, int] = {}
    missing = []
    for item in config["benchmarks"]:
        value = item.get("min_heap_mb")
        if type(value) is not int or value <= 0:
            missing.append(item["name"])
        else:
            minima[item["name"]] = value
    if missing:
        raise ValueError(
            "min_heap_mb ainda não foi medido e aprovado no ambiente-alvo para: "
            + ", ".join(missing)
            + ". Atualize env/benchmarks.json após os probes; os valores históricos não servem como substitutos."
        )
    return minima


def flags_diff_ready(text: str) -> bool:
    if not text.strip() or re.search(r"(?im)^\s*(?:#\s*)?(?:TODO|PENDING|PENDENTE)\b", text):
        return False
    return any(
        line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        for line in text.splitlines()
    )


def run_preflight(config: dict[str, Any], jar: Path, env: dict[str, str]) -> None:
    docker = shutil.which("docker")
    if not docker:
        raise ValueError("Docker CLI não encontrado")
    if not VALIDATOR.exists():
        raise ValueError(f"Validador ausente: {VALIDATOR}")
    help_result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--help"], cwd=ROOT, capture_output=True, text=True
    )
    if help_result.returncode != 0:
        raise ValueError("Pré-voo do validador falhou; instale as dependências fixadas em requirements.txt")
    compose = subprocess.run(
        [docker, "compose", "-f", str(COMPOSE.relative_to(ROOT)), "config"],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    if compose.returncode != 0:
        raise ValueError(f"docker compose config falhou:\n{compose.stderr}")
    info = subprocess.run([docker, "info", "--format", "{{.OSType}}"], cwd=ROOT, capture_output=True, text=True)
    if info.returncode != 0 or info.stdout.strip() != "linux":
        raise ValueError("Daemon Docker indisponível ou sem runtime Linux; nenhum run foi iniciado")
    image = docker_image_name()
    inspected = subprocess.run([docker, "image", "inspect", image], cwd=ROOT, capture_output=True, text=True)
    if inspected.returncode != 0:
        raise ValueError(f"Imagem local {image!r} não existe; construa e valide-a conforme env/README.md")
    flags = FLAGS_DIFF.read_text(encoding="utf-8", errors="replace") if FLAGS_DIFF.exists() else ""
    if not flags_diff_ready(flags):
        raise ValueError("env/flags.diff ainda não contém mudanças reais para revisão")
    if not jar.is_file() or jar.stat().st_size == 0:
        raise ValueError("JAR DaCapo ausente ou vazio")


def make_row(
    mode: str, rep: int, seed: int, cell: dict[str, Any], heap_mb: int, cpus: int,
    digest: str, output: str, gc_text: str, run_dir: Path, exit_code: int | None,
    iterations: int, host: str,
) -> dict[str, Any]:
    benchmark = cell["benchmark"]
    exec_ms = parse_exec_ms(output, benchmark)
    warmups = count_warmups(output, benchmark)
    p99_ms = parse_simple_p99_ms(output) if benchmark in {"cassandra", "spring"} else None
    cpu_raw = parse_marker(output, "CPU_S")
    rss_raw = parse_marker(output, "RSS_KB")
    cpu_s = float(cpu_raw) if cpu_raw and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", cpu_raw) else None
    rss_kb = int(rss_raw) if rss_raw and rss_raw.isdigit() else None
    pause_max = parse_gc_pause_max_ms(gc_text)
    jdk = parse_jdk_version(output)
    jdk_major = parse_jdk_major(output)
    observed_gc = collector_from_log(gc_text)
    reasons: list[str] = []
    java_status = parse_marker(output, "JAVA_EXIT_CODE")
    if java_status is None:
        reasons.append("marcador de saída Java ausente")
    else:
        try:
            java_exit_code = int(java_status)
        except ValueError:
            reasons.append("marcador de saída Java inválido")
        else:
            if java_exit_code != 0:
                if "OutOfMemoryError" in output:
                    reasons.append("OutOfMemoryError")
                elif java_exit_code == 137:
                    reasons.append("Java terminou com código 137; possível OOM, confirmar no daemon")
                else:
                    reasons.append(f"processo Java terminou com código {java_exit_code}")
    if exit_code not in (0, None):
        if "OutOfMemoryError" in output:
            if "OutOfMemoryError" not in "; ".join(reasons):
                reasons.append("OutOfMemoryError")
        elif exit_code == 137:
            reasons.append("contêiner terminou com código 137; possível OOM, confirmar no daemon")
        else:
            reasons.append(f"docker compose terminou com código {exit_code}")
    if not jdk:
        reasons.append("java -version ausente na saída")
    elif jdk_major != 25:
        reasons.append(f"esperado OpenJDK 25, versão principal encontrada: {jdk_major}")
    if warmups != list(range(1, iterations)):
        reasons.append(f"esperados {iterations - 1} aquecimentos numerados, encontrados {warmups}")
    if exec_ms is None:
        reasons.append("linha DaCapo PASSED da iteração cronometrada ausente ou ambígua")
    if benchmark in {"cassandra", "spring"} and p99_ms is None:
        reasons.append("p99 simple ausente para workload de latência")
    if cpu_s is None or rss_kb is None:
        reasons.append("medidas user+sys ou VmHWM do processo Java ausentes")
    if not gc_text.strip():
        reasons.append("log de GC ausente ou vazio")
    elif observed_gc != cell["gc"]:
        reasons.append(f"log de GC indica {observed_gc or 'coletor indeterminado'}, esperado {cell['gc']}")

    failed = bool(reasons)
    raw_rel = (Path(mode) / run_dir.name / "stdout.txt").as_posix()
    gc_rel = (Path(mode) / run_dir.name / "gc.log").as_posix()
    row: dict[str, Any] = {
        "run_id": run_id(mode, rep, cell),
        "rep": rep,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "host": host,
        "jdk_version": jdk,
        "image_digest": digest,
        "gc": cell["gc"],
        "cpus": cpus,
        "heap_mult": f"{cell['heap_mult']:.1f}",
        "heap_mb": heap_mb,
        "benchmark": benchmark,
        "iterations": iterations,
        "exec_ms": "" if failed else f"{exec_ms:.6f}",
        "lat_p99_ms": "" if failed or p99_ms is None else f"{p99_ms:.6f}",
        "gc_pause_max_ms": "" if failed else f"{pause_max:.6f}",
        "cpu_s": "" if failed else f"{cpu_s:.6f}",
        "rss_peak_mb": "" if failed else f"{rss_kb / 1024:.6f}",
        "failed": int(failed),
        "failure_reason": "; ".join(reasons),
        "seed": seed,
        "raw_file": raw_rel,
        "gc_log_file": gc_rel,
    }
    return row


def validate_csv(path: Path, expected_n: int | None = None) -> int:
    cmd = [sys.executable, str(VALIDATOR), str(path), "--base-dir", str(DATA / "raw")]
    if expected_n is not None:
        cmd.extend(["--n", str(expected_n)])
    return subprocess.run(cmd, cwd=ROOT).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coleta retomável DaCapo→CSV do Lab05")
    parser.add_argument("--mode", choices=("pilot", "full"), default="pilot")
    parser.add_argument("--blocks", type=int, help="sobrescreve o padrão de blocos do arquivo de configuração")
    parser.add_argument("--seed", type=int, default=20261127, help="semente-base da ordem (seed do bloco = base + rep - 1)")
    parser.add_argument("--cooldown-seconds", type=int, help="sobrescreve o intervalo fixo entre invocações")
    parser.add_argument("--execute", action="store_true", help="autoriza execução; sem esta opção, apenas lista o plano")
    args = parser.parse_args(argv)

    try:
        config = load_config()
        suite = config["suite"]
        total_blocks = args.blocks if args.blocks is not None else int(config["blocks"][args.mode])
        cooldown = args.cooldown_seconds if args.cooldown_seconds is not None else int(suite["cooldown_seconds"])
        if total_blocks < 1 or cooldown < 0:
            raise ValueError("blocos precisa ser >= 1 e cooldown >= 0")
        cells = make_cells(config)
        if len(cells) != 16:
            raise ValueError(f"O contrato exige 16 células, mas a configuração gerou {len(cells)}")
        if len({(c["benchmark"], c["heap_mult"], c["gc"]) for c in cells}) != 16:
            raise ValueError("A configuração contém células duplicadas; revise benchmarks e multiplicadores de heap")
        seeds = {rep: args.seed + rep - 1 for rep in range(1, total_blocks + 1)}
        total = total_blocks * len(cells)
        print(f"Modo={args.mode}; blocos={total_blocks}; células/bloco={len(cells)}; runs={total}; iterações={suite['iterations']}")
        print(f"Benchmarks={', '.join(b['name'] for b in config['benchmarks'])}; heaps={config['heap_multipliers']} × mínimo alvo; cooldown={cooldown}s")
        print("Nenhum run será iniciado sem --execute.")
        if not args.execute:
            for rep, seed in seeds.items():
                for cell in order_block(cells, seed):
                    print(f"rep={rep:02d} seed={seed} {cell['gc']} {cell['benchmark']} heap={cell['heap_mult']:g}×M")
            return 0

        minima = heap_minima(config)
        jar = discover_jar(suite["jar_glob"])
        memory_limit = os.environ.get("LAB05_MEM_LIMIT", config["container"]["memory_limit"])
        memory_mb = parse_memory_mb(memory_limit)
        cpus_raw = os.environ.get("LAB05_CPUS", str(config["container"]["cpus"]))
        cpus_value = float(cpus_raw)
        if cpus_value <= 0 or not cpus_value.is_integer():
            raise ValueError("LAB05_CPUS deve ser inteiro positivo, em acordo com a coluna cpus do contrato")
        cpus = int(cpus_value)
        compose_env = os.environ.copy()
        compose_env["LAB05_CPUS"] = str(cpus)
        compose_env["LAB05_MEM_LIMIT"] = memory_limit
        compose_env.setdefault("LAB05_PLATFORM", config["container"]["platform"])
        for cell in cells:
            heap_mb = round(minima[cell["benchmark"]] * cell["heap_mult"])
            if heap_mb >= memory_mb:
                raise ValueError(f"heap {heap_mb} MiB não cabe no limite do contêiner {memory_limit}")
        run_preflight(config, jar, compose_env)

        csv_path = DATA / ("pilot.csv" if args.mode == "pilot" else "full.csv")
        existing = load_existing(csv_path)
        planned_cells = {
            run_id(args.mode, rep, cell): (rep, cell)
            for rep in range(1, total_blocks + 1)
            for cell in cells
        }
        planned_ids = set(planned_cells)
        for rid, row in existing.items():
            planned = planned_cells.get(rid)
            if planned is None:
                try:
                    old_rep = int(row.get("rep", ""))
                except ValueError as exc:
                    raise ValueError(f"CSV existente tem rep inválida em {rid}") from exc
                if old_rep > total_blocks:
                    raise ValueError(
                        f"CSV existente já contém rep={old_rep}, maior que --blocks={total_blocks}; "
                        "aumente --blocks para cobrir os blocos já gravados"
                    )
                raise ValueError(f"CSV existente não corresponde à configuração atual: {rid}")
            expected_rep, expected_cell = planned
            try:
                old_heap_mult = float(row.get("heap_mult", ""))
                old_rep = int(row.get("rep", ""))
            except ValueError as exc:
                raise ValueError(f"CSV existente tem rep/heap_mult inválidos em {rid}") from exc
            if (
                old_rep != expected_rep
                or row.get("gc") != expected_cell["gc"]
                or row.get("benchmark") != expected_cell["benchmark"]
                or old_heap_mult != expected_cell["heap_mult"]
            ):
                raise ValueError(f"CSV existente não corresponde à configuração atual: {rid}")
        digest = image_digest()
        jar_rel = jar.relative_to(ARTIFACTS).as_posix()
        compose = shutil.which("docker") or "docker"
        completed = 0
        for rep, seed in seeds.items():
            block_ordered = order_block(cells, seed)
            for cell in block_ordered:
                rid = run_id(args.mode, rep, cell)
                if rid in existing:
                    completed += 1
                    continue
                heap_mb = round(minima[cell["benchmark"]] * cell["heap_mult"])
                run_dir = DATA / "raw" / args.mode / rid
                run_dir.mkdir(parents=True, exist_ok=True)
                stdout_path = run_dir / "stdout.txt"
                gc_path = run_dir / "gc.log"
                stdout_path.touch(exist_ok=True)
                gc_path.touch(exist_ok=True)
                env_values = {
                    "LAB05_MODE": args.mode,
                    "LAB05_RUN_ID": rid,
                    "LAB05_GC": cell["gc"],
                    "LAB05_BENCHMARK": cell["benchmark"],
                    "LAB05_HEAP_MB": str(heap_mb),
                    "LAB05_ITERATIONS": str(suite["iterations"]),
                    "LAB05_SIZE": str(suite["workload_size"]),
                    "LAB05_DACAPO_JAR": f"/workspace/artifacts/{jar_rel}",
                }
                cmd = [compose, "compose", "-f", str(COMPOSE.relative_to(ROOT)), "run", "--rm", "--no-deps"]
                for key, value in env_values.items():
                    cmd.extend(["-e", f"{key}={value}"])
                cmd.append("benchmark")
                print(f"[{completed + 1}/{total}] {rid}", flush=True)
                result = subprocess.run(cmd, cwd=ROOT, env=compose_env, capture_output=True, text=True)
                try:
                    output = stdout_path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    output = ""
                if not output.strip():
                    output = (result.stdout or "") + (result.stderr or "")
                    if output:
                        stdout_path.write_text(output, encoding="utf-8")
                gc_text = gc_path.read_text(encoding="utf-8", errors="replace") if gc_path.exists() else ""
                host_label = os.environ.get(
                    "LAB05_HOST_LABEL",
                    f"{platform.system()}-{platform.machine()}-{platform.release()}",
                )
                row = make_row(
                    args.mode, rep, seed, cell, heap_mb, cpus, digest, output, gc_text,
                    run_dir, result.returncode, int(suite["iterations"]), host_label,
                )
                append_row(csv_path, row)
                existing[row["run_id"]] = {k: str(v) for k, v in row.items()}
                completed += 1
                if result.returncode != 0:
                    driver_path = run_dir / "compose-driver.log"
                    driver_path.write_text((result.stdout or "") + (result.stderr or ""), encoding="utf-8")
                if cooldown and completed < total:
                    time.sleep(cooldown)
            block_ids = {run_id(args.mode, rep, cell) for cell in cells}
            if block_ids.issubset(existing):
                if validate_csv(csv_path) != 0:
                    raise ValueError(f"Validação do CSV falhou ao fechar bloco {rep}; coleta pausada")
        missing = planned_ids.difference(existing)
        if missing:
            raise ValueError(f"Faltam {len(missing)} runs previstos; a retomada pode continuar depois")
        if validate_csv(csv_path, expected_n=total_blocks) != 0:
            raise ValueError("Validação final do CSV falhou")
        failures = sum(row.get("failed") == "1" or row.get("failed") == 1 for row in existing.values() if row.get("run_id") in planned_ids)
        print(f"Tentativas registradas: {total}; falhas registradas: {failures}; CSV: {csv_path}")
        return 0 if failures == 0 else 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
