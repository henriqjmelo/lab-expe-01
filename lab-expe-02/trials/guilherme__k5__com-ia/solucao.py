def compactar(texto: str) -> str:
    if any(caractere < "a" or caractere > "z" for caractere in texto):
        raise ValueError("texto")
    if not texto:
        return ""

    partes: list[str] = []
    inicio = 0

    for indice in range(1, len(texto) + 1):
        if indice == len(texto) or texto[indice] != texto[inicio]:
            quantidade = indice - inicio
            caractere = texto[inicio]
            if quantidade >= 3:
                partes.append(f"{caractere}{quantidade}")
            else:
                partes.append(caractere * quantidade)
            inicio = indice

    return "".join(partes)


def descompactar(codigo: str) -> str:
    partes: list[str] = []
    indice = 0

    while indice < len(codigo):
        caractere = codigo[indice]
        indice += 1
        inicio_numero = indice
        while indice < len(codigo) and codigo[indice].isdigit():
            indice += 1

        if inicio_numero < indice:
            partes.append(caractere * int(codigo[inicio_numero:indice]))
        else:
            partes.append(caractere)

    return "".join(partes)
