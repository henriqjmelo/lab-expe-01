from __future__ import annotations

import argparse
from pathlib import Path

CABECALHO = """# Mineração de métricas DORA em repositórios open-source populares

**Laboratório de Experimentação de Software** · Engenharia de Software, 6º período
Guilherme Costa · Henrique Jardim Melo · Gabriel Afonso

> Documento consolidado, gerado por `python artigo/montar.py`. Não editar diretamente:
> altere as seções em `artigo/0N-*.md` e rode o script de novo.

---
"""


def montar(pasta: Path) -> str:
    partes = [CABECALHO]
    for caminho in sorted(pasta.glob("0*.md")):
        partes.append(caminho.read_text(encoding="utf-8").rstrip())
        partes.append("\n---\n")
    return "\n".join(partes[:-1]) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python artigo/montar.py")
    ap.add_argument("--pasta", type=Path, default=Path("artigo"))
    ap.add_argument("--saida", type=Path, default=Path("artigo/ARTIGO.md"))
    args = ap.parse_args(argv)
    texto = montar(args.pasta)
    args.saida.write_text(texto, encoding="utf-8")
    print(f"{args.saida}: {len(texto.splitlines())} linhas, {len(texto.split())} palavras")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
