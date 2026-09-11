import pytest

from solucao import detectar_rajadas


def test_lista_vazia_retorna_lista_vazia():
    assert detectar_rajadas([], limite=2, janela_segundos=10) == []


def test_rajada_basica_do_enunciado():
    eventos = [
        ("ana", 0), ("ana", 5), ("ana", 8), ("ana", 40),
        ("bruno", 0), ("bruno", 100),
    ]
    assert detectar_rajadas(eventos, limite=2, janela_segundos=10) == ["ana"]


def test_exatamente_no_limite_nao_e_rajada():
    eventos = [("ana", 0), ("ana", 5)]
    assert detectar_rajadas(eventos, limite=2, janela_segundos=10) == []


def test_janela_inclui_as_duas_pontas():
    # diff exatamente igual a janela_segundos precisa contar como dentro da
    # janela; se alguem implementar limite exclusivo (diff < janela), esses
    # dois eventos cairiam em janelas separadas e o teste pegaria o erro.
    eventos = [("ana", 0), ("ana", 10)]
    assert detectar_rajadas(eventos, limite=1, janela_segundos=10) == ["ana"]


def test_eventos_fora_de_ordem_sao_tratados_corretamente():
    eventos = [("ana", 40), ("ana", 0), ("ana", 8), ("ana", 5)]
    assert detectar_rajadas(eventos, limite=2, janela_segundos=10) == ["ana"]


def test_limite_invalido_levanta_erro():
    with pytest.raises(ValueError):
        detectar_rajadas([("ana", 0)], limite=0, janela_segundos=10)


def test_usuario_nao_aparece_duplicado_na_saida():
    eventos = [("ana", 0), ("ana", 1), ("ana", 2), ("ana", 100), ("ana", 101), ("ana", 102)]
    resultado = detectar_rajadas(eventos, limite=2, janela_segundos=5)
    assert resultado == ["ana"]
    assert resultado.count("ana") == 1


def test_multiplos_usuarios_apenas_um_com_rajada():
    eventos = [
        ("ana", 0), ("ana", 1), ("ana", 2),
        ("bruno", 0), ("bruno", 50),
    ]
    assert detectar_rajadas(eventos, limite=2, janela_segundos=5) == ["ana"]
