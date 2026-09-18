from collections import defaultdict

def consolidar_notas(notas: list[dict]) -> dict[str, float]:
    """Soma as notas não canceladas por categoria."""
    totais = defaultdict(float)
    
    for nota in notas:
        if nota["cancelada"]:
            continue
        
        if nota["valor"] < 0:
            raise ValueError(f"Valor negativo não permitido: {nota['valor']}")
        
        totais[nota["categoria"]] += nota["valor"]
    
    return {cat: round(total, 2) for cat, total in totais.items()}