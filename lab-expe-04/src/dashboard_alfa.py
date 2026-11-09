from __future__ import annotations


def renderizar(st, graficos, comparar_alfa, formatar_numero) -> None:
    st.subheader("O que muda com α = 0,01? — análise extra da pergunta 12")
    resumo = comparar_alfa(graficos.carregar_simulacoes())
    tabela = resumo.rename(columns={
        "situacao": "Situação", "teste": "Teste", "erro_tipo_i_005": "Erro tipo I α=0,05",
        "erro_tipo_i_001": "Erro tipo I α=0,01", "poder_005_max_efeito": "Poder α=0,05 (r máx.)",
        "poder_001_max_efeito": "Poder α=0,01 (r máx.)", "reducao_poder_pp": "Perda de poder (p.p.)",
        "r_maximo": "Maior r simulado",
    })
    for coluna in ("Erro tipo I α=0,05", "Erro tipo I α=0,01", "Poder α=0,05 (r máx.)", "Poder α=0,01 (r máx.)"):
        tabela[coluna] = tabela[coluna].map(lambda v: f"{v:.2%}".replace(".", ","))
    tabela["Perda de poder (p.p.)"] = tabela["Perda de poder (p.p.)"].map(
        lambda v: f"{v:.1f}".replace(".", ",")
    )
    st.dataframe(tabela, hide_index=True, width="stretch")
    pearson_b = resumo[(resumo["situacao"] == "B") & (resumo["teste"] == "Pearson")].iloc[0]
    st.markdown(
        f"**Interpretação.** Reduzir α diminui o poder nos dois testes, pois exige evidência mais forte antes de rejeitar H₀. "
        f"Na situação A, os erros tipo I com α=0,01 ficam próximos de 1%; na B, o Pearson tem "
        f"{formatar_numero(pearson_b['erro_tipo_i_001'] * 100, 2)}%, acima do nominal, indicando que a aproximação t do Pearson "
        f"fica menos bem calibrada sob essas marginais lognormais. A tabela reaplica os dois cortes aos mesmos resultados simulados."
    )
