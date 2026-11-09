from __future__ import annotations

import pandas as pd


def comparar_alfa(dados: pd.DataFrame) -> pd.DataFrame:
    """Compara erro tipo I e poder no maior efeito para α=0,05 e α=0,01."""
    max_efeito = float(dados["r_latente"].max())
    nulo = dados[dados["r_latente"] == 0.0].set_index(["situacao", "teste"])
    teto = dados[dados["r_latente"] == max_efeito].set_index(["situacao", "teste"])
    linhas = []
    for (situacao, teste), linha_nula in nulo.iterrows():
        linha_teto = teto.loc[(situacao, teste)]
        linhas.append({
            "situacao": situacao,
            "teste": teste,
            "erro_tipo_i_005": float(linha_nula["taxa_005"]),
            "erro_tipo_i_001": float(linha_nula["taxa_001"]),
            "poder_005_max_efeito": float(linha_teto["taxa_005"]),
            "poder_001_max_efeito": float(linha_teto["taxa_001"]),
            "reducao_poder_pp": float((linha_teto["taxa_005"] - linha_teto["taxa_001"]) * 100),
            "r_maximo": max_efeito,
        })
    return pd.DataFrame(linhas)
