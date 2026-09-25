# K2 — Verificador de Senha Corporativa

## Contexto

O setor de TI de uma empresa define regras próprias para senha, diferentes das regras genéricas de mercado. É preciso validar uma senha contra essas regras e reportar exatamente quais foram violadas.

## Assinatura

```python
def validar_senha(senha: str) -> tuple[bool, list[str]]:
    ...
```

## Especificação

Retorna uma tupla `(valida, violacoes)`, em que `valida` é `True` somente se `violacoes` for uma lista vazia.

Regras, cada uma associada a um código de violação (usar exatamente esses códigos na lista de violações, uma entrada por regra violada, na ordem abaixo):

| Código | Regra |
| :--- | :--- |
| `"tamanho"` | Precisa ter no mínimo 10 caracteres. |
| `"maiuscula"` | Precisa ter ao menos 1 letra maiúscula. |
| `"minuscula"` | Precisa ter ao menos 1 letra minúscula. |
| `"digito"` | Precisa ter ao menos 1 dígito. |
| `"especial"` | Precisa ter ao menos 1 caractere do conjunto `!@#$%&*` |
| `"repeticao"` | Não pode ter 3 ou mais caracteres idênticos consecutivos (ex.: `"aaa"`, `"111"`). |
| `"palavra_senha"` | Não pode conter a substring `"senha"`, ignorando maiúsculas/minúsculas. |

## Regras e casos de borda

- Todas as regras são checadas de forma independente — uma senha pode violar várias ao mesmo tempo, e todas as violadas devem aparecer na lista, na ordem da tabela acima.
- String vazia viola `"tamanho"`, `"maiuscula"`, `"minuscula"`, `"digito"` e `"especial"` (mas não `"repeticao"` nem `"palavra_senha"`, já que não há caractere nenhum pra violar essas duas).
- A regra de repetição olha caracteres consecutivos, não a contagem total. `"aabaa"` não viola `"repeticao"` (nenhum trecho de 3 iguais seguidos), mas `"aaab"` viola.
- Exatamente 10 caracteres já satisfaz `"tamanho"` (a regra é "no mínimo").

## Exemplo

```python
validar_senha("abc")
# (False, ["tamanho", "maiuscula", "digito", "especial"])

validar_senha("Senha1234!")
# (False, ["palavra_senha"])

validar_senha("Corp2024!Xz")
# (True, [])
```
