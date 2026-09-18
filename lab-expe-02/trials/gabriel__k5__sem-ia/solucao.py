def compactar(texto: str) -> str:
    """Compacta sequências de três ou mais letras minúsculas iguais."""
    if any(caractere < "a" or caractere > "z" for caractere in texto):
        raise ValueError("texto")
    if not texto:
        return ""

    partes: list[str] = []
    inicio = 0

    for indice in range(1, len(texto) + 1):
        if indice == len(texto) or texto[indice] != texto[inicio]:
            quantidade = indice - inicio
            letra = texto[inicio]
            partes.append(letra + str(quantidade) if quantidade >= 3 else letra * quantidade)
            inicio = indice

    return "".join(partes)


def descompactar(codigo: str) -> str:
    """Desfaz um código válido gerado por :func:`compactar`."""
    partes: list[str] = []
    indice = 0

    while indice < len(codigo):
        letra = codigo[indice]
        if letra < "a" or letra > "z":
            raise ValueError("codigo")
        indice += 1

        inicio_numero = indice
        while indice < len(codigo) and codigo[indice].isdigit():
            indice += 1

        if inicio_numero < indice:
            quantidade = int(codigo[inicio_numero:indice])
            if quantidade < 3:
                raise ValueError("codigo")
            partes.append(letra * quantidade)
        else:
            partes.append(letra)

    return "".join(partes)
