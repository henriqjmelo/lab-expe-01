#!/usr/bin/env python3
"""Cronometro e registrador de trial do Lab02.

Padroniza a coleta do time-to-green (RQ1) e da taxa de testes aprovados (RQ2),
eliminando o cronometro manual. Cada execucao corresponde a um trial: prepara
uma copia isolada da kata, marca o inicio, roda a suite de aceitacao sob demanda
e grava uma linha em data/trials_raw.csv.

Uso:
    python src/timer.py --integrante guilherme --kata k1 --tratamento com-ia --ordem 1

Durante o trial, edite a solucao em trials/<id>/solucao.py e volte ao terminal:
    t (ou Enter) -> roda a suite de aceitacao
    s            -> mostra o tempo restante
    x            -> encerra o trial antes do time-box

O trial termina de tres formas, e nenhuma delas descarta o registro:
    1. verde     -> todos os testes passam; tempo_s = tempo real, censurado = 0
    2. time-box  -> 2100 s sem verde; tempo_s = 2100, censurado = 1
    3. desistencia (x) -> tratada como censura no time-box, conforme protocolo
"""

from __future__ import annotations

import argparse
import csv
import json
import select
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

TIME_BOX_PADRAO = 2100  # 35 minutos, conforme DESENHO.md secao 3
TRATAMENTOS = ("com-ia", "sem-ia")
COLUNAS = (
    "integrante",
    "kata",
    "tratamento",
    "ordem",
    "tempo_s",
    "testes_passando",
    "testes_total",
    "censurado",
)


@dataclass
class Resultado:
    """Resultado de uma execucao da suite de aceitacao."""

    passando: int
    total: int
    duracao_s: float

    @property
    def verde(self) -> bool:
        return self.total > 0 and self.passando == self.total


def raiz_lab() -> Path:
    """Raiz do lab-expe-02, derivada da localizacao deste arquivo."""
    return Path(__file__).resolve().parent.parent


def rodar_suite(diretorio: Path) -> Resultado:
    """Executa pytest no diretorio do trial e devolve a contagem de testes.

    A contagem vem do relatorio JUnit, e nao do texto do resumo, para nao
    depender do formato de saida da versao do pytest instalada.
    """
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        relatorio = Path(tmp.name)

    inicio = time.monotonic()
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--tb=no",
                "-p",
                "no:cacheprovider",
                f"--junitxml={relatorio}",
            ],
            cwd=diretorio,
            capture_output=True,
            text=True,
            check=False,
        )
        duracao = time.monotonic() - inicio

        try:
            suite = ET.parse(relatorio).getroot()
        except (ET.ParseError, FileNotFoundError):
            # Erro de coleta (import quebrado, arquivo sem testes): 0 de 0.
            return Resultado(passando=0, total=0, duracao_s=duracao)

        if suite.tag == "testsuites":
            nos = list(suite)
            if not nos:
                return Resultado(passando=0, total=0, duracao_s=duracao)
            suite = nos[0]

        total = int(suite.get("tests", 0))
        falhas = int(suite.get("failures", 0))
        erros = int(suite.get("errors", 0))
        pulados = int(suite.get("skipped", 0))
        passando = max(total - falhas - erros - pulados, 0)
        return Resultado(passando=passando, total=total, duracao_s=duracao)
    finally:
        relatorio.unlink(missing_ok=True)


def preparar_trial(raiz: Path, integrante: str, kata: str, tratamento: str,
                   refazer: bool) -> Path:
    """Cria a copia isolada da kata onde o trial sera executado.

    Diretorios separados por trial atendem a mitigacao de vazamento de solucao
    descrita na secao 5 do DESENHO.md: nada do trial volta para katas/.
    """
    origem = raiz / "katas" / kata
    if not origem.is_dir():
        raise SystemExit(f"kata inexistente: {origem}")

    destino = raiz / "trials" / f"{integrante}__{kata}__{tratamento}"
    if destino.exists():
        if not refazer:
            raise SystemExit(
                f"trial ja existe: {destino}\n"
                "Use --refazer apenas se for um trial de teste; um trial valido "
                "nao deve ser repetido (efeito de aprendizado)."
            )
        shutil.rmtree(destino)

    destino.mkdir(parents=True)
    for arquivo in sorted(origem.iterdir()):
        if arquivo.is_file():
            shutil.copy2(arquivo, destino / arquivo.name)
    return destino


def formatar_restante(segundos: float) -> str:
    segundos = max(int(segundos), 0)
    return f"{segundos // 60:02d}:{segundos % 60:02d}"


def ler_comando(timeout_s: float) -> str | None:
    """Le um comando do stdin respeitando o tempo restante do time-box.

    Devolve None quando o time-box estoura ou quando o stdin termina (caso em
    que o trial simplesmente corre ate o time-box).
    """
    if timeout_s <= 0:
        return None
    pronto, _, _ = select.select([sys.stdin], [], [], timeout_s)
    if not pronto:
        return None
    linha = sys.stdin.readline()
    if linha == "":  # EOF
        time.sleep(timeout_s)
        return None
    return linha.strip().lower()


