def compactar(texto: str) -> str:
    if any(not ("a" <= caractere <= "z") for caractere in texto):
        raise ValueError("texto")
    if texto == "":
        return ""

    saida: list[str] = []
    indice = 0
    while indice < len(texto):
        fim = indice + 1
        while fim < len(texto) and texto[fim] == texto[indice]:
            fim += 1

        quantidade = fim - indice
        if quantidade >= 3:
            saida.append(f"{texto[indice]}{quantidade}")
        else:
            saida.append(texto[indice] * quantidade)
        indice = fim

    return "".join(saida)


def descompactar(codigo: str) -> str:
    saida: list[str] = []
    indice = 0

    while indice < len(codigo):
        caractere = codigo[indice]
        indice += 1
        numero = ""
        while indice < len(codigo) and codigo[indice].isdigit():
            numero += codigo[indice]
            indice += 1

        if numero:
            quantidade = int(numero)
            if quantidade < 3:
                raise ValueError("codigo")
            saida.append(caractere * quantidade)
        else:
            saida.append(caractere)

    return "".join(saida)
