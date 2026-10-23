# Artigo

| Arquivo | O que é |
| :--- | :--- |
| `0N-*.md` | as seis seções, fonte da verdade |
| `ARTIGO.md` | consolidação gerada por `python artigo/montar.py` |
| `artigo.tex` | versão SBC gerada por `python artigo/para_latex.py` |
| `artigo.pdf` | compilado com `tectonic -X compile artigo.tex` |
| `figuras/` | as figuras achatadas com nome único, referenciadas pelo `.tex` |
| `sbc-template.sty`, `sbc.bst` | template oficial da SBC |

## Regenerar

```bash
python artigo/montar.py        # 0N-*.md -> ARTIGO.md
python artigo/para_latex.py    # 0N-*.md -> artigo.tex
cd artigo && tectonic -X compile artigo.tex
```

Para o Overleaf: suba `artigo.tex`, `sbc-template.sty`, `sbc.bst` e a pasta `figuras/`.

## Estado

15 páginas. O enunciado pede no máximo 10. O que ainda pode sair, por ordem de custo:
a seção 3.7 (análises além do escopo), as figuras das RQ05/RQ06 e as tabelas de
concordância da seção 2.7.
