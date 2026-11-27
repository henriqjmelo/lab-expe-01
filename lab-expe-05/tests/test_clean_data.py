"""Fixtures sintéticas do cleaner; não são medições de DaCapo."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import clean_data  # noqa: E402
import validate_schema as schema  # noqa: E402


def sample_frame() -> pd.DataFrame:
    rows = []
    for benchmark in ("cassandra", "spring", "biojava", "pmd"):
        for heap in ("2.0", "4.0"):
            for gc in ("G1", "ZGC"):
                latency = benchmark in {"cassandra", "spring"}
                rows.append({
                    "run_id": f"pilot-b01-{gc}-h{heap}-{benchmark}", "rep": "1",
                    "timestamp": "2026-11-20T12:00:00Z", "host": "fixture-host",
                    "jdk_version": "openjdk version 25.0.5.1 fixture", "image_digest": "sha256:fixture",
                    "gc": gc, "cpus": "4", "heap_mult": heap, "heap_mb": "512",
                    "benchmark": benchmark, "iterations": "5", "exec_ms": "1234.5",
                    "lat_p99_ms": "12.3" if latency else "", "gc_pause_max_ms": "4.2",
                    "cpu_s": "9.8", "rss_peak_mb": "640.1", "failed": "0",
                    "failure_reason": "", "seed": "42",
                    "raw_file": f"pilot/run-{gc}-{heap}-{benchmark}/stdout.txt",
                    "gc_log_file": f"pilot/run-{gc}-{heap}-{benchmark}/gc.log",
                })
    return pd.DataFrame(rows, columns=schema.COLUNAS)


def test_clean_frame_preserva_16_celulas_balanceadas():
    source = sample_frame()
    cleaned, excluded, warnings = clean_data.clean_frame(source, expected_n=1)
    assert len(cleaned) == 16
    assert excluded == 0
    assert warnings == []
    assert list(cleaned.columns) == schema.COLUNAS


def test_falha_e_excluida_mas_saida_confirmatoria_desbalanceada_e_bloqueada():
    source = sample_frame()
    source.loc[0, ["failed", "failure_reason", "exec_ms", "gc_pause_max_ms", "cpu_s", "rss_peak_mb"]] = [
        "1", "OutOfMemoryError", "", "", "", "",
    ]
    with pytest.raises(ValueError, match="faltam 1 células|não balanceado"):
        clean_data.clean_frame(source, expected_n=1)
    exploratory, excluded, _ = clean_data.clean_frame(source, allow_unbalanced=True)
    assert len(exploratory) == 15
    assert excluded == 1


def test_cleaner_rejeita_csv_que_nao_passou_no_schema():
    source = sample_frame()
    source.loc[0, "gc"] = "Parallel"
    with pytest.raises(ValueError, match="não passou no contrato"):
        clean_data.clean_frame(source)


def test_saida_existente_nao_e_substituida_sem_force(tmp_path):
    output = tmp_path / "clean.csv"
    output.write_text("previous derivative", encoding="utf-8")
    with pytest.raises(FileExistsError, match="saída já existe"):
        clean_data.write_csv_atomic(sample_frame(), output)
    assert output.read_text(encoding="utf-8") == "previous derivative"
    clean_data.write_csv_atomic(sample_frame(), output, force=True)
    assert pd.read_csv(output).shape[0] == 16


def test_cli_rejeita_saida_fora_de_processed_antes_de_ler_entrada(capsys):
    status = clean_data.main(["arquivo-nao-existe.csv", "--output", "data/raw/nao-sobrescrever.csv"])
    assert status == 2
    assert "saída deve ficar sob" in capsys.readouterr().err
    assert not (clean_data.DATA / "raw" / "nao-sobrescrever.csv").exists()
