# K1 — Turno de Atendimento

## Contexto

Uma central de atendimento recebe uma fila de chamados e precisa distribuí-los entre os atendentes disponíveis, em ordem, respeitando um limite de chamados por atendente.

## Assinatura

```python
def distribuir_chamados(chamados: list[str], atendentes: list[str], capacidade: int) -> dict[str, list[str]]:
    ...
```

## Especificação

- `chamados`: lista de IDs de chamado, na ordem em que chegaram.
- `atendentes`: lista de nomes de atendentes, na ordem em que devem receber chamados.
- `capacidade`: número máximo de chamados que cada atendente pode receber.
- A distribuição é round-robin: o 1º chamado vai para o 1º atendente, o 2º chamado para o 2º atendente, e assim por diante, voltando ao início da lista de atendentes quando ela acabar — mas pulando qualquer atendente que já tenha atingido a capacidade.
- Retorna um dicionário `{atendente: [chamados atribuídos, em ordem]}`. Todo atendente de `atendentes` deve aparecer no dicionário, mesmo que receba zero chamados (lista vazia).

## Regras e casos de borda

- Se a soma das capacidades (`capacidade * len(atendentes)`) for menor que `len(chamados)`, levantar `ValueError` com mensagem contendo `"capacidade insuficiente"`.
- Se `atendentes` for uma lista vazia e `chamados` também for vazia, retornar `{}`.
- Se `atendentes` for uma lista vazia e `chamados` não for vazia, levantar `ValueError` (capacidade insuficiente, mesma regra acima).
- Se `chamados` for uma lista vazia, retornar o dicionário com todos os atendentes e listas vazias.
- Se `capacidade <= 0`, levantar `ValueError` com mensagem contendo `"capacidade"`.
- IDs de chamado podem se repetir na entrada (chamados reabertos) — tratar cada ocorrência como um chamado distinto a distribuir.

## Exemplo

```python
distribuir_chamados(["c1", "c2", "c3", "c4"], ["ana", "bruno"], 2)
# {"ana": ["c1", "c3"], "bruno": ["c2", "c4"]}
```
