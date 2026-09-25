def compactar(texto: str) -> str:
    if any(not ("a" <= caractere <= "z") for caractere in texto):
        raise ValueError("texto deve conter apenas letras minusculas de a a z")

    partes: list[str] = []
    indice = 0

    while indice < len(texto):
        fim = indice + 1
        while fim < len(texto) and texto[fim] == texto[indice]:
            fim += 1

        repeticoes = fim - indice
        if repeticoes >= 3:
            partes.append(f"{texto[indice]}{repeticoes}")
        else:
            # Sequencias de 1 ou 2 ficam literais, sem contagem.
            partes.append(texto[indice] * repeticoes)

        indice = fim

    return "".join(partes)


def descompactar(codigo: str) -> str:
    partes: list[str] = []
    indice = 0

    while indice < len(codigo):
        caractere = codigo[indice]
        indice += 1

        # A contagem pode ter mais de um digito, entao consome todos.
        digitos = ""
        while indice < len(codigo) and codigo[indice].isdigit():
            digitos += codigo[indice]
            indice += 1

        partes.append(caractere * int(digitos) if digitos else caractere)

    return "".join(partes)
