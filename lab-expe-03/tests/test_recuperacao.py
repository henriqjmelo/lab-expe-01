"""Testes de metricas/recuperacao.py: tempo de recuperacao (RQ 04), issue #139."""

from __future__ import annotations

import pytest

from metricas.recuperacao import Run, episodios_do_workflow, tempo_recuperacao


def run(wf, conclusion, inicio, fim=None):
    return Run(wf, conclusion, f"2025-03-10T{inicio}:00Z", f"2025-03-10T{fim or inicio}:00Z")


def test_exemplo_do_enunciado_1h20():
    # sucesso antes; falhas 10:00 e 10:30; sucesso as 11:15 terminando 11:20.
    runs = [
        run(1, "success", "09:00", "09:05"),
        run(1, "failure", "10:00", "10:05"),
        run(1, "failure", "10:30", "10:35"),
        run(1, "success", "11:15", "11:20"),
    ]
    r = tempo_recuperacao(runs)
    assert r["mediana_horas"] == pytest.approx(80 / 60)
    assert r["n_episodios"] == 1
    assert r["n_censurados"] == 0


def test_falha_nunca_recuperada_e_censurada():
    runs = [run(1, "success", "09:00"), run(1, "failure", "10:00")]
    r = tempo_recuperacao(runs)
    assert r["n_episodios"] == 1
    assert r["n_censurados"] == 1
    assert r["prop_censurados"] == 1.0
    assert r["mediana_horas"] is None


def test_cancelados_nao_abrem_nem_fecham_episodio():
    runs = [
        run(1, "success", "09:00"),
        run(1, "cancelled", "09:30"),
        run(1, "failure", "10:00"),
        run(1, "cancelled", "10:10"),
        run(1, "skipped", "10:20"),
        run(1, "success", "11:00", "11:00"),
    ]
    assert tempo_recuperacao(runs)["mediana_horas"] == pytest.approx(1.0)


def test_workflows_diferentes_nao_se_misturam():
    # A falha do workflow 1 nao e "recuperada" pelo sucesso do workflow 2.
    runs = [
        run(1, "success", "08:00"),
        run(1, "failure", "09:00"),
        run(2, "success", "09:30"),
        run(1, "success", "12:00", "12:00"),
    ]
    r = tempo_recuperacao(runs)
    assert r["n_episodios"] == 1
    assert r["mediana_horas"] == pytest.approx(3.0)


def test_falhas_antes_do_primeiro_sucesso_nao_abrem_episodio():
    duracoes, censurados, iniciais = episodios_do_workflow(
        [run(1, "failure", "08:00"), run(1, "timed_out", "08:30"), run(1, "success", "09:00")]
    )
    assert duracoes == []
    assert censurados == 0
    assert iniciais == 2


def test_mediana_entre_episodios_de_varios_workflows_e_ordem_da_entrada_nao_importa():
    runs = [
        run(2, "success", "12:00", "12:00"),
        run(1, "success", "08:00"),
        run(1, "failure", "09:00"),
        run(1, "success", "10:00", "10:00"),  # 1h
        run(2, "success", "07:00"),
        run(2, "startup_failure", "08:00"),  # ate 12:00 = 4h
        run(1, "failure", "13:00"),
        run(1, "success", "15:00", "15:00"),  # 2h
    ]
    r = tempo_recuperacao(runs)
    assert r["n_episodios"] == 3
    assert r["mediana_horas"] == pytest.approx(2.0)


def test_sem_runs():
    r = tempo_recuperacao([])
    assert r["n_episodios"] == 0
    assert r["prop_censurados"] is None
    assert r["mediana_horas"] is None
