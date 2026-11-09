# Lab04 — Testes de hipótese por dentro

**Par P5: Pearson × Spearman.** Cenário: o tamanho de uma classe (LOC) está associado ao
número de defeitos? Dados reais do **KC1 (NASA), nível de classe**, 145 classes.

| | |
| :--- | :--- |
| Dashboard | roda local com o comando único abaixo (publicação pendente, entrega final) |
| Repositório | <https://github.com/henriqjmelo/lab-expe-01> |
| GitHub Projects | <https://github.com/users/henriqjmelo/projects/1> |
| Enunciado | [`ENUNCIADO.md`](ENUNCIADO.md) |

## Comando único

```bash
cd lab-expe-04
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O `streamlit run app.py` é o comando único da entrega: ele calcula os parâmetros a partir dos
dados reais e desenha os gráficos na hora, sem depender de nenhum PNG gerado antes.

Python 3.12 ou superior (testado em 3.14.7). As versões das bibliotecas estão fixadas em
[`requirements.txt`](requirements.txt).

## Reprodutibilidade

Toda a aleatoriedade passa por `numpy.random.default_rng(SEED)` com **`SEED = 42`**, definida
em um lugar só, [`src/params.py`](src/params.py). As demais constantes do experimento ficam no
mesmo arquivo:

| Constante | Valor | O que é |
| :--- | :--- | :--- |
| `SEED` | 42 | semente de toda a simulação |
| `N_SIM` | 30 | observações por conjunto simulado (28 graus de liberdade) |
| `N_REP` | 10 000 | repetições por ponto das curvas de erro tipo I e de poder |
| `EFEITOS` | 0,0 … 0,5 | correlações latentes usadas na curva de poder |
| `ALFA` | 0,05 | nível de significância; `ALFA_EXTRA = 0,01` na análise extra |

Rodar duas vezes dá exatamente o mesmo resultado.

## Estrutura

```
lab-expe-04/
  app.py               dashboard Streamlit (comando único)
  requirements.txt     versões fixadas
  data/
    kc1_class.csv      dados reais: 145 classes
    README.md          fonte do dataset e como foi obtido
  src/
    params.py          constantes + parâmetros estimados dos dados reais
    estilo.py          cores e estilo compartilhados dos gráficos
    generate.py        gerador das situações A (normal) e B (lognormal)
    analysis.py        aplica Pearson e Spearman a um conjunto e interpreta
    simulate.py        motor vetorizado (10.000 × 30): erro tipo I e poder -> results/situacao_*.csv
    dados_reais.py     Pearson e Spearman nas 145 classes reais (seção 6)
    g1.py              G1: histogramas real × simulado
    graficos.py        G2: distribuição de t sob H₀, rejeição e p-valor; G4: curvas de poder
    dashboard_demo.py  bloco da seção 3: tabela dos dois testes no exemplo
  tests/               pytest do gerador, da análise, do motor e dos dados reais
  results/             PNGs (g1.png, g2.png, g3.png, g4.png) e CSVs da simulação (situacao_A.csv, situacao_B.csv)
  docs/
    oral.md            roteiro das 15 perguntas da apresentação, por integrante
```

## Scripts avulsos

Úteis para conferir um número sem abrir o dashboard:

```bash
python src/params.py      # resumo dos dados reais e os parâmetros da situação B
python src/g1.py          # grava results/g1.png
python src/graficos.py    # grava results/g2.png, g3.png e, se houver CSV de simulação, results/g4.png
python src/simulate.py    # simula A e B (10.000 repetições, seed 42) e grava results/situacao_*.csv
python src/simulate.py --situacao A    # só uma das situações
python src/dados_reais.py # Pearson e Spearman nas 145 classes reais
```

## Testes

```bash
python -m pytest tests -q
```

Cobrem o gerador das duas situações, a aplicação dos dois testes a um conjunto, o motor de simulação
(p-valores conferidos linha a linha contra `scipy.stats`) e os testes nos dados reais.

## Resultados da simulação (`results/situacao_*.csv`)

Uma linha por efeito (r latente) e por teste: 6 efeitos × 2 testes por situação. Colunas:
`situacao`, `r_latente`, `teste`, `n`, `repeticoes`, `rejeicoes_005`, `taxa_005`, `rejeicoes_001`,
`taxa_001` e `estatistica_media`. Com `r_latente = 0` a taxa é o **erro tipo I** (Q1); com
`r_latente > 0` é o **poder** (Q2). As taxas em α = 0,01 saem dos mesmos p-valores, para a análise extra.
O Spearman é igual nas situações A e B: `exp()` não muda a ordem dos valores, então os postos são os mesmos.

## O conjunto de exemplo da S01

O exemplo que aparece na seção 3 do dashboard e tem o p-valor marcado no G2 é **um só**,
definido em `analysis.gerar_exemplo()`: situação A, n = 30, correlação latente 0,3, semente 42.
Nele o Pearson rejeita H₀ (r = 0,374; p = 0,042) e o Spearman não (ρ = 0,247; p = 0,188) — é o
primeiro sinal de que a escolha do teste muda a conclusão.

## As duas situações simuladas

| Situação | Como os dados são gerados | Para que serve |
| :--- | :--- | :--- |
| **A** | pressupostos em ordem, dados bem comportados | referência: os dois testes deveriam ir bem |
| **B** | marginais lognormais estimadas do log das 145 classes reais | viola a normalidade do Pearson (Q3) |

A situação B herda a assimetria dos dados reais (3,40 em LOC e 5,53 em defeitos). A limitação
conhecida: 85 das 145 classes reais não têm defeito algum, e a lognormal nunca gera zero — está
registrado em `src/params.py` (`JUSTIFICATIVA`) e na seção 2 do dashboard.

## Estado por sprint

| Sprint | Entrega | Issues |
| :--- | :--- | :--- |
| S01 | dados reais, cenário, gerador, 2 testes em 1 conjunto, G1 e G2, dashboard seções 1–3 | #184–#191 (concluída) |
| S02 | Q1, Q2 e Q3, G3 e G4, dashboard seções 4 e 5 | #192–#198 |
| Final | dashboard seções 6 e 7, revisão, roteiro oral | #199–#204 |

## Convenções

- Commits no formato `#NN descrição`; **commit sem número de issue não conta na avaliação**.
- Branch própria por issue e Pull Request referenciando a issue.
- Cartão movido no Projects: Backlog → In progress → In review → Done.
