# K5 — Compactador de Texto por Repetição

## Contexto

Um sistema de log interno quer compactar mensagens com muita repetição de caractere (ex.: barras de progresso, separadores) sem usar uma lib de compressão de propósito geral.

## Assinatura

```python
def compactar(texto: str) -> str:
    ...

def descompactar(codigo: str) -> str:
    ...
```

## Especificação

- `texto` contém apenas letras minúsculas do alfabeto (`a` a `z`). Nunca contém dígitos, espaços ou outros símbolos.
- Uma sequência de **3 ou mais** ocorrências consecutivas do mesmo caractere é substituída por `<caractere><contagem>` (contagem em decimal, sem zeros à esquerda).
- Sequências de 1 ou 2 ocorrências consecutivas permanecem literais, sem qualquer alteração.
- `descompactar` deve reverter exatamente o que `compactar` produz: `descompactar(compactar(x)) == x` para qualquer `x` válido.

## Regras e casos de borda

- String vazia: `compactar("")` retorna `""`.
- Um único caractere (`"a"`) permanece `"a"` (sequência de tamanho 1, não compacta).
- Sequência de exatamente 3 já compacta: `"aaa"` vira `"a3"`.
- Uma contagem pode ter mais de um dígito: 15 `"b"` seguidos vira `"b15"`.
- Se `texto` contiver qualquer caractere fora de `a-z` (dígito, maiúscula, espaço, símbolo), `compactar` levanta `ValueError`.
- `descompactar` só recebe entradas produzidas por `compactar` — não precisa validar formato malformado.

## Exemplo

```python
compactar("aaaabbbcc")
# "a4b3cc"
# "aaaa" (4x) vira "a4"; "bbb" (3x) vira "b3"; "cc" (2x) fica literal por ser sequência de 2.

descompactar("a4b3cc")
# "aaaabbbcc"
```
