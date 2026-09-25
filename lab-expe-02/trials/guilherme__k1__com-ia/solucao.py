def distribuir_chamados(chamados: list[str], atendentes: list[str], capacidade: int) -> dict[str, list[str]]:
    if capacidade <= 0:
        raise ValueError("capacidade deve ser positiva")
    if not atendentes:
        if chamados:
            raise ValueError("capacidade insuficiente")
        return {}
    if capacidade * len(atendentes) < len(chamados):
        raise ValueError("capacidade insuficiente")

    resultado = {atendente: [] for atendente in atendentes}
    indice = 0
    restantes = len(chamados)

    while restantes:
        atendente = atendentes[indice % len(atendentes)]
        if len(resultado[atendente]) < capacidade:
            resultado[atendente].append(chamados[len(chamados) - restantes])
            restantes -= 1
        indice += 1

    return resultado
