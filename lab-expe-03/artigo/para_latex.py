from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MAPA_FIGURAS = json.loads(Path("artigo/figuras/_mapa.json").read_text(encoding="utf-8"))


def caminho_figura(bruto: str) -> str:
    limpo = bruto.replace("../", "")
    return "figuras/" + MAPA_FIGURAS.get(limpo, Path(limpo).name)

PREAMBULO = r"""\documentclass[12pt]{article}

\usepackage{sbc-template}
\usepackage{graphicx,url}
\usepackage[hidelinks]{hyperref}
\usepackage[brazil]{babel}
\usepackage[utf8]{inputenc}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{ragged2e}
\usepackage{float}
\setlength{\textfloatsep}{8pt}
\setlength{\intextsep}{8pt}
\setlength{\abovecaptionskip}{4pt}

\sloppy

\title{Mineração de métricas DORA em repositórios open-source populares:\\
o que acontece quando os proxies são validados}

\author{Guilherme Costa\inst{1}, Henrique Jardim Melo\inst{1}, Gabriel Afonso\inst{1}}

\address{Engenharia de Software -- Pontifícia Universidade Católica de Minas Gerais
  (PUC Minas)\\
  Belo Horizonte -- MG -- Brasil
  \email{\{guilherme,henrique,gabriel\}@sga.pucminas.br}
}

\begin{document}

\maketitle

\begin{abstract}
We mine the four DORA metrics from 900 popular open-source repositories that use
GitHub Actions, and then test whether the proxies required to do so are valid
measures. Three raters independently labelled 300 releases: no version of the
corrective-release heuristic reaches the required F1 of 0.70, and the one behind
the dataset has 36.5\% precision. Conditioning on observation opportunity, the
correlation between deployment frequency and change failure rate collapses from
0.604 to $-0.039$, showing that this proxy largely measures publication cadence
rather than failure. The DORA bands show no discriminant power against repository
attributes. Estimates reproduce across three independent samples.
\end{abstract}

\begin{resumo}
Minera-se as quatro métricas DORA de 900 repositórios open-source populares que
usam GitHub Actions e, em seguida, testa-se se os proxies necessários para isso
são medidas válidas. Três avaliadores rotularam 300 releases de forma
independente: nenhuma versão da heurística de release corretiva alcança o F1
mínimo de 0,70, e a que gerou o dataset tem precisão de 36,5\%. Ao condicionar
pela oportunidade de observação, a correlação entre frequência de deploy e taxa
de falha cai de 0,604 para $-0,039$, mostrando que esse proxy mede, em boa parte,
cadência de publicação e não falha. As faixas DORA não apresentam poder
discriminante. As estimativas se reproduzem em três amostras independentes.
\end{resumo}

"""

RODAPE = "\n\\end{document}\n"

ESPECIAIS = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
             "_": r"\_", "{": r"\{", "}": r"\}"}

UNICODE = {"≈": r"$\approx$", "≥": r"$\geq$", "≤": r"$\leq$", "×": r"$\times$",
           "−": "--", "ε": r"$\varepsilon$", "ρ": r"$\rho$", "κ": r"$\kappa$",
           "δ": r"$\delta$", "χ": r"$\chi$", "β": r"$\beta$", "²": r"$^2$",
           "⁻": r"$^-$", "⁴": r"$^4$", "³": r"$^3$", "→": r"$\rightarrow$",
           "⊇": r"$\supseteq$", "±": r"$\pm$", "…": r"\ldots{}"}


def escapar(texto: str) -> str:
    saida = []
    for ch in texto:
        if ch in ESPECIAIS:
            saida.append(ESPECIAIS[ch])
        elif ch == "~":
            saida.append(r"\textasciitilde{}")
        elif ch == "^":
            saida.append(r"\textasciicircum{}")
        elif ch == "\\":
            saida.append(r"\textbackslash{}")
        else:
            saida.append(ch)
    texto = "".join(saida)
    for k, v in UNICODE.items():
        texto = texto.replace(k, v)
    texto = re.sub(r'"([^"]*)"', r"``\1''", texto)
    return texto


def inline(texto: str) -> str:
    marcadores: list[str] = []

    def guardar(valor: str) -> str:
        marcadores.append(valor)
        return f"\x00{len(marcadores) - 1}\x00"

    texto = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                   lambda m: guardar(r"\includegraphics[width=0.46\columnwidth]{"
                                     + caminho_figura(m.group(2)) + "}"), texto)
    texto = re.sub(r"`([^`]+)`", lambda m: guardar(r"\texttt{" + escapar(m.group(1)) + "}"), texto)
    texto = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
                   lambda m: guardar(r"\href{" + m.group(2) + "}{" + escapar(m.group(1)) + "}"), texto)
    texto = escapar(texto)
    texto = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", texto)
    texto = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\\emph{\1}", texto)
    for i, valor in enumerate(marcadores):
        texto = texto.replace(f"\x00{i}\x00", valor)
    return texto


