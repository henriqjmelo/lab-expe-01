import pytest

from solucao import compactar, descompactar


def test_compactar_string_vazia():
    assert compactar("") == ""


def test_compactar_caractere_unico_fica_literal():
    assert compactar("a") == "a"


def test_compactar_sequencia_de_dois_fica_literal():
    assert compactar("aa") == "aa"


def test_compactar_sequencia_de_tres_compacta():
    assert compactar("aaa") == "a3"


def test_compactar_exemplo_do_enunciado():
    assert compactar("aaaabbbcc") == "a4b3cc"


def test_compactar_contagem_com_dois_digitos():
    assert compactar("b" * 15) == "b15"


def test_compactar_caractere_invalido_levanta_erro():
    with pytest.raises(ValueError):
        compactar("aa1bb")


def test_descompactar_reverte_compactar():
    assert descompactar("a4b3cc") == "aaaabbbcc"


def test_round_trip_para_varias_entradas():
    for original in ["", "a", "aa", "aaa", "xyzzzzzy", "mississippi"]:
        assert descompactar(compactar(original)) == original
