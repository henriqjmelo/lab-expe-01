def distribuir_chamados(chamados: list[str], atendentes: list[str], capacidade: int) -> dict[str, list[str]]:
    if capacidade <= 0:
        raise ValueError("capacidade deve ser maior que zero")
    if len(chamados) > capacidade * len(atendentes):
        raise ValueError("capacidade insuficiente")

    resultado: dict[str, list[str]] = {atendente: [] for atendente in atendentes}
    if not chamados:
        return resultado

    posicao = 0
    for chamado in chamados:
        # Pula quem ja atingiu a capacidade; a validacao acima garante que
        # sempre sobra lugar, entao o laco nao roda indefinidamente.
        while len(resultado[atendentes[posicao % len(atendentes)]]) >= capacidade:
            posicao += 1
        resultado[atendentes[posicao % len(atendentes)]].append(chamado)
        posicao += 1

    return resultado