def alinhamento(separador: str) -> str:
    colunas = []
    for celula in separador.strip().strip("|").split("|"):
        c = celula.strip()
        if c.endswith(":") and c.startswith(":"):
            colunas.append("c")
        elif c.endswith(":"):
            colunas.append("r")
        else:
            colunas.append("l")
    return colunas


def tabela(linhas: list[str]) -> str:
    cabecalho = [c.strip() for c in linhas[0].strip().strip("|").split("|")]
    cols = alinhamento(linhas[1])
    corpo = []
    comprimentos = [0] * len(cols)
    for linha in linhas[2:]:
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        celulas += [""] * (len(cols) - len(celulas))
        celulas = celulas[:len(cols)]
        for j, c in enumerate(celulas):
            comprimentos[j] = max(comprimentos[j], len(c))
        corpo.append(" & ".join(inline(c) for c in celulas) + r" \\")

    total = sum(max(c, 6) for c in comprimentos) or 1
    if max(comprimentos) > 28:
        pesos = [max(0.07, 0.86 * max(c, 6) / total) for c in comprimentos]
        fator = 0.86 / sum(pesos)
        spec = "".join(f"p{{{w * fator:.3f}\\columnwidth}}" for w in pesos)
    else:
        spec = "".join(cols)
    return ("\n\\begin{table}[!htbp]\n\\centering\n\\scriptsize\n"
            f"\\begin{{tabular}}{{{spec}}}\n\\toprule\n"
            + " & ".join(r"\textbf{" + inline(c) + "}" for c in cabecalho) + r" \\" + "\n\\midrule\n"
            + "\n".join(corpo)
            + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")


def converter(md: str) -> str:
    md = re.sub(r"(?m)^>.*\n?", "", md)
    linhas = md.split("\n")
    saida: list[str] = []
    i = 0
    lista_aberta: str | None = None

    def fechar_lista() -> None:
        nonlocal lista_aberta
        if lista_aberta:
            saida.append(f"\\end{{{lista_aberta}}}")
            lista_aberta = None

    while i < len(linhas):
        linha = linhas[i]

        if re.match(r"^\s*$", linha):
            fechar_lista()
            saida.append("")
            i += 1
            continue

        if re.match(r"^---+\s*$", linha):
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", linha)
        if m:
            fechar_lista()
            nivel, titulo = len(m.group(1)), m.group(2).strip()
            titulo = re.sub(r"^\d+(\.\d+)*\.?\s*", "", titulo)
            comando = {1: "section", 2: "subsection", 3: "subsubsection", 4: "paragraph"}[nivel]
            saida.append(f"\\{comando}{{{inline(titulo)}}}")
            i += 1
            continue

        if linha.lstrip().startswith("![") :
            m = re.match(r"^\s*!\[([^\]]*)\]\(([^)]+)\)", linha)
            if m:
                fechar_lista()
                legenda, caminho = m.group(1), caminho_figura(m.group(2))
                saida.append("\n\\begin{figure}[!htbp]\n\\centering\n"
                             f"\\includegraphics[width=0.55\\columnwidth]{{{caminho}}}\n"
                             f"\\caption{{{inline(legenda)}}}\n\\end{{figure}}\n")
                i += 1
                continue

        if linha.strip().startswith("|") and i + 1 < len(linhas) and re.match(r"^\s*\|[\s:|-]+\|\s*$", linhas[i + 1]):
            fechar_lista()
            bloco = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                bloco.append(linhas[i])
                i += 1
            saida.append(tabela(bloco))
            continue

        m = re.match(r"^(\s*)[-*]\s+(.*)$", linha)
        if m:
            if lista_aberta != "itemize":
                fechar_lista()
                saida.append("\\begin{itemize}")
                lista_aberta = "itemize"
            saida.append(f"  \\item {inline(m.group(2))}")
            i += 1
            continue

        m = re.match(r"^(\s*)\d+\.\s+(.*)$", linha)
        if m:
            if lista_aberta != "enumerate":
                fechar_lista()
                saida.append("\\begin{enumerate}")
                lista_aberta = "enumerate"
            saida.append(f"  \\item {inline(m.group(2))}")
            i += 1
            continue

        fechar_lista()
        saida.append(inline(linha.strip()))
        i += 1

    fechar_lista()
    texto = "\n".join(saida)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python artigo/para_latex.py")
    ap.add_argument("--entrada", type=Path, default=Path("artigo"))
    ap.add_argument("--saida", type=Path, default=Path("artigo/artigo.tex"))
    args = ap.parse_args(argv)

    secoes = sorted(args.entrada.glob("0*.md")) if args.entrada.is_dir() else [args.entrada]
    corpo = "\n\n".join(converter(c.read_text(encoding="utf-8")) for c in secoes)
    args.saida.write_text(PREAMBULO + corpo + RODAPE, encoding="utf-8")
    print(f"{args.saida}: {len(corpo.splitlines())} linhas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
