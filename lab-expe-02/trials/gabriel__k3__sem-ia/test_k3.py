import pytest

from solucao import consolidar_notas


def test_lista_vazia_retorna_dicionario_vazio():
    assert consolidar_notas([]) == {}


def test_soma_por_categoria_ignorando_canceladas():
    notas = [
        {"categoria": "livros", "valor": 50.0, "cancelada": False},
        {"categoria": "livros", "valor": 30.5, "cancelada": False},
        {"categoria": "eletronicos", "valor": 200.0, "cancelada": True},
        {"categoria": "papelaria", "valor": 12.333, "cancelada": False},
    ]
    assert consolidar_notas(notas) == {"livros": 80.5, "papelaria": 12.33}


def test_categoria_so_com_notas_canceladas_nao_aparece():
    notas = [
        {"categoria": "eletronicos", "valor": 100.0, "cancelada": True},
        {"categoria": "eletronicos", "valor": 50.0, "cancelada": True},
    ]
    assert consolidar_notas(notas) == {}


def test_valor_negativo_em_nota_valida_levanta_erro():
    notas = [{"categoria": "livros", "valor": -10.0, "cancelada": False}]
    with pytest.raises(ValueError, match="valor"):
        consolidar_notas(notas)


def test_valor_negativo_em_nota_cancelada_nao_levanta_erro():
    notas = [{"categoria": "livros", "valor": -10.0, "cancelada": True}]
    assert consolidar_notas(notas) == {}


def test_duas_notas_mesma_categoria_somam():
    notas = [
        {"categoria": "papelaria", "valor": 10.0, "cancelada": False},
        {"categoria": "papelaria", "valor": 5.0, "cancelada": False},
    ]
    assert consolidar_notas(notas) == {"papelaria": 15.0}


def test_arredondamento_e_so_na_soma_final():
    notas = [
        {"categoria": "servicos", "valor": 10.005, "cancelada": False},
        {"categoria": "servicos", "valor": 10.005, "cancelada": False},
    ]
    resultado = consolidar_notas(notas)
    assert resultado == {"servicos": round(20.01, 2)}


def test_uma_unica_nota_valida():
    notas = [{"categoria": "livros", "valor": 99.9, "cancelada": False}]
    assert consolidar_notas(notas) == {"livros": 99.9}
