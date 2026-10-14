# #137 — Amostra-ouro: sorteio, planilha de rotulagem, kappa de Fleiss e consenso

- **Responsável:** Henrique (`henriqjmelo`)
- **Sprint:** Lab03S02
- **Issue:** https://github.com/henriqjmelo/lab-expe-01/issues/137
- **Leia antes:** `lab-expe-03/AGENTS.md` e a seção 6 ("Validação manual (amostra-ouro)") de `lab-expe-03/ENUNCIADO.md`

## Por que esta issue existe

As métricas DORA aqui são proxies. A amostra-ouro mede o quanto esses proxies concordam com o **julgamento humano**: três pessoas rotulam, de forma independente, os mesmos 60 repositórios, e o grupo mede a concordância (kappa de Fleiss). O consenso desses rótulos vira o **gabarito** com que a heurística de release corretiva da #138 (Gabriel) é avaliada (precisão, recall e F1). É o principal argumento de validade de construto do artigo.

## Regra do sorteio (já fixada na issue, não mude)

Para ninguém ficar esperando, a regra foi fixada em comentário na issue em 14/10. Os três geram a mesma lista sozinhos:

```python
import random
import pandas as pd

repos = pd.read_csv("data/dataset_dora.csv")
ouro = repos.sample(n=60, random_state=42)

releases = pd.read_csv("data/eventos/releases.csv")
elegiveis = releases[releases["na_janela"] & ~releases["prerelease"]].sort_values("published_at")

def releases_sorteadas(owner, repo):
    lista = elegiveis[(elegiveis.owner == owner) & (elegiveis.repo == repo)]["tag_name"].tolist()
    return lista if len(lista) <= 5 else random.Random(42).sample(lista, 5)
```

- Base: **amostra 1** (`data/dataset_dora.csv`, 300 repositórios), lida sem reordenar o CSV.
- Dimensão (iii): 5 releases por repositório, ou todas se houver menos de 5. Um `random.Random(42)` **novo por repositório**.
- O resultado tem 60 repositórios e até 300 releases.

## O que implementar

1. **Sorteio e planilhas** (`analise/amostra_ouro.py`), gerando arquivos versionados em `validacao/`:
   - `validacao/amostra_ouro_repos.csv`: `full_name, url, linguagem, estrelas` (url = `https://github.com/<owner>/<repo>`)
   - `validacao/amostra_ouro_releases.csv`: `full_name, tag_name, published_at, url` (url = `https://github.com/<owner>/<repo>/releases/tag/<tag>`)
   - modelos vazios para cada pessoa preencher: `validacao/modelo_rotulos_repos.csv` e `validacao/modelo_rotulos_releases.csv`.
2. **Formato dos rótulos.** Cada integrante preenche os próprios arquivos **sem olhar os dos outros nem a saída da heurística**:
   - `validacao/rotulos_<nome>_repos.csv`: `full_name, tipo_projeto, releases_reais`
     - `tipo_projeto` ∈ {`biblioteca_framework`, `aplicacao_servico`, `ferramenta_cli`, `outro`}
     - `releases_reais` ∈ {`sim`, `nao`, `incerto`} (as releases representam entregas reais ao usuário?)
   - `validacao/rotulos_<nome>_releases.csv`: `full_name, tag_name, corretiva` com `corretiva` ∈ {`sim`, `nao`}
   - `<nome>` ∈ {`henrique`, `gabriel`, `guilherme`}
   - Publique o formato no comentário da issue assim que fechar, porque os outros dois vão rotular em paralelo.
3. **Concordância** (`analise/concordancia.py`):
   - kappa de Fleiss **por dimensão**, com `statsmodels.stats.inter_rater.aggregate_raters` + `fleiss_kappa`;
   - interpretação de Landis & Koch (1977): ≤ 0,20 leve, 0,21–0,40 razoável, 0,41–0,60 moderada, 0,61–0,80 substancial, 0,81–1 quase perfeita;
   - a função recebe os DataFrames dos três avaliadores e devolve uma tabela `dimensao, n_itens, kappa, interpretacao`.
4. **Consenso** (no mesmo módulo):
   - **protocolo de desempate**: maioria de 2 em 3; com três rótulos diferentes (só possível em `tipo_projeto`), o caso vai para discussão e a decisão fica registrada com a justificativa;
   - gera `validacao/consenso_repos.csv` e `validacao/consenso_releases.csv`;
   - registra o protocolo em `validacao/PROTOCOLO.md`.
5. **Artigo:** subseção "Validação manual" em `artigo/02-metodologia.md` (substituir os marcadores `[PENDENTE]` da #137) com o κ por dimensão.

## Testes esperados (`tests/test_concordancia.py`, `tests/test_amostra_ouro.py`)

- O sorteio é reprodutível (mesma lista em duas chamadas) e devolve 60 repositórios com no máximo 5 releases cada.
- Fleiss com concordância total → κ = 1; com rótulos aleatórios → κ ≈ 0. Comparar com um exemplo pequeno calculado à mão.
- Consenso: casos 2 × 1 e 3 × 0 resolvidos pela maioria; o caso de três rótulos diferentes é sinalizado para discussão.

## Cuidados

- **A IA não deve rotular nada.** Os rótulos são julgamento humano independente: rótulo gerado por IA invalida a medida de concordância.
- Não use a amostra 2 para a amostra-ouro: a base é a A1, como fixado.
- O consenso de releases é a entrada da #138: mantenha as colunas `full_name, tag_name, corretiva`.

## Pronto quando

- [ ] Script do sorteio e planilhas commitados (`#137 ...`)
- [ ] Três arquivos de rótulos recebidos, κ calculado e consenso gerado por script
- [ ] Texto da validação manual na Metodologia
- [ ] PR a partir do `main` mergeado
