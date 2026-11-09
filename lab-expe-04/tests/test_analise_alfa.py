import numpy as np
import pandas as pd

from src.analise_alfa import comparar_alfa


def test_compara_erro_tipo_i_e_poder_com_os_mesmos_pvalores_agregados():
    dados = pd.DataFrame([
        {"situacao": s, "r_latente": r, "teste": t, "taxa_005": p05, "taxa_001": p01}
        for s in ("A", "B")
        for t in ("Pearson", "Spearman")
        for r, p05, p01 in ((0.0, 0.05, 0.01), (0.5, 0.8, 0.6))
    ])

    resultado = comparar_alfa(dados)

    assert len(resultado) == 4
    assert (resultado["r_maximo"] == 0.5).all()
    assert np.allclose(resultado["reducao_poder_pp"], 20.0)
    assert (resultado["erro_tipo_i_001"] < resultado["erro_tipo_i_005"]).all()
