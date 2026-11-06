# Dados reais: KC1 em nível de classe

Arquivo: [`kc1_class.csv`](kc1_class.csv) — 145 classes, 8 colunas, sem valores faltantes.

## Fonte

| Item | Valor |
| :--- | :--- |
| Dataset | KC1 (NASA), versão em nível de classe |
| Origem original | Koru & Liu (2005), repositório PROMISE/NASA |
| Cópia usada | [eduardomioto/r-sandbox, `example-2/example2.csv`](https://github.com/eduardomioto/r-sandbox/blob/64a9bbbd19a06ca9e4622f44a59c7b444d6f62a7/example-2/example2.csv) (commit `64a9bbb`) |
| Descrição do dataset | [OpenML 1070 (KC1 class-level)](https://api.openml.org/d/1070/json) |
| Repositório PROMISE | <http://promise.site.uottawa.ca/SERepository/datasets-page.html> |

**Atenção à origem.** O CSV veio de uma cópia pública no GitHub, não de um repositório oficial. O grupo identificou o KC1 pelas colunas e pelo tamanho (145 classes), conferindo com a descrição do OpenML. A citação acadêmica é Koru & Liu (2005).

## Como foi obtido

```bash
curl -L -o data/kc1_class.csv \
  https://raw.githubusercontent.com/eduardomioto/r-sandbox/64a9bbbd19a06ca9e4622f44a59c7b444d6f62a7/example-2/example2.csv
```

O arquivo foi salvo sem nenhuma alteração. A URL fixa o commit da cópia para que o download seja reprodutível.

## Colunas

| Coluna | Significado | Uso no Lab04 |
| :--- | :--- | :--- |
| `sumLOC_TOTAL` | Linhas de código da classe (tamanho) | **Variável 1** (LOC) |
| `NUMDEFECTS` | Número de defeitos da classe | **Variável 2** (defeitos) |
| `COUPLING_BETWEEN_OBJECTS`, `DEPTH_INHERITANCE`, `LACK_OF_COHESION_OF_METHODS`, `FAN_IN`, `RESPONSE_FOR_CLASS`, `WEIGHTED_METHODS_PER_CLASS` | Métricas CK | Não usadas |

## Por que nível de classe

O KC1 por módulo só traz defeito sim/não. O enunciado pede a contagem de defeitos (par P5), e só a versão por classe tem essa contagem.

## Características relevantes para a simulação

Calculadas por `src/params.py` (rode `python src/params.py` para reproduzir).

| Característica | Valor |
| :--- | :--- |
| Classes | 145 |
| Mediana de LOC | 162 |
| Assimetria | 3,40 (LOC) e 5,53 (defeitos) |
| Classes sem defeito | 85 de 145 (58,6%) |
| Correlação (n = 145) | Pearson 0,690 e Spearman 0,573, ambos com p < 0,001 |
