"""Estilo compartilhado dos graficos G1 a G4: uma cor fixa por serie."""
import matplotlib

# Testes (G3 e G4): Pearson azul, Spearman laranja
COR_PEARSON = "#1f77b4"
COR_SPEARMAN = "#ff7f0e"

# Dados (G1)
COR_REAL = "#2a9d8f"
COR_SIMULADO = "#7b4fa3"


def aplicar() -> None:
    matplotlib.rcParams.update({
        "figure.dpi": 110,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.frameon": False,
    })
