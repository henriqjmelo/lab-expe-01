import re


def validar_senha(senha: str) -> tuple[bool, list[str]]:
    violacoes: list[str] = []

    if len(senha) < 10:
        violacoes.append("tamanho")
    if not any(c.isupper() for c in senha):
        violacoes.append("maiuscula")
    if not any(c.islower() for c in senha):
        violacoes.append("minuscula")
    if not any(c.isdigit() for c in senha):
        violacoes.append("digito")
    if not any(c in "!@#$%&*" for c in senha):
        violacoes.append("especial")
    if re.search(r"(.)\1\1", senha):
        violacoes.append("repeticao")
    if "senha" in senha.lower():
        violacoes.append("palavra_senha")

    return not violacoes, violacoes
