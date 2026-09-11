# K6 — Divisor de Times por Afinidade

## Contexto

Um professor de educação física quer dividir a turma em dois times para um jogo, tentando equilibrar o nível técnico total de cada lado, usando uma nota de habilidade que já tem de cada aluno.

## Assinatura

```python
def dividir_times(jogadores: list[tuple[str, int]]) -> tuple[list[str], list[str]]:
    ...
```

## Especificação

- `jogadores`: lista de tuplas `(nome, habilidade)`, `habilidade` é um inteiro positivo.
- Retorna `(time_a, time_b)`, cada um uma lista de nomes.
- **Algoritmo obrigatório** (o resultado precisa ser exatamente este, não "qualquer divisão equilibrada"): ordene os jogadores por habilidade em ordem decrescente; em caso de empate de habilidade, mantenha a ordem em que apareceram em `jogadores`. Percorra a lista ordenada e distribua alternadamente, começando pelo time A: 1º jogador (maior habilidade) vai pro time A, 2º pro time B, 3º pro time A, 4º pro time B, e assim por diante.

## Regras e casos de borda

- Lista vazia retorna `([], [])`.
- Um jogador só: vai para o time A, time B fica `[]`.
- Número ímpar de jogadores: time A fica com um jogador a mais que o time B (porque a distribuição começa pelo time A e ele recebe as posições ímpares da lista ordenada).
- Nomes duplicados na entrada são permitidos e tratados como jogadores distintos (ex.: dois jogadores diferentes podem por coincidência se chamar "Ana" — ambos entram na distribuição normalmente).
- `habilidade` igual a zero é permitido e não é caso de erro.
- `habilidade` negativa levanta `ValueError`.

## Exemplo

```python
jogadores = [("ana", 10), ("bruno", 8), ("carla", 8), ("davi", 5), ("elis", 3)]
dividir_times(jogadores)
# ordenado por habilidade desc (empate mantém ordem original): ana(10), bruno(8), carla(8), davi(5), elis(3)
# distribuição alternada A,B,A,B,A:
# (["ana", "carla", "elis"], ["bruno", "davi"])
```
