"""O dado sintetico so serve se for indistinguivel do real em forma.

Se ele nao passar no validador do contrato, o pipeline estara sendo testado
contra um arquivo que a coleta nunca vai produzir.
"""
import numpy as np
import pytest

import validate_schema as contrato
from scripts import gerar_sintetico as gs


@pytest.fixture(scope="module")
def dados():
    return gs.gerar(blocos=12, semente=42)


def test_passa_no_validador_do_contrato(dados, tmp_path):
    caminho = tmp_path / "s.csv"
    dados.to_csv(caminho, index=False)
    problemas = contrato.validar(contrato.ler_csv(caminho), n=12)
    erros = [str(p) for p in problemas if p.gravidade == "erro"]
    assert erros == []


def test_tem_16_celulas_vezes_os_blocos(dados):
    assert len(dados) == 16 * 12
    assert dados.groupby(["gc", "heap_mult", "benchmark"]).size().unique().tolist() == [12]


def test_p99_so_nos_benchmarks_de_latencia(dados):
    for bench, info in gs.BENCHMARKS.items():
        valores = dados[(dados["benchmark"] == bench) & (dados["failed"] == 0)]["lat_p99_ms"]
        tem = bool((valores != "").all())
        assert tem == (info["p99_g1_ms"] is not None), bench


def test_a_semente_torna_a_geracao_reproduzivel():
    a = gs.gerar(blocos=4, semente=7)
    b = gs.gerar(blocos=4, semente=7)
    assert a.equals(b)
    assert not a.equals(gs.gerar(blocos=4, semente=8))


def test_a_ordem_das_celulas_e_embaralhada_dentro_do_bloco(dados):
    bloco1 = dados[dados["rep"] == 1]["benchmark"].tolist()
    # ordenado seria 4 blocos de 4 iguais em sequencia; embaralhado nao e
    assert bloco1 != sorted(bloco1)


def test_a_razao_injetada_aparece_nos_numeros():
    """Media de 2000 blocos tem de convergir para a razao plantada."""
    df = gs.gerar(blocos=2000, semente=1)
    df = df[df["failed"] == 0]
    for (bench, heap), esperado in gs.EFEITO_EXEC.items():
        c = df[(df["benchmark"] == bench) & (df["heap_mult"] == heap)]
        obtido = c[c["gc"] == "ZGC"]["exec_ms"].mean() / c[c["gc"] == "G1"]["exec_ms"].mean()
        assert obtido == pytest.approx(esperado, rel=0.01), (bench, heap)


def test_sem_efeito_zera_todas_as_razoes():
    df = gs.gerar(blocos=1500, semente=3, sem_efeito=True)
    for (bench, heap) in gs.EFEITO_EXEC:
        c = df[(df["benchmark"] == bench) & (df["heap_mult"] == heap)]
        razao = c[c["gc"] == "ZGC"]["exec_ms"].mean() / c[c["gc"] == "G1"]["exec_ms"].mean()
        assert razao == pytest.approx(1.0, rel=0.01), (bench, heap)
    assert df["failed"].sum() == 0
