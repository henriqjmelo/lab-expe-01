import pytest

from solucao import dividir_times


def test_lista_vazia_retorna_dois_times_vazios():
    assert dividir_times([]) == ([], [])


def test_um_unico_jogador_vai_pro_time_a():
    assert dividir_times([("ana", 10)]) == (["ana"], [])


def test_exemplo_do_enunciado():
    jogadores = [("ana", 10), ("bruno", 8), ("carla", 8), ("davi", 5), ("elis", 3)]
    assert dividir_times(jogadores) == (["ana", "carla", "elis"], ["bruno", "davi"])


def test_numero_par_de_jogadores_times_do_mesmo_tamanho():
    jogadores = [("a", 4), ("b", 3), ("c", 2), ("d", 1)]
    time_a, time_b = dividir_times(jogadores)
    assert len(time_a) == len(time_b) == 2


def test_numero_impar_time_a_fica_com_um_a_mais():
    jogadores = [("a", 4), ("b", 3), ("c", 2)]
    time_a, time_b = dividir_times(jogadores)
    assert len(time_a) == 2
    assert len(time_b) == 1


def test_empate_mantem_ordem_de_entrada():
    jogadores = [("a", 5), ("b", 5), ("c", 5), ("d", 5)]
    assert dividir_times(jogadores) == (["a", "c"], ["b", "d"])


def test_habilidade_zero_e_permitida():
    resultado = dividir_times([("a", 0), ("b", 0)])
    assert resultado == (["a"], ["b"])


def test_habilidade_negativa_levanta_erro():
    with pytest.raises(ValueError):
        dividir_times([("a", -1)])


def test_todos_os_jogadores_aparecem_exatamente_uma_vez():
    jogadores = [("a", 9), ("b", 7), ("c", 5), ("d", 3), ("e", 1)]
    time_a, time_b = dividir_times(jogadores)
    assert sorted(time_a + time_b) == ["a", "b", "c", "d", "e"]
