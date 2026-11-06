import numpy as np
import pandas as pd
import pytest

from src.generate import gerar_lognormal, gerar_normal, gerar_situacao


def test_situacao_a_e_reprodutivel_com_mesma_seed():
    primeiro = gerar_normal(30, 0.3, np.random.default_rng(42))
    segundo = gerar_normal(30, 0.3, np.random.default_rng(42))

    pd.testing.assert_frame_equal(primeiro, segundo)


def test_situacao_b_e_reprodutivel_e_positiva():
    parametros = {"loc_log_mu": 5.0, "loc_log_sigma": 1.0}
    primeiro = gerar_lognormal(30, 0.3, np.random.default_rng(42), **parametros)
    segundo = gerar_lognormal(30, 0.3, np.random.default_rng(42), **parametros)

    pd.testing.assert_frame_equal(primeiro, segundo)
    assert (primeiro > 0).all().all()


def test_gerar_situacao_exige_parametros_para_b():
    with pytest.raises(ValueError, match="exige parâmetros"):
        gerar_situacao("B", 30, 0.3, np.random.default_rng(42))


@pytest.mark.parametrize("correlacao", [-1.01, 1.01])
def test_rejeita_correlacao_fora_do_intervalo(correlacao):
    with pytest.raises(ValueError, match="entre -1 e 1"):
        gerar_normal(30, correlacao, np.random.default_rng(42))