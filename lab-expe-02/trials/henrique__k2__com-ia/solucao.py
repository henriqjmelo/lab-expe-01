def validar_senha(senha: str) -> tuple[bool, list[str]]:
    violacoes: list[str] = []
    especiais = "\!@#$%&*"

    if len(senha) < 10:
        violacoes.append("tamanho")
    if not any(caractere.isupper() for caractere in senha):
        violacoes.append("maiuscula")
    if not any(caractere.islower() for caractere in senha):
        violacoes.append("minuscula")
    if not any(caractere.isdigit() for caractere in senha):
        violacoes.append("digito")
    if not any(caractere in especiais for caractere in senha):
        violacoes.append("especial")

    for indice in range(len(senha) - 2):
        if senha[indice] == senha[indice + 1] == senha[indice + 2]:
            violacoes.append("repeticao")
            break

    if "senha" in senha.lower():
        violacoes.append("palavra_senha")

    return (len(violacoes) == 0, violacoes)
