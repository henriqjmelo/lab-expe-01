from __future__ import annotations

import pytest

from metricas.frequencia import frequencia_semanal, na_janela, semanas_da_janela

INICIO = "2025-10-01T00:00:00Z"
FIM = "2026-10-01T00:00:00Z"


def test_janela_de_12_meses_tem_cerca_de_52_1_semanas():
    assert semanas_da_janela(INICIO, FIM) == pytest.approx(52.14, abs=0.01)


def test_conta_so_as_datas_da_janela():
    datas = [
        "2025-09-30T23:59:59Z",
        "2025-10-01T00:00:00Z",
        "2026-03-15T12:00:00Z",
        "2026-10-01T00:00:00Z",
    ]
    assert frequencia_semanal(datas, INICIO, FIM) == pytest.approx(2 / 52.142857)


def test_na_janela_com_data_vazia():
    assert not na_janela(None, INICIO, FIM)
    assert not na_janela("", INICIO, FIM)
