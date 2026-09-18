def dividir_times(jogadores: list[tuple[str, int]]) -> tuple[list[str], list[str]]:
    for _, habilidade in jogadores:
        if habilidade < 0:
            raise ValueError("habilidade")

    ordenados = sorted(jogadores, key=lambda jogador: jogador[1], reverse=True)

    time_a = [nome for indice, (nome, _) in enumerate(ordenados) if indice % 2 == 0]
    time_b = [nome for indice, (nome, _) in enumerate(ordenados) if indice % 2 == 1]

    return time_a, time_b
