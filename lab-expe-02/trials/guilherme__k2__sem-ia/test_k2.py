from solucao import validar_senha


def test_senha_curta_e_generica_acumula_varias_violacoes():
    assert validar_senha("abc") == (False, ["tamanho", "maiuscula", "digito", "especial"])


def test_senha_valida_sem_violacoes():
    assert validar_senha("Corp2024!Xz") == (True, [])


def test_contem_palavra_senha_ignorando_maiuscula_minuscula():
    assert validar_senha("Senha1234!") == (False, ["palavra_senha"])


def test_string_vazia_viola_cinco_regras():
    valida, violacoes = validar_senha("")
    assert valida is False
    assert violacoes == ["tamanho", "maiuscula", "minuscula", "digito", "especial"]


def test_tres_iguais_consecutivos_viola_repeticao():
    valida, violacoes = validar_senha("Ab1!aaaXyz")
    assert "repeticao" in violacoes


def test_dois_iguais_intercalados_nao_viola_repeticao():
    valida, violacoes = validar_senha("Ab1!aabaaXyz")
    assert "repeticao" not in violacoes


def test_exatamente_dez_caracteres_satisfaz_tamanho():
    senha = "Ab1!567890"
    assert len(senha) == 10
    valida, violacoes = validar_senha(senha)
    assert "tamanho" not in violacoes


def test_falta_apenas_caractere_especial():
    valida, violacoes = validar_senha("Corp2024Xz")
    assert violacoes == ["especial"]


def test_falta_apenas_maiuscula():
    valida, violacoes = validar_senha("corp2024!xz")
    assert violacoes == ["maiuscula"]
