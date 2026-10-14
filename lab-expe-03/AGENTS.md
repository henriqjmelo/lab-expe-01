# Guia do Lab03 para assistentes de IA

Leia este arquivo inteiro antes de mexer em qualquer coisa em `lab-expe-03/`. Depois leia o documento da sua issue em `docs/issues/` (veja a tabela no fim). Os dois juntos têm o contexto necessário para trabalhar **sem refazer a coleta e sem depender do computador de outro integrante**.

## 1. O que é este laboratório

Lab03 da disciplina **Laboratório de Experimentação de Software** (Engenharia de Software, 6º período, prof. Danilo Maia). O enunciado completo está em `ENUNCIADO.md`; leia as seções citadas na sua issue.

O grupo **minera as métricas DORA** de repositórios open-source populares que usam GitHub Actions:

| Métrica | Proxy usado (o GitHub não registra "deploy" nem "falha em produção") |
| :--- | :--- |
| Deployment frequency | releases publicadas na janela ÷ semanas (~52,1) |
| Lead time for changes | (a) release − commit mais antigo da release; (b) release − cada commit (mediana) |
| Change failure rate | (a) falhas de CI ÷ runs válidos; (b) releases seguidas de release corretiva em ≤ 7 dias |
| Tempo de recuperação | episódios de falha por workflow: 1ª falha após sucesso → próximo sucesso |

Além de calcular as métricas, o trabalho testa **o quanto elas são confiáveis**: validação manual (amostra-ouro), sensibilidade à definição (RQ07) e comparação entre amostras independentes.

- **Janela de observação:** 01/10/2025 a 30/09/2026, inclusive (`config.yaml`).
- **Critério de inclusão:** ≥ 5 releases publicadas (sem pré-release) e ≥ 50 workflow runs válidos (push no default branch) na janela.

## 2. Integrantes e issues

| Integrante | GitHub | Issues |
| :--- | :--- | :--- |
| Guilherme Costa | `guicostak` | #139 (dataset), #142 (RQ07/RQ08 rework), #145, #151 (relatório), #154–#157 |
| Henrique Jardim Melo | `henriqjmelo` | #137 (amostra-ouro, S02), #140 (caracterização da amostra, S03), #143 |
| Gabriel Afonso | `Gabriel200481` | #138 (heurística corretiva, S02), #141 (robustez RQ06, S03), #158 (RQ08 temporal, S03), #144 |

Regra de avaliação do enunciado: **em toda sprint, cada integrante precisa ter commits de código em pelo menos uma issue própria**, senão a parcela individual da sprint zera.

## 3. Estrutura do código

```
lab-expe-03/
  config.yaml              janela, filtros, alvo (amostra 1)
  config-amostra2.yaml     amostra 2 (outra semente, exclui a amostra 1)
  pipeline/                coleta (REST/GraphQL próprio, sem PyGithub)
    github_client.py       cliente HTTP: cache, rate limit, retentativas
    cache.py               cache em disco (só existe na máquina de quem coletou)
    selecao.py             busca de candidatos, filtros, funil
    coleta_releases.py     releases, tags, compare
    coleta_runs.py         workflow runs mês a mês
    repositorio.py         métricas por unidade de deploy
    executar.py            comando único: python -m pipeline --config config.yaml
    exportar.py            exporta do cache os eventos por repositório (data/eventos/)
  metricas/                funções puras de cálculo, testadas (cobertura >= 80% no CI)
    frequencia.py  lead_time.py  cfr.py  recuperacao.py  dora.py
  analise/                 estatísticas e figuras: python -m analise
    estatisticas.py        resumo, classificação DORA, RQ05, RQ06, RQ07, comparação de amostras
    graficos.py            estilo e figuras (paleta validada para daltonismo)
    saida/figuras/  saida/tabelas/
  data/                    datasets (ver data/DICIONARIO.md)
  artigo/                  seções do artigo em Markdown (02-metodologia.md, 03-resultados.md)
  tests/                   pytest
```

## 4. Dados disponíveis no repositório (não precisa coletar nada)

Todos os dados abaixo estão versionados no Git. **Não rode `python -m pipeline`**: a coleta completa leva ~15 h e gasta a cota de API do seu token. O cache da coleta (`.cache/`, vários GB) **não** vai para o Git.

| Arquivo | Conteúdo |
| :--- | :--- |
| `data/dataset_dora.csv` | **Amostra 1 (A1)**, 300 repositórios: uma linha por repositório com metadados e todas as métricas e variantes |
| `data/funil.csv`, `data/descartes.csv` | funil de seleção da A1 e cada candidato descartado com o motivo |
| `data/candidatos.csv` | metadados dos **8.457 candidatos** da busca (estrelas, linguagem, criação...) |
| `data/eventos/releases.csv` | todas as releases publicadas dos repositórios da A1 (com `na_janela`) |
| `data/eventos/lead_time_releases.csv` | lead time (a) e (b) de cada release da janela |
| `data/eventos/commits_releases.csv.gz` | cada commit de cada release da janela: SHA, data, 1ª linha da mensagem, SHA revertido |
| `data/eventos/runs.csv.gz` | cada workflow run da janela (workflow, conclusão, classe, início, fim) |
| `data/amostra2/...` | **Amostra 2 (A2)**: mesmos arquivos; entram no `main` quando a coleta da A2 terminar |

