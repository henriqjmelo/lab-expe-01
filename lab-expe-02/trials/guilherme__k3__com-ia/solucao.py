def consolidar_notas(notas: list[dict]) -> dict[str, float]:
    totais: dict[str, float] = {}

    for nota in notas:
        # Canceladas saem antes de qualquer validacao: valor negativo em
        # nota cancelada nao e erro, e so ignorado.
        if nota["cancelada"]:
            continue

        valor = nota["valor"]
        if valor < 0:
            raise ValueError("valor negativo em nota nao cancelada")

        categoria = nota["categoria"]
        totais[categoria] = totais.get(categoria, 0.0) + valor

    # Arredonda so na soma final de cada categoria, nunca nota a nota.
    return {
        categoria: round(total, 2)
        for categoria, total in totais.items()
        if round(total, 2) > 0
    }
