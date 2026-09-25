def consolidar_notas(notas: list[dict]) -> dict[str, float]:
    totais: dict[str, float] = {}

    for nota in notas:
        if nota["cancelada"]:
            continue
        if nota["valor"] < 0:
            raise ValueError("valor negativo")
        categoria = nota["categoria"]
        totais[categoria] = totais.get(categoria, 0.0) + nota["valor"]

    return {
        categoria: round(total, 2)
        for categoria, total in totais.items()
        if total > 0
    }