Colunas: `data/DICIONARIO.md`. Para ler os `.csv.gz`: `pd.read_csv("data/eventos/runs.csv.gz")` (o pandas descomprime sozinho).

**Desenho amostral:** A1 = 300 (semente 42); A2 = 300 novos (semente 2026, excluindo a A1); futura A3 → 900. **Toda análise deve sair em paralelo: 300 (A1) × 600 (A1 + A2)**. Enquanto a A2 não estiver no `main`, faça tudo funcionar com a A1 e deixe a função pronta para receber vários datasets (ex.: `pd.concat([a1, a2])`).

## 5. Ambiente e comandos

```bash
cd lab-expe-03
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-analise.txt
python -m pytest --cov=metricas --cov-report=term-missing   # testes (o CI exige >= 80% em metricas)
python -m analise                                           # regenera figuras e tabelas da A1
```

Python 3.12. Bibliotecas de análise permitidas pelo enunciado: pandas, SciPy, statsmodels, scikit-learn, pymannkendall. **Proibido** usar bibliotecas prontas de acesso à API do GitHub (PyGithub etc.).

## 6. Convenções do grupo (siga à risca)

- **Commits:** mensagem no formato `#NN descrição em português no infinitivo/presente` (ex.: `#140 adiciona comparacao amostra x descartados`). **Commit sem número de issue não conta na avaliação.** Sem trailers de coautoria (ex.: `Co-Authored-By`): cada integrante assina os próprios commits.
- **Branch e PR:** branch própria a partir do `main` (ex.: `issue-140-caracterizacao`), PR referenciando a issue, sem misturar escopo de outras issues. Mova o cartão no Project (Backlog → In progress → In review → Done).
- **Código:** nomes em português (funções, variáveis, colunas), sem acentos nos identificadores. **Sem comentários nem docstrings** no código (decisão do grupo: o código deve se explicar pelos nomes; a explicação vai no artigo e nos docs).
- **Funções puras e testáveis:** cálculo em funções que recebem DataFrames ou listas e devolvem resultados; leitura de arquivos e gráficos separados. Teste com fixtures pequenas e casos de borda.
- **Estatística:** reportar **mediana e IQR**, nunca média e desvio. Testes não paramétricos. Muitos testes: corrigir por **Holm** (`statsmodels.stats.multitest.multipletests(method="holm")`). Sempre reportar **tamanho de efeito** (ε², delta de Cliff) além do p-valor.
- **Figuras:** reaproveite `analise/graficos.py` (`estilo()`, `cabecalho()`, `salvar()`, cores `SERIE` e `DORA_COR`, `fmt_num`/`fmt_pct` com vírgula decimal). Título que diga a conclusão, subtítulo que diga o que é cada ponto e o `n`. Salvar em `analise/saida/figuras/`.
- **Artigo:** texto em português, seção correspondente em `artigo/`, com um parágrafo "como ler" para cada figura.

## 7. O que NÃO fazer

- Não alterar `metricas/` nem `pipeline/` de outra issue sem combinar (outros dependem desses arquivos).
- Não recoletar dados nem commitar `.cache/`.
- Não mexer nos CSVs de `data/` à mão; eles são gerados por script.
- Não editar `artigo/02-metodologia.md` e `artigo/03-resultados.md` fora da sua seção.

## 8. Documentos por issue

| Issue | Responsável | Documento |
| :--- | :--- | :--- |
| #137 amostra-ouro e kappa de Fleiss (S02) | Henrique | `docs/issues/137-amostra-ouro.md` |
| #138 heurística de release corretiva e P/R/F1 (S02) | Gabriel | `docs/issues/138-heuristica-corretiva.md` |
| #140 caracterização da amostra e viés de seleção (S03) | Henrique | `docs/issues/140-caracterizacao-amostra.md` |
| #141 robustez da RQ06 (S03) | Gabriel | `docs/issues/141-rq06-robustez.md` |
| #158 RQ08 evolução temporal (S03) | Gabriel | `docs/issues/158-rq08-temporal.md` |

Sugestão de prompt inicial para a IA: *"Leia `lab-expe-03/AGENTS.md` e `lab-expe-03/docs/issues/<arquivo da issue>.md`, depois a issue #NN no GitHub. Proponha um plano e implemente seguindo as convenções do AGENTS.md."*
