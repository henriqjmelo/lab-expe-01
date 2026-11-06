from __future__ import annotations

import pandas as pd

from src.analysis import gerar_exemplo, interpretar_resultados


def renderizar_exemplo(st) -> pd.DataFrame:
    dados, resultados = gerar_exemplo(seed=42, n=30, correlacao=0.3)
    st.subheader("Exemplo S01 — Pearson e Spearman em um conjunto simulado")
    st.markdown(
        "O conjunto contém 30 pares gerados por uma normal bivariada com correlação latente 0,3 e semente 42. "
        "A tabela mostra a correlação amostral e o p-valor bicaudal de cada teste; diferenças entre as estimativas "
        "são esperadas porque uma amostra pequena varia em relação ao parâmetro usado para gerar os dados."
    )
    tabela = resultados.rename(columns={
        "conjunto": "Conjunto", "teste": "Teste", "n": "n",
        "estatistica": "Estatística (r ou ρ)", "p_valor": "p-valor",
        "significativo_005": "p < 0,05",
    })
    st.dataframe(tabela, hide_index=True, use_container_width=True)
    st.markdown(interpretar_resultados(resultados))
    st.caption(
        "O p-valor mede quão extremos seriam resultados como este sob H₀; não é a probabilidade de H₀ ser verdadeira. "
        "Este exemplo ilustra a aplicação dos testes, não estima por si só erro tipo I nem poder."
    )
    return dados