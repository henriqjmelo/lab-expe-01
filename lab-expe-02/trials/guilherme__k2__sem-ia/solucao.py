def validar_senha(senha: str) -> tuple[bool, list[str]]:
    violacoes = []

    # 1. Tamanho: Mínimo de 10 caracteres
    if len(senha) < 10:
        violacoes.append("tamanho")

    # 2. Maiúscula: Ao menos 1 letra maiúscula
    if not any(c.isupper() for c in senha):
        violacoes.append("maiuscula")

    # 3. Minúscula: Ao menos 1 letra minúscula
    if not any(c.islower() for c in senha):
        violacoes.append("minuscula")

    # 4. Dígito: Ao menos 1 dígito
    if not any(c.isdigit() for c in senha):
        violacoes.append("digito")

    # 5. Especial: Ao menos 1 caractere do conjunto !@#$%&*
    caracteres_especiais = set("!@#$%&*")
    if not any(c in caracteres_especiais for c in senha):
        violacoes.append("especial")

    # 6. Repetição: Não ter 3 ou mais caracteres idênticos consecutivos
    tem_repeticao_tripla = False
    for i in range(len(senha) - 2):
        if senha[i] == senha[i + 1] == senha[i + 2]:
            tem_repeticao_tripla = True
            break
    if tem_repeticao_tripla:
        violacoes.append("repeticao")

    # 7. Palavra "senha": Não conter a substring "senha" (case-insensitive)
    if "senha" in senha.lower():
        violacoes.append("palavra_senha")

    valida = len(violacoes) == 0
    return valida, violacoes