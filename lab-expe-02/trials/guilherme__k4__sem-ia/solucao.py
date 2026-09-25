from collections import defaultdict


def detectar_rajadas(
    eventos: list[tuple[str, int]], limite: int, janela_segundos: int
) -> list[str]:
    if limite < 1 or janela_segundos < 0:
        raise ValueError("O limite deve ser >= 1 e a janela de segundos deve ser >= 0.")

    if not eventos:
        return []

    eventos_por_usuario = defaultdict(list)
    for usuario, timestamp in eventos:
        eventos_por_usuario[usuario].append(timestamp)

    usuarios_em_rajada = []

    for usuario, timestamps in eventos_por_usuario.items():
        timestamps.sort()

        inicio = 0
        tem_rajada = False

        for fim in range(len(timestamps)):
            while timestamps[fim] - timestamps[inicio] > janela_segundos:
                inicio += 1

            if (fim - inicio + 1) > limite:
                tem_rajada = True
                break

        if tem_rajada:
            usuarios_em_rajada.append(usuario)

    return usuarios_em_rajada