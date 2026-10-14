# #141 — Robustez da RQ06: efeito de cada fator controlando os demais

- **Responsável:** Gabriel (`Gabriel200481`)
- **Sprint:** Lab03S03
- **Issue:** https://github.com/henriqjmelo/lab-expe-01/issues/141 (escopo redefinido em 14/10; o original entrou no #152)
- **Leia antes:** `lab-expe-03/AGENTS.md`, a RQ 06 em `lab-expe-03/ENUNCIADO.md` e a seção 3.7 de `artigo/03-resultados.md`

## Por que esta issue existe

A RQ06 pergunta que características se associam a melhor desempenho DORA. A análise atual (`analise.estatisticas.rq06`, já no `main`) faz **um Kruskal-Wallis por fator**, com ε² e Holm. Resultado na A1:

| Fator | Efeito no lead time (a) | Leitura |
| :--- | :--- | :--- |
| Idade (quartil) | ε² = 0,25 (grande) | ≤ 2 anos: 2,0 dias; > 10,9 anos: 28,5 dias |
| Contribuidores (quartil) | ε² = 0,11 (médio) | ≤ 48: 4,7 dias; > 338: 18,5 dias |
| Estrelas (quartil) | ε² = 0,06 (pequeno) | |
| Linguagem | não significativo após Holm | |

O problema: **os fatores são correlacionados entre si**. Projetos antigos tendem a ter mais contribuidores e mais estrelas. O teste univariado não diz se "equipes maiores têm lead time maior" ou se isso é só a idade aparecendo por outro caminho. Esta issue separa esses efeitos.

## Dados disponíveis (no Git)

`data/dataset_dora.csv`: uma linha por repositório.
- **Fatores:** `estrelas`, `contribuidores`, `idade_anos`, `linguagem` (use as linguagens com ≥ 15 repositórios e agrupe o resto em "Outras").
- **Métricas:**
  - `df_release_semana` (frequência);
  - `lt_a_release_dias` e `lt_b_release_dias` (lead time; 7 vazios);
  - `cfr_a` (proporção de 0 a 1);
  - `cfr_b_release` (preliminar, heurística v0 da #138);
  - `recuperacao_mediana_horas` (22 vazios).
- **A2:** `data/amostra2/dataset_dora.csv`, mesmo formato, entra no `main` quando a coleta terminar. Rode em **A1 (300)** e em **A1 + A2 (600)**.

Funções prontas: `analise.estatisticas.carregar`, `fatores(df)` (grupos e quartis usados hoje), `rq06(df)` (resultado univariado, para comparar).

## O que implementar (`analise/rq06_robustez.py`)

1. **Correlação entre os fatores:** Spearman entre `log10(estrelas)`, `log10(contribuidores)` e `idade_anos`. Mostra o tamanho do problema.
2. **Correlação parcial de Spearman:** de cada fator com cada métrica, controlando os outros dois fatores contínuos.
   - Implementação: transformar tudo em postos (`rank`), tirar o resíduo de uma regressão linear dos postos do fator e dos postos da métrica sobre os postos dos controles, e correlacionar os resíduos (Pearson nos resíduos de postos).
   - Não use bibliotecas fora da lista permitida (o pingouin não está nela).
   - p-valor com t de n − 2 − k graus de liberdade; Holm sobre todos os testes.
3. **Regressão múltipla** (`statsmodels`):
   - Métricas contínuas e positivas: `np.log1p(métrica) ~ log10(estrelas) + log10(contribuidores) + idade_anos + C(linguagem)`.
   - Erros-padrão robustos `cov_type="HC3"`.
   - Reportar coeficiente, IC de 95%, p e **coeficientes padronizados** (variáveis em z-score), para comparar os fatores.
   - CFR (proporção com muitos zeros): fique na correlação parcial ou use logit fracionário (`sm.GLM(..., family=sm.families.Binomial())` com a proporção como resposta). Justifique a escolha no texto.
   - **Multicolinearidade:** VIF com `statsmodels.stats.outliers_influence.variance_inflation_factor` (VIF > 5 é preocupante).
   - **Diagnóstico de resíduos:** gráfico resíduo × ajustado e Q-Q, só para conferir, sem precisar ir para o artigo.
4. **Figura:** *forest plot* dos coeficientes padronizados com IC de 95%, uma linha por fator e um painel por métrica, A1 e A1 + A2 lado a lado.
5. **Artigo:** na seção da RQ06, a leitura controlada. Por exemplo: "a idade continua associada ao lead time controlando contribuidores e estrelas (β = …, IC …)?" Inclua a limitação de que é associação, não causalidade.

## Testes esperados (`tests/test_rq06_robustez.py`)

- Correlação parcial com dados sintéticos: o fator X causa Y e Z é confundidor (Z → X e Z → Y). A correlação simples de X com Y é alta, e a parcial controlando Z tem de cair perto do efeito real. E o contrário: X sem efeito nenhum dá parcial ≈ 0.
- Regressão com dados sintéticos de coeficiente conhecido recupera o coeficiente dentro do IC.
- VIF alto quando dois fatores são quase iguais.

## Pronto quando

- [ ] Análise reexecutável com um comando, A1 e A1 + A2 (`#141 ...`)
- [ ] Tabela e figura em `analise/saida/`
- [ ] Texto da RQ06 controlada no artigo
- [ ] PR a partir do `main` mergeado