def gravar_csv(destino: Path, linha: dict[str, object]) -> None:
    novo = not destino.exists()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(COLUNAS))
        if novo:
            escritor.writeheader()
        escritor.writerow(linha)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cronometro de trial do Lab02")
    parser.add_argument("--integrante", required=True)
    parser.add_argument("--kata", required=True, help="k1 a k6")
    parser.add_argument("--tratamento", required=True, choices=TRATAMENTOS)
    parser.add_argument("--ordem", required=True, type=int,
                        help="posicao do trial na sequencia do participante (1-6)")
    parser.add_argument("--timebox", type=int, default=TIME_BOX_PADRAO,
                        help="segundos ate a censura (padrao 2100)")
    parser.add_argument("--refazer", action="store_true",
                        help="apaga um trial existente de mesmo id (use so em teste)")
    parser.add_argument("--saida", default=None,
                        help="CSV de destino (padrao data/trials_raw.csv)")
    args = parser.parse_args()

    raiz = raiz_lab()
    kata = args.kata.lower()
    integrante = args.integrante.lower()
    trial = preparar_trial(raiz, integrante, kata, args.tratamento, args.refazer)
    saida = Path(args.saida) if args.saida else raiz / "data" / "trials_raw.csv"

    inicio_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    eventos: list[str] = [f"inicio={inicio_iso}"]

    print(f"\nTrial: {integrante} | {kata} | {args.tratamento} | ordem {args.ordem}")
    print(f"Pasta: {trial}")
    print(f"Time-box: {formatar_restante(args.timebox)}")
    print("Edite solucao.py nessa pasta. Comandos: [t|Enter] testar  [s] status  [x] encerrar\n")

    relogio = time.monotonic()
    fim = relogio + args.timebox
    ultimo = Resultado(passando=0, total=0, duracao_s=0.0)
    tempo_s = args.timebox
    censurado = 1

    while True:
        comando = ler_comando(fim - time.monotonic())

        if comando is None:
            # Time-box estourado: preserva o estado observado neste instante.
            decorrido = time.monotonic() - relogio
            print(f"\n[{formatar_restante(decorrido)}] TIME-BOX. Rodando a suite uma ultima vez...")
            ultimo = rodar_suite(trial)
            eventos.append(f"timebox testes={ultimo.passando}/{ultimo.total}")
            tempo_s = args.timebox
            censurado = 1
            break

        if comando == "s":
            print(f"  restante: {formatar_restante(fim - time.monotonic())}")
            continue

        if comando == "x":
            decorrido = time.monotonic() - relogio
            print(f"[{formatar_restante(decorrido)}] Encerrado pelo participante. Ultima verificacao...")
            ultimo = rodar_suite(trial)
            eventos.append(
                f"desistencia t={decorrido:.1f}s testes={ultimo.passando}/{ultimo.total}"
            )
            tempo_s = args.timebox
            censurado = 1
            break

        if comando not in ("", "t"):
            print("  comandos: [t|Enter] testar  [s] status  [x] encerrar")
            continue

        # O relogio do time-to-green para no instante em que a execucao que
        # ficou verde foi disparada: e o momento em que a solucao ja estava
        # pronta. A duracao da propria execucao fica registrada no log.
        disparo = time.monotonic() - relogio
        ultimo = rodar_suite(trial)
        eventos.append(
            f"run t={disparo:.1f}s testes={ultimo.passando}/{ultimo.total} "
            f"dur={ultimo.duracao_s:.1f}s"
        )
        print(
            f"[{formatar_restante(disparo)}] {ultimo.passando}/{ultimo.total} testes passando"
        )

        if ultimo.verde:
            tempo_s = int(round(disparo))
            censurado = 0
            print(f"\nVERDE em {formatar_restante(disparo)} ({tempo_s} s).")
            break

    linha = {
        "integrante": integrante,
        "kata": kata,
        "tratamento": args.tratamento,
        "ordem": args.ordem,
        "tempo_s": tempo_s,
        "testes_passando": ultimo.passando,
        "testes_total": ultimo.total,
        "censurado": censurado,
    }
    gravar_csv(saida, linha)

    (trial / "trial.json").write_text(
        json.dumps(
            {
                "integrante": integrante,
                "kata": kata,
                "tratamento": args.tratamento,
                "ordem": args.ordem,
                "inicio": inicio_iso,
                "timebox_s": args.timebox,
                **{c: linha[c] for c in ("tempo_s", "testes_passando", "testes_total", "censurado")},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (trial / "trial_log.txt").write_text("\n".join(eventos) + "\n", encoding="utf-8")

    print(f"Registrado em {saida}")
    print(f"  {linha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
