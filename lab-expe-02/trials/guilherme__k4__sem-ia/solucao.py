from collections import defaultdict


def detectar_rajadas(eventos: list[tuple[str, int]], limite: int, janela_segundos: int) -> list[str]:
    if limite <= 0:
        raise ValueError("limite")

    por_usuario = defaultdict(list)
    for usuario, timestamp in eventos:
        por_usuario[usuario].append(timestamp)

    usuarios = []
    for usuario, timestamps in por_usuario.items():
        timestamps.sort()
        inicio = 0
        for fim, timestamp in enumerate(timestamps):
            while timestamp - timestamps[inicio] > janela_segundos:
                inicio += 1
            if fim - inicio + 1 > limite:
                usuarios.append(usuario)
                break

    return sorted(set(usuarios))
