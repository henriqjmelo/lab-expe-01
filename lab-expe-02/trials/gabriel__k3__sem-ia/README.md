# K3 — Consolidador de Notas Fiscais

## Contexto

Uma pequena loja registra cada venda como uma nota fiscal com categoria e valor. No fim do mês, é preciso somar o faturamento por categoria, desconsiderando notas canceladas.

## Assinatura

```python
def consolidar_notas(notas: list[dict]) -> dict[str, float]:
    ...
```

## Especificação

- Cada item de `notas` é um dicionário com as chaves `"categoria"` (str), `"valor"` (float) e `"cancelada"` (bool).
- Retorna um dicionário `{categoria: soma_dos_valores}`, somando apenas as notas com `"cancelada"` igual a `False`.
- Os valores somados devem ser arredondados para 2 casas decimais no resultado final (o arredondamento é só na soma final de cada categoria, não em cada nota individual antes de somar).
- Categorias que só têm notas canceladas, ou nenhuma nota, **não aparecem** no dicionário de saída — o dicionário só tem as categorias com soma maior que zero proveniente de notas válidas.

## Regras e casos de borda

- Lista vazia retorna `{}`.
- Se `"valor"` for negativo em qualquer nota não cancelada, levantar `ValueError` com mensagem contendo `"valor"`.
- Notas canceladas com valor negativo não devem levantar erro (já que são ignoradas antes de qualquer validação de valor).
- A ordem das categorias no dicionário de saída não importa para os testes.
- Duas notas podem ter a mesma categoria — os valores se somam.
- `"cancelada"` sempre vem como `bool` na entrada (não é preciso tratar strings tipo `"true"`).

## Exemplo

```python
notas = [
    {"categoria": "livros", "valor": 50.0, "cancelada": False},
    {"categoria": "livros", "valor": 30.5, "cancelada": False},
    {"categoria": "eletronicos", "valor": 200.0, "cancelada": True},
    {"categoria": "papelaria", "valor": 12.333, "cancelada": False},
]
consolidar_notas(notas)
# {"livros": 80.5, "papelaria": 12.33}
```
