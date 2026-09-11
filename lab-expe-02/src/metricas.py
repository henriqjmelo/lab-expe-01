#!/usr/bin/env python3
"""Coleta das metricas estaticas da RQ3 sobre o codigo final de cada trial.

Roda sobre a solucao de um trial (ou sobre todos os trials de uma vez) e
consolida em data/metricas.csv, com chave (integrante, kata, tratamento).

Ferramentas:
    radon cc   -> complexidade ciclomatica media por funcao/metodo (RQ3)
    radon raw  -> LOC e SLOC (variavel de controle)
    radon mi   -> indice de manutenibilidade (aprofundamento opcional)
    jscpd      -> percentual de linhas duplicadas (RQ3)

O enunciado sugere CK, que exige Java. Como a linguagem fixada do experimento e
Python, usamos Radon + jscpd como equivalentes, conforme o enunciado permite.
As opcoes de cada ferramenta ficam fixas neste arquivo (ver PARAMS_JSCPD) para
atender a mitigacao de "efeito de medicao" da secao 5 do DESENHO.md.

Uso:
    python src/metricas.py --todos
    python src/metricas.py --trial trials/guilherme__k1__com-ia
    python src/metricas.py --arquivo caminho/solucao.py \
        --integrante guilherme --kata k1 --tratamento com-ia
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Fixados para reprodutibilidade: mudar aqui muda todas as medicoes.
PARAMS_JSCPD = ("--min-lines", "5", "--min-tokens", "50")

COLUNAS = (
    "integrante",
    "kata",
    "tratamento",
    "complexidade_media",
    "n_blocos",
    "loc",
    "sloc",
    "mi",
    "duplicacao_pct",
)


def raiz_lab() -> Path:
    return Path(__file__).resolve().parent.parent


def rodar(comando: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(comando, cwd=cwd, capture_output=True, text=True, check=False)


def radon_json(subcomando: str, alvo: Path) -> dict:
    """Executa `radon <subcomando> -j` e devolve o JSON ja decodificado."""
    proc = rodar([sys.executable, "-m", "radon", subcomando, "-j", str(alvo)])
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"radon {subcomando} falhou em {alvo}: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def complexidade(alvo: Path) -> tuple[float | None, int]:
    """Media da complexidade ciclomatica por funcao/metodo, e quantos blocos.

    Entradas do tipo `class` sao ignoradas: a complexidade da classe agrega a
    dos proprios metodos e contaria em dobro na media.
    """
    dados = radon_json("cc", alvo)
    blocos = [
        b
        for entradas in dados.values()
        if isinstance(entradas, list)
        for b in entradas
        if b.get("type") in ("function", "method")
    ]
    if not blocos:
        return None, 0
    media = sum(b["complexity"] for b in blocos) / len(blocos)
    return round(media, 3), len(blocos)


def brutas(alvo: Path) -> tuple[int | None, int | None]:
    dados = radon_json("raw", alvo)
    for valor in dados.values():
        if isinstance(valor, dict) and "loc" in valor:
            return valor["loc"], valor["sloc"]
    return None, None


def manutenibilidade(alvo: Path) -> float | None:
    dados = radon_json("mi", alvo)
    for valor in dados.values():
        if isinstance(valor, dict) and "mi" in valor:
            return round(valor["mi"], 3)
    return None


def duplicacao(alvo: Path) -> float | None:
    """Percentual de linhas duplicadas do arquivo, medido pelo jscpd.

    O arquivo e copiado para um diretorio temporario para que o jscpd analise
    somente a solucao, sem a suite de testes nem o README da kata ao lado.
    """
    jscpd = shutil.which("jscpd") or shutil.which("npx")
    if jscpd is None:
        raise RuntimeError("jscpd nao encontrado; rode `npm install` em lab-expe-02/")
    base = [jscpd] if jscpd.endswith("jscpd") else [jscpd, "jscpd"]

    with tempfile.TemporaryDirectory() as tmp:
        entrada = Path(tmp) / "entrada"
        entrada.mkdir()
        shutil.copy2(alvo, entrada / alvo.name)
        saida = Path(tmp) / "relatorio"

        proc = rodar(
            base
            + ["--reporters", "json", "--output", str(saida), "--silent"]
            + list(PARAMS_JSCPD)
            + [str(entrada)],
            cwd=raiz_lab(),
        )
        relatorio = saida / "jscpd-report.json"
        if not relatorio.exists():
            raise RuntimeError(
                f"jscpd nao gerou relatorio para {alvo}: "
                f"{(proc.stderr or proc.stdout).strip()[:300]}"
            )
        dados = json.loads(relatorio.read_text(encoding="utf-8"))

    total = dados.get("statistics", {}).get("total", {})
    pct = total.get("percentage")
    return round(float(pct), 3) if pct is not None else None


def medir(alvo: Path, integrante: str, kata: str, tratamento: str) -> dict:
    media, n_blocos = complexidade(alvo)
    loc, sloc = brutas(alvo)
    return {
        "integrante": integrante,
        "kata": kata,
        "tratamento": tratamento,
        "complexidade_media": media if media is not None else "",
        "n_blocos": n_blocos,
        "loc": loc if loc is not None else "",
        "sloc": sloc if sloc is not None else "",
        "mi": manutenibilidade(alvo),
        "duplicacao_pct": duplicacao(alvo),
    }


def metadados_do_trial(pasta: Path) -> tuple[str, str, str]:
    """Le integrante/kata/tratamento do trial.json, com fallback para o nome."""
    meta = pasta / "trial.json"
    if meta.exists():
        dados = json.loads(meta.read_text(encoding="utf-8"))
        return dados["integrante"], dados["kata"], dados["tratamento"]
    partes = pasta.name.split("__")
    if len(partes) != 3:
        raise SystemExit(
            f"nao consegui identificar o trial em {pasta}: sem trial.json e nome "
            "fora do padrao <integrante>__<kata>__<tratamento>"
        )
    return partes[0], partes[1], partes[2]


def escrever_csv(destino: Path, linhas: list[dict]) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(COLUNAS))
        escritor.writeheader()
        escritor.writerows(linhas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Metricas estaticas do Lab02 (RQ3)")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--todos", action="store_true",
                       help="mede todos os trials em trials/")
    grupo.add_argument("--trial", help="pasta de um trial")
    grupo.add_argument("--arquivo", help="caminho direto de um solucao.py")
    parser.add_argument("--integrante")
    parser.add_argument("--kata")
    parser.add_argument("--tratamento")
    parser.add_argument("--saida", default=None,
                        help="CSV de destino (padrao data/metricas.csv)")
    args = parser.parse_args()

    raiz = raiz_lab()
    saida = Path(args.saida) if args.saida else raiz / "data" / "metricas.csv"
    linhas: list[dict] = []

    if args.arquivo:
        faltando = [n for n in ("integrante", "kata", "tratamento") if not getattr(args, n)]
        if faltando:
            raise SystemExit(f"--arquivo exige tambem: {', '.join('--' + f for f in faltando)}")
        linhas.append(medir(Path(args.arquivo), args.integrante, args.kata, args.tratamento))
    else:
        pastas = (
            sorted(p for p in (raiz / "trials").iterdir() if p.is_dir())
            if args.todos
            else [Path(args.trial)]
        )
        for pasta in pastas:
            solucao = pasta / "solucao.py"
            if not solucao.exists():
                print(f"  ignorado (sem solucao.py): {pasta.name}")
                continue
            integrante, kata, tratamento = metadados_do_trial(pasta)
            print(f"  medindo {integrante} | {kata} | {tratamento}")
            linhas.append(medir(solucao, integrante, kata, tratamento))

    if not linhas:
        raise SystemExit("nenhuma solucao medida")

    escrever_csv(saida, linhas)
    print(f"\n{len(linhas)} linha(s) em {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
