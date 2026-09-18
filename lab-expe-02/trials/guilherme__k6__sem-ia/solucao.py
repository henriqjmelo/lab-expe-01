def dividir_times(jogadores: list[tuple[str, int]]) -> tuple[list[str], list[str]]:
    for _, habilidade in jogadores:
        if habilidade < 0:
            raise ValueError("habilidade")

    ordenados = sorted(jogadores, key=lambda item: item[1], reverse=True)
    time_a: list[str] = []
    time_b: list[str] = []

    for indice, (nome, _) in enumerate(ordenados):
        if indice % 2 == 0:
            time_a.append(nome)
        else:
            time_b.append(nome)

    return time_a, time_b
