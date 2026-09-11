# K4 — Detector de Rajada de Login

## Contexto

Um sistema de autenticação quer sinalizar usuários com padrão suspeito de login: muitas tentativas em um intervalo curto de tempo. É preciso varrer o histórico de eventos e apontar quem se encaixa nesse padrão.

## Assinatura

```python
def detectar_rajadas(eventos: list[tuple[str, int]], limite: int, janela_segundos: int) -> list[str]:
    ...
```

## Especificação

- `eventos`: lista de tuplas `(usuario, timestamp)`, em que `timestamp` é um inteiro representando segundos desde um marco de referência. A lista **não** vem necessariamente ordenada por timestamp.
- `limite`: número de logins que, se ultrapassado dentro da janela, caracteriza rajada.
- `janela_segundos`: tamanho da janela deslizante, em segundos, inclusive nas duas pontas.
- Retorna a lista de usuários (sem repetição) que tiveram, em algum momento, mais de `limite` logins com timestamps dentro de um intervalo de `janela_segundos` segundos.
- "Mais de `limite`" significa estritamente maior — se o usuário teve exatamente `limite` logins na janela, não é rajada.

## Regras e casos de borda

- A janela é contígua: um evento em `t` e outro em `t + janela_segundos` estão na mesma janela (a checagem é `fim - inicio <= janela_segundos`, não `<`).
- A ordem dos usuários na lista de saída é a ordem em que cada um **primeiro** ultrapassou o limite, considerando os eventos desse usuário ordenados por timestamp.
- Eventos de usuários diferentes não interagem entre si — a janela é sempre calculada dentro dos eventos do mesmo usuário.
- Se dois eventos do mesmo usuário têm o mesmo timestamp, contam como dois eventos distintos.
- Lista de eventos vazia retorna `[]`.
- `limite <= 0` levanta `ValueError`.
- Um usuário nunca aparece duas vezes na lista de saída, mesmo que ultrapasse o limite em mais de uma janela ao longo do histórico.

## Exemplo

```python
eventos = [
    ("ana", 0), ("ana", 5), ("ana", 8), ("ana", 40),
    ("bruno", 0), ("bruno", 100),
]
detectar_rajadas(eventos, limite=2, janela_segundos=10)
# ["ana"]
# ana teve 3 logins entre os segundos 0 e 8 (janela de 10s), o que é > 2.
# bruno teve no máximo 1 login em qualquer janela de 10s.
```
