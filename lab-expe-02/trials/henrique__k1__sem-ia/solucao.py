def distribuir_chamados(chamados: list[str], atendentes: list[str], capacidade: int) -> dict[str, list[str]]:
    if capacidade <= 0:
        raise ValueError("capacidade")

    if not atendentes:
        if not chamados:
            return {}
        raise ValueError("capacidade insuficiente")

    if capacidade * len(atendentes) < len(chamados):
        raise ValueError("capacidade insuficiente")

    if not chamados:
        return {atendente: [] for atendente in atendentes}

    distribuicao = {atendente: [] for atendente in atendentes}
    ocupacao = {atendente: 0 for atendente in atendentes}
    indice = 0

    for chamado in chamados:
        while True:
            atendente = atendentes[indice % len(atendentes)]
            if ocupacao[atendente] < capacidade:
                distribuicao[atendente].append(chamado)
                ocupacao[atendente] += 1
                indice += 1
                break
            indice += 1

    return distribuicao
