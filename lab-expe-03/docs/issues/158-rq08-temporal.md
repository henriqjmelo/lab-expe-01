# #158 — RQ08 (bônus): evolução temporal das métricas e Mann-Kendall

- **Responsável:** Gabriel (`Gabriel200481`)
- **Sprint:** Lab03S03
- **Issue:** https://github.com/henriqjmelo/lab-expe-01/issues/158
- **Leia antes:** `lab-expe-03/AGENTS.md` e a RQ 08 em `lab-expe-03/ENUNCIADO.md` ("Evolução temporal")

## Por que esta issue existe

O enunciado oferece duas opções para o bônus da RQ08. A **rework rate** fica na #142 (Guilherme); **esta issue faz a evolução temporal**, de forma independente: os repositórios estão melhorando ou piorando nas métricas DORA ao longo dos 12 meses da janela?

## ⚠ Armadilha estatística: decida isso primeiro

O enunciado sugere métricas **por trimestre** com o teste de **Mann-Kendall**. Com só **4 pontos** por série, o Mann-Kendall **não consegue dar p < 0,05 nunca**: o menor p-valor bilateral possível com n = 4 é **≈ 0,089**, mesmo com a série perfeitamente monótona (S = 6, Var(S) = 8,67, z = 1,70).

Recomendação:
- **Análise principal com série mensal** (12 pontos), em que o teste tem poder.
- A versão **trimestral** fica como descritiva, nas figuras das medianas por trimestre, citando essa limitação no texto. Isso é justamente um bom ponto de discussão metodológica para o artigo.

## Dados disponíveis (no Git, sem coletar nada)

| Arquivo | Uso |
| :--- | :--- |
| `data/eventos/releases.csv` | `owner, repo, tag_name, published_at, prerelease, na_janela` → frequência por período (use `~prerelease`) |
| `data/eventos/lead_time_releases.csv` | `owner, repo, tag_name, published_at, n_commits, lt_a_dias, lt_b_mediana_dias, ignorada` → lead time por período (pelo `published_at` da release) |
| `data/eventos/runs.csv.gz` | `owner, repo, workflow_id, conclusion, classe` (`sucesso`/`falha`/`ignorado`), `run_started_at, updated_at` → CFR (a) e recuperação por período |
| `data/dataset_dora.csv` | lista dos 300 repositórios da A1 e as métricas da janela inteira (para conferir) |
| `data/amostra2/eventos/*` | os mesmos arquivos da A2, quando a coleta terminar; rode em A1 e A1 + A2 |

**Teste de regressão útil:** agregando os 12 meses, os seus cálculos têm que bater com o dataset. O CFR (a) por repositório com a janela inteira é igual a `cfr_a`, e o número de releases é igual a `n_release`. Isso já foi verificado na exportação (bate 100%).

Janela: 2025-10-01T00:00:00Z ≤ data < 2026-10-01T00:00:00Z.
- Trimestres: out–dez/2025, jan–mar/2026, abr–jun/2026, jul–set/2026.
- Meses: 12, de out/2025 a set/2026.

## Funções prontas para reaproveitar

```python
from metricas.cfr import cfr_ci, classificar_conclusao
from metricas.recuperacao import Run, tempo_recuperacao
from metricas.frequencia import frequencia_semanal, na_janela, semanas_da_janela
```

- **Frequência por período:** releases no período ÷ semanas do período (`semanas_da_janela(inicio, fim)`).
- **Lead time (a) por período:** mediana de `lt_a_dias` das releases publicadas no período (ignore `ignorada = True`).
- **CFR (a) por período:** falhas ÷ (falhas + sucessos) dos runs com `run_started_at` no período.
- **Recuperação por período:** monte `Run(workflow_id, conclusion, run_started_at, updated_at)` e use `tempo_recuperacao`, atribuindo o episódio ao período em que ele **começou**. Documente a escolha.

## O que implementar (`analise/rq08_temporal.py`)

1. `series_por_periodo(eventos, periodo="M" | "Q") -> DataFrame` no formato longo: `owner, repo, metrica, periodo, valor`. Período sem dado fica vazio, não zero (exceto a frequência, em que zero releases é zero).
2. **Mann-Kendall por repositório × métrica** com `pymannkendall.original_test` (adicione `pymannkendall` ao `requirements-analise.txt`):
   - exigir um mínimo de pontos não vazios (por exemplo, ≥ 8 dos 12 meses), senão o caso é "dados insuficientes";
   - classificar em **melhora / piora / sem tendência**, lembrando que o sentido de "melhor" depende da métrica:
     - frequência ↑ é melhor;
     - lead time, CFR e recuperação ↓ são melhores.
3. **Correção de múltiplos testes:** são ~300 testes por métrica. Use **Benjamini-Hochberg (FDR)** por métrica (`multipletests(method="fdr_bh")`), porque o Holm fica conservador demais com tantos testes, e reporte o Holm também. Justifique no texto.
4. **Resultado principal:** % de repositórios com tendência significativa de melhora, de piora e sem tendência, por métrica, em A1 e A1 + A2.
5. **Figuras** (estilo de `analise/graficos.py`):
   - barras 100% empilhadas (melhora / sem tendência / piora / insuficiente) por métrica;
   - mediana entre repositórios por mês, com IQR sombreado, por métrica.
6. **Artigo:** subseção da RQ08 (evolução temporal) em `artigo/03-resultados.md`, com a limitação dos 4 trimestres explicada.

## Testes esperados (`tests/test_rq08_temporal.py`)

- Recorte por período nas fronteiras: um evento em 2025-12-31T23:59:59Z cai em dezembro / no 1º trimestre, e um em 2026-01-01T00:00:00Z cai em janeiro / no 2º trimestre.
- Séries sintéticas crescente, decrescente e constante → tendência certa, e "sem tendência" para a constante.
- O sentido de "melhora" invertido corretamente para lead time e CFR.
- Agregado da janela inteira = `cfr_a` e `n_release` do dataset, numa fixture pequena.

## Pronto quando

- [ ] Análise reexecutável com um comando, A1 e A1 + A2 (`#158 ...`)
- [ ] Tabelas e figuras em `analise/saida/`
- [ ] Texto da RQ08 temporal no artigo, com a limitação do Mann-Kendall com 4 pontos
- [ ] PR a partir do `main` mergeado
