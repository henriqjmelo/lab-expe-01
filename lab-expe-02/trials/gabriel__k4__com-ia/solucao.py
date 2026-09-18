def detectar_rajadas(eventos: list[tuple[str, int]], limite: int, janela_segundos: int) -> list[str]:
    if limite <= 0:
        raise ValueError("limite")

    por_usuario: dict[str, list[int]] = {}
    for usuario, ts in eventos:
        por_usuario.setdefault(usuario, []).append(ts)

    resultado = []
    for usuario, timestamps in por_usuario.items():
        timestamps.sort()
        inicio = 0
        for fim in range(len(timestamps)):
            while timestamps[fim] - timestamps[inicio] > janela_segundos:
                inicio += 1
            if fim - inicio + 1 > limite:
                resultado.append(usuario)
                break

    return resultado
