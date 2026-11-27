"""Fixtures textuais do harness para testar o parser; não são dados medidos."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_dacapo as runner  # noqa: E402


HARNESS = """openjdk version \"25.0.5.1\" 2026-10-21 LTS
OpenJDK Runtime Environment Temurin-25.0.5.1+2
OpenJDK 64-Bit Server VM Temurin-25.0.5.1+2
===== DaCapo 23.11-MR2-chopin cassandra completed warmup 1 =====
===== DaCapo 23.11-MR2-chopin cassandra completed warmup 2 =====
===== DaCapo 23.11-MR2-chopin cassandra completed warmup 3 =====
===== DaCapo 23.11-MR2-chopin cassandra completed warmup 4 =====
===== DaCapo tail latency, simple: 50% 900 usec, 90% 1900 usec, 99% 2500 usec, 99.9% 2900 usec, max 3000 usec =====
===== DaCapo tail latency, metered 100ms smoothing: 50% 1000 usec, 90% 2000 usec, 99% 3500 usec, max 4000 usec =====
===== DaCapo 23.11-MR2-chopin cassandra PASSED in 12345 msec =====
"""


def test_parser_reconhece_a_iteracao_final_e_quatro_aquecimentos():
    assert runner.parse_exec_ms(HARNESS, "cassandra") == 12345.0
    assert runner.count_warmups(HARNESS, "cassandra") == [1, 2, 3, 4]


def test_parser_identifica_major_do_jdk_no_fixture_textual():
    assert runner.parse_jdk_major(HARNESS) == 25
    assert runner.parse_jdk_major('openjdk version "21.0.4" 2024-07-16') == 21
    assert runner.parse_jdk_major("java indisponivel") is None


def test_preflight_exige_linhas_de_diff_revisaveis_e_rejeita_placeholder():
    assert not runner.flags_diff_ready("# PENDENTE — comparar flags\n")
    assert not runner.flags_diff_ready("--- G1.txt\n+++ ZGC.txt\n")
    assert runner.flags_diff_ready("--- G1.txt\n+++ ZGC.txt\n@@\n- old\n+ new\n")


def test_p99_simple_e_convertido_de_microssegundos_sem_misturar_metered():
    assert runner.parse_simple_p99_ms(HARNESS) == 2.5


def test_parser_de_p99_nao_inventa_valor_quando_nao_ha_relatorio():
    assert runner.parse_simple_p99_ms("DaCapo biojava PASSED in 100 msec") is None


def test_pausa_maxima_de_gc_converte_segundos_e_milisegundos():
    texto = "[0.1s][info][gc] GC(0) Pause Young 2.5ms\n[0.2s][info][gc] Pause Cleanup 0.004s"
    assert runner.parse_gc_pause_max_ms(texto) == 4.0


def test_make_row_exige_exit_code_java_e_major_jdk_25(tmp_path):
    output = HARNESS + "__LAB05_JAVA_EXIT_CODE__=0\n__LAB05_CPU_S__=9.25\n__LAB05_RSS_KB__=655360\n"
    cell = {"benchmark": "cassandra", "gc": "G1", "heap_mult": 2.0}
    params = {
        "mode": "pilot", "rep": 1, "seed": 42, "cell": cell, "heap_mb": 512,
        "cpus": 4, "digest": "sha256:abc", "output": output,
        "gc_text": "[0.2s][info][gc] Using G1\n[0.3s][info][gc] Pause Young 2.5ms",
        "run_dir": tmp_path / "run", "exit_code": 0, "iterations": 5, "host": "host",
    }
    assert runner.make_row(**params)["failed"] == 0
    missing_exit = runner.make_row(**{**params, "output": output.replace("__LAB05_JAVA_EXIT_CODE__=0\n", "")})
    assert missing_exit["failed"] == 1 and "marcador de saída Java ausente" in missing_exit["failure_reason"]
    wrong_jdk = runner.make_row(**{**params, "output": output.replace("25.0.5.1", "21.0.1")})
    assert wrong_jdk["failed"] == 1 and "esperado OpenJDK 25" in wrong_jdk["failure_reason"]


def test_config_gera_16_celulas_e_ordem_por_bloco_reprodutivel():
    config = runner.load_config()
    cells = runner.make_cells(config)
    assert len(cells) == 16
    assert len({(c["benchmark"], c["heap_mult"], c["gc"]) for c in cells}) == 16
    assert runner.order_block(cells, 42) == runner.order_block(cells, 42)
    assert runner.order_block(cells, 42) != runner.order_block(cells, 43)


def test_run_id_e_estavel_e_distingue_celulas():
    cell = {"benchmark": "cassandra", "gc": "G1", "heap_mult": 2.0}
    assert runner.run_id("pilot", 1, cell) == "pilot-b01-G1-h2-cassandra"
