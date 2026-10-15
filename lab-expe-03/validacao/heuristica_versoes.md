# Versões da heurística de release corretiva (issue #138)

Histórico das versões testadas, com a comparação descritiva na amostra 1 (300 repositórios). A avaliação por precisão, recall e F1 contra o gabarito humano depende de `validacao/consenso_releases.csv` (issue #137), que ainda não existe. Quando existir, esta tabela ganha as colunas de P/R/F1 e a versão final é escolhida por F1 (mínimo 0,70).

Gerado por `python -m validacao.comparar_versoes`, a partir de `data/eventos/releases.csv` e `data/eventos/commits_releases.csv.gz`. Implementação em `metricas/corretiva.py`.

## Versões

| Versão | Regra | Motivo |
| :--- | :--- | :--- |
| **v0** `v0_semver_patch` | A versão SemVer da release mantém `maior.menor` da release anterior e sobe só o `patch` (ex.: `2.3.0 → 2.3.1`). | Heurística original do pipeline (#136), só olha o número da versão. |
| **v1** `v1_mensagens` | Pelo menos metade dos commits da release tem prefixo Conventional Commits `fix:` ou é um `Revert "..."` (`metricas.fluxo.tipo_commit`). | Usa o conteúdo da release, não só o número; evita falso positivo de quem sobe o patch por rotina (ex.: dependência). |
| **v2** `v2_patch_poucos_commits` | v0 **e** a release tem no máximo 3 commits. | Uma correção de verdade costuma ser pequena e focada; filtra patches "grandes" que a v0 sozinha marcaria. |
| **v3** `v3_combinada` | v0 **ou** v1 **ou** o nome da tag contém `hotfix`/`patch`. | Reúne os três sinais; é a mais permissiva (maior recall esperado, mas também mais falso positivo). |

## Comparação descritiva, amostra 1 (300 repositórios)

| Versão | Repositórios com CFR (b) calculável | Mediana | Q1 | Q3 | Releases marcadas corretivas |
| :--- | :---: | :---: | :---: | :---: | :---: |
| v0_semver_patch | 300 | 25,00% | 5,19% | 56,47% | 8.186 |
| v1_mensagens | 300 | 0,00% | 0,00% | 12,64% | 1.479 |
| v2_patch_poucos_commits | 300 | 2,45% | 0,00% | 21,63% | 1.903 |
| v3_combinada | 300 | 25,00% | 6,04% | 57,20% | 8.597 |

CSV completo: `validacao/comparacao_versoes.csv`.

**Leitura.** v0 e v3 ficam coladas (v3 ⊇ v0, já que v0 é uma das condições do "ou"), as duas bem acima do CFR (a) por CI (mediana 2,6%, RQ 03a). v1, que exige sinal na mensagem do commit, é a mais conservadora: mediana zero quer dizer que mais da metade dos repositórios não tem nenhuma release com metade ou mais dos commits marcados como correção. v2 fica no meio, porque herda o filtro de SemVer da v0 mas descarta releases "grandes".

Isso por si só não diz qual versão está certa: diz que as quatro discordam bastante entre si, o que reforça por que a validação contra o gabarito humano da #137 é necessária antes de fechar a heurística final.

## Próximo passo

Quando `validacao/consenso_releases.csv` existir: rodar `precision_recall_fscore_support` de cada versão contra o consenso, escolher a de maior F1 (mínimo 0,70; se nenhuma alcançar, documentar a melhor e a justificativa), atualizar `metricas/cfr.py`/o pipeline para usar a versão escolhida e preencher a tabela pendente em `artigo/02-metodologia.md` (seção 2.4).
