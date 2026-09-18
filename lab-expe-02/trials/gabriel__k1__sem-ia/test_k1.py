from itertools import cycle

def distribuir_chamados(
    chamados: list[str], atendentes: list[str], capacidade: int
) -> dict[str, list[str]]:
    """Distribui chamados em round-robin respeitando capacidade máxima por atendente."""
    if not atendentes:
        raise ValueError("Lista de atendentes vazia")
    
    if capacidade <= 0:
        raise ValueError("Capacidade deve ser > 0")
    
    if len(chamados) > capacidade * len(atendentes):
        raise ValueError(
            f"Capacidade insuficiente: {len(chamados)} chamados, "
            f"máximo {capacidade * len(atendentes)}"
        )
    
    distribuicao = {atendente: [] for atendente in atendentes}
    rotacao = cycle(atendentes)
    
    for chamado in chamados:
        atendente = next(rotacao)
        distribuicao[atendente].append(chamado)
    
    return distribuicao