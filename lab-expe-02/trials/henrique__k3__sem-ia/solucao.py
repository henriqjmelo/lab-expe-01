from collections import defaultdict


def consolidar_notas(notas: list[dict]) -> dict[str, float]:
    totais = defaultdict(float)

    for nota in notas:
        if nota.get("cancelada"):
            continue

        valor = float(nota["valor"])
        if valor < 0:
            raise ValueError("valor")

        totais[nota["categoria"]] += valor

    return {categoria: round(total, 2) for categoria, total in totais.items() if round(total, 2) > 0}
