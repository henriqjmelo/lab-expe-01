def dividir_times(jogadores: list[tuple[str, int]]) -> tuple[list[str], list[str]]:
    for nome, hab in jogadores:
        if hab < 0:
            raise ValueError("A habilidade não pode ser negativa.")

    jogadores_ordenados = sorted(
        enumerate(jogadores),
        key=lambda item: (-item[1][1], item[0])
    )

    time_a = []
    time_b = []

    for i, (_, (nome, _)) in enumerate(jogadores_ordenados):
        if i % 2 == 0:
            time_a.append(nome)
        else:
            time_b.append(nome)

    return time_a, time_b