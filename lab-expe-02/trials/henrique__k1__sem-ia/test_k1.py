import pytest

from solucao import distribuir_chamados


def test_distribuicao_round_robin_basica():
    resultado = distribuir_chamados(["c1", "c2", "c3", "c4"], ["ana", "bruno"], 2)
    assert resultado == {"ana": ["c1", "c3"], "bruno": ["c2", "c4"]}


def test_lista_vazia_retorna_atendentes_com_listas_vazias():
    resultado = distribuir_chamados([], ["ana", "bruno"], 3)
    assert resultado == {"ana": [], "bruno": []}


def test_sem_chamados_e_sem_atendentes():
    assert distribuir_chamados([], [], 5) == {}


def test_atendente_unico_recebe_tudo():
    resultado = distribuir_chamados(["c1", "c2", "c3"], ["ana"], 3)
    assert resultado == {"ana": ["c1", "c2", "c3"]}


def test_resto_desigual_entre_tres_atendentes():
    resultado = distribuir_chamados(
        ["c1", "c2", "c3", "c4", "c5"], ["ana", "bruno", "carla"], 2
    )
    assert resultado == {"ana": ["c1", "c4"], "bruno": ["c2", "c5"], "carla": ["c3"]}


def test_capacidade_insuficiente_levanta_erro():
    with pytest.raises(ValueError, match="capacidade insuficiente"):
        distribuir_chamados(["c1", "c2", "c3"], ["ana"], 2)


def test_atendentes_vazio_com_chamados_levanta_erro():
    with pytest.raises(ValueError):
        distribuir_chamados(["c1"], [], 5)


def test_capacidade_zero_ou_negativa_levanta_erro():
    with pytest.raises(ValueError, match="capacidade"):
        distribuir_chamados(["c1"], ["ana"], 0)


def test_ids_de_chamado_repetidos_contam_como_distintos():
    resultado = distribuir_chamados(["c1", "c1", "c1"], ["ana"], 3)
    assert resultado == {"ana": ["c1", "c1", "c1"]}
