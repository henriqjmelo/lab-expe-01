# #140 — Caracterização da amostra e viés de seleção

- **Responsável:** Henrique (`henriqjmelo`)
- **Sprint:** Lab03S03
- **Issue:** https://github.com/henriqjmelo/lab-expe-01/issues/140 (escopo redefinido em 14/10; o original entrou no #152)
- **Leia antes:** `lab-expe-03/AGENTS.md`, `artigo/02-metodologia.md` (seção 2.3, funil) e `data/DICIONARIO.md`

## Por que esta issue existe

O artigo precisa responder a duas perguntas de **validade externa**:
1. **Quem são os 300 (depois 600) repositórios estudados?** É a caracterização da amostra.
2. **A seleção enviesou o resultado?** Quem passou nos filtros (Actions, ≥ 5 releases, ≥ 50 runs) é diferente de quem foi descartado? A amostra 1 é parecida com a amostra 2?

Já se sabe que o filtro de releases é o mais restritivo: 57% dos repositórios com Actions caíram nele. Se os descartados forem, por exemplo, sistematicamente mais antigos ou de certas linguagens, as conclusões das RQs só valem para "projetos que publicam releases", e isso precisa estar no artigo.

## Dados disponíveis (no Git, sem coletar nada)

| Arquivo | Conteúdo |
| :--- | :--- |
| `data/candidatos.csv` | **8.457 candidatos** da busca: `full_name, owner, repo, estrelas, linguagem, default_branch, criado_em` |
| `data/dataset_dora.csv` | os **300 aceitos** da A1, com metadados (inclusive `contribuidores` e `idade_anos`) e métricas |
| `data/descartes.csv` | os **808 descartados** da A1: `full_name, etapa, motivo, detalhe`. Etapas: `com_actions` (171), `min_5_releases` (538), `min_50_runs` (99) |
| `data/funil.csv` | contagens do funil |
| `data/amostra2/*` | os mesmos arquivos da A2 (chegam ao `main` quando a coleta terminar; deixe o código pronto para recebê-los) |

Situação de cada candidato na A1:
- **aceito**, se está em `dataset_dora.csv`;
- **descartado**, se está em `descartes.csv`, com a etapa;
- **não avaliado**, nos demais 7.349. A avaliação parou quando a amostra chegou a 300. Como a ordem de avaliação foi **aleatória** (semente 42), os não avaliados devem ser estatisticamente parecidos com os avaliados: é um bom **teste de sanidade** do sorteio.

Idade: `(2026-09-30 − criado_em)` em anos, igual ao `idade_anos` do dataset (`pipeline.executar.idade_anos`). Os candidatos não têm `contribuidores` (só foi coletado para os aceitos): compare **estrelas, idade e linguagem**.

## O que implementar (`analise/caracterizacao.py`)

1. `situacao_candidatos(candidatos, aceitos, descartes) -> DataFrame` com a coluna `situacao` ∈ {`aceito`, `descartado_<etapa>`, `nao_avaliado`}.
2. **Caracterização da amostra:** tabela com mediana e IQR de estrelas, idade e contribuidores, e a distribuição por linguagem (top 8 + "Outras"), para A1 e para A1 + A2.
3. **Viés de seleção:**
   - aceitos × descartados (cada etapa separada e todos juntos): **Mann-Whitney + delta de Cliff** para estrelas e idade, **qui-quadrado** para a linguagem (top 8 + Outras), com p corrigido por **Holm**;
   - avaliados × não avaliados (sanidade do sorteio): mesmos testes;
   - padrões do projeto: `scipy.stats.mannwhitneyu`, Cliff δ = 2·U₁/(n₁·n₂) − 1, referência |δ| < 0,147 desprezível, < 0,33 pequeno, < 0,474 médio. Veja `analise.estatisticas.mann_whitney_amostras`, que já faz esse cálculo para as métricas.
4. **A1 × A2:** os mesmos testes nos metadados das duas amostras (são independentes).
5. **Figuras** (reaproveite o estilo de `analise/graficos.py`):
   - curvas acumuladas de estrelas e idade: aceitos × cada etapa de descarte;
   - barras de linguagem em %: aceitos × descartados.
6. **Artigo:**
   - parágrafo de caracterização em `artigo/02-metodologia.md` (seção 2.6, "Dataset");
   - item "viés de seleção" em ameaças à validade (externa).

## Testes esperados (`tests/test_caracterizacao.py`)

- `situacao_candidatos` com fixture de 5 candidatos cobrindo as três situações.
- Comparação com dois grupos sintéticos claramente diferentes → p pequeno e |δ| grande; grupos iguais → δ ≈ 0.
- Correção de Holm aplicada sobre o conjunto de testes.

## Pronto quando

- [ ] Script reexecutável com um comando, para A1 e A1 + A2 (`#140 ...`)
- [ ] Tabelas e figuras em `analise/saida/`
- [ ] Textos de caracterização e de viés de seleção no artigo
- [ ] PR a partir do `main` mergeado
