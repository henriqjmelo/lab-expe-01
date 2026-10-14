# #138 — Heurística de release corretiva (CFR b): implementação, P/R/F1 e refinamento

- **Responsável:** Gabriel (`Gabriel200481`)
- **Sprint:** Lab03S02
- **Issue:** https://github.com/henriqjmelo/lab-expe-01/issues/138
- **Leia antes:** `lab-expe-03/AGENTS.md`, a seção 4 / RQ 03 de `lab-expe-03/ENUNCIADO.md` e `metricas/cfr.py`

## Por que esta issue existe

O **CFR (b), proxy de entrega**, diz que uma release R falhou se for seguida, em até 7 dias, por uma **release corretiva**. Tudo depende de reconhecer o que é "corretiva". Hoje o pipeline usa uma heurística provisória, a **v0** (`corretiva_semver_patch` em `metricas/cfr.py`): é corretiva se mantém o `maior.menor` da release anterior e sobe só o patch.

A v0 provavelmente **exagera** o CFR (b):
- mediana de 25% na amostra 1, contra 5,6% do CFR (a);
- correlação forte e parcialmente artificial com a frequência (ρ = 0,60 na RQ05).

Esta issue entrega uma heurística melhor e **validada contra o gabarito humano** da amostra-ouro (#137).

## O que já existe e deve ser reaproveitado

Em `metricas/cfr.py`:

```python
@dataclass
class Deploy:
    tag_name: str
    published_at: str

Heuristica = Callable[[Deploy, "Deploy | None"], bool]

def versao_semver(tag: str) -> tuple[int, int, int] | None
def corretiva_semver_patch(release: Deploy, anterior: Deploy | None) -> bool
def marcar_corretivas(deploys: list[Deploy], heuristica: Heuristica = corretiva_semver_patch) -> list[bool]
def cfr_entrega(deploys, inicio: str, fim: str, heuristica: Heuristica = corretiva_semver_patch) -> dict
```

`cfr_entrega` já recebe a heurística como parâmetro: **não é preciso mexer no pipeline**. Uma heurística que use as mensagens dos commits pode ser montada como closure, por exemplo:

```python
def corretiva_v1(mensagens_por_tag: dict[str, list[str]]) -> Heuristica:
    def heuristica(release: Deploy, anterior: Deploy | None) -> bool:
        ...
    return heuristica
```

## Dados disponíveis (no Git, sem coletar nada)

| Arquivo | Uso |
| :--- | :--- |
| `data/eventos/releases.csv` | `owner, repo, tag_name, published_at, prerelease, na_janela` (todas as releases publicadas da A1) |
| `data/eventos/commits_releases.csv.gz` | `owner, repo, tag_name, sha, data, mensagem` (1ª linha), `reverte_sha`: commits de cada release da janela desde a anterior |
| `validacao/consenso_releases.csv` | gabarito `full_name, tag_name, corretiva` (sim/não), gerado pela **#137**; necessário só para a etapa de avaliação |

Na amostra 1 há 615.555 commits de releases e 1.941 commits de revert com o SHA revertido identificado.

## O que implementar

1. **`metricas/corretiva.py`** com as versões da heurística, todas com a assinatura `Heuristica`. Sugestões de sinais para combinar:
   - SemVer: só o patch subiu (a v0);
   - mensagens dos commits da release: prefixos `fix:`, `hotfix`, `revert`, `Revert "`, `bugfix`, `patch`, e a proporção de commits de correção;
   - poucos commits (*hotfix* costuma ser pequeno);
   - nome da tag ou da release contendo `hotfix` ou `fix`.
2. **CFR (b) a partir dos eventos**: uma função `cfr_b_por_repositorio(releases, commits, heuristica)` que monta os `Deploy` de cada repositório (releases publicadas, sem pré-release, em ordem de `published_at`, incluindo as anteriores à janela), chama `cfr_entrega` com a janela 2025-10-01T00:00:00Z a 2026-10-01T00:00:00Z e devolve `owner, repo, cfr_b, n_avaliadas, n_censuradas, n_corretivas`.
   - **Confira:** com a v0, o resultado tem que bater com a coluna `cfr_b_release` de `data/dataset_dora.csv`. É um ótimo teste de regressão.
3. **Avaliação contra o gabarito** (quando o consenso da #137 existir):
   - `sklearn.metrics.precision_recall_fscore_support` com `corretiva = sim` como classe positiva, nas releases da amostra-ouro;
   - **F1 < 0,70 → refinar e reavaliar.** Cada versão testada (v0, v1, v2...) vai para `validacao/heuristica_versoes.md` com as regras, P, R, F1 e o motivo da mudança.
   - Cuidado com sobreajuste: são poucos exemplos (até 300 releases). Se fizer muitos ajustes, separe parte do gabarito para teste.
4. **Artigo:** substituir os `[PENDENTE]` da heurística em `artigo/02-metodologia.md` (seção 2.4) pela versão final, com a tabela de P/R/F1 por versão.

## Testes esperados (`tests/test_corretiva.py`)

- Cada versão com casos claros: `v1.2.0 → v1.2.1` com commit `fix:`, release só com `feat:`, tag fora do SemVer, primeira release (sem anterior).
- `cfr_b_por_repositorio` com a v0 reproduz `cfr_b_release` do dataset em uma fixture pequena (2 repositórios).
- Cobertura de `metricas/` continua ≥ 80%.

## Ordem sugerida (para não esperar ninguém)

1. Implementar as heurísticas e o `cfr_b_por_repositorio` agora, testando contra a v0 e contra o dataset.
2. Rodar as versões na A1 e ver como o CFR (b) muda, de forma descritiva.
3. Quando o consenso da #137 sair, avaliar P/R/F1 e escolher a versão final.

## Pronto quando

- [ ] Heurísticas e cálculo do CFR (b) a partir dos eventos, com testes (`#138 ...`)
- [ ] P/R/F1 por versão documentados; F1 ≥ 0,70 ou a justificativa de por que não foi possível
- [ ] Metodologia atualizada
- [ ] PR a partir do `main` mergeado
