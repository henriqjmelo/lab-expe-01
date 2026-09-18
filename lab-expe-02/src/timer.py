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
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
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
    coletou: bool = True

    @property
    def verde(self) -> bool:
        return self.coletou and self.total > 0 and self.passando == self.total


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
            # Erro de coleta (import quebrado, arquivo sem testes): sem denominador.
            return Resultado(passando=0, total=0, duracao_s=duracao, coletou=False)

        if suite.tag == "testsuites":
            nos = list(suite)
            if not nos:
                return Resultado(passando=0, total=0, duracao_s=duracao, coletou=False)
            suite = nos[0]

        total = int(suite.get("tests", 0))
        falhas = int(suite.get("failures", 0))
        erros = int(suite.get("errors", 0))
        pulados = int(suite.get("skipped", 0))
        passando = max(total - falhas - erros - pulados, 0)
        return Resultado(
            passando=passando, total=total, duracao_s=duracao, coletou=total > 0
        )
    finally:
        relatorio.unlink(missing_ok=True)


def consolidar(anterior: Resultado, novo: Resultado, total_esperado: int) -> Resultado:
    """Descarta execucao que nao coletou a suite inteira.

    testes_total e propriedade da kata, nao da execucao: a suite foi congelada
    na issue #59 e nao muda durante o trial. Quando pytest falha na coleta
    (import quebrado, sintaxe invalida) ele devolve 0 de 0, ou 1 de 1 contando
    o proprio erro - gravar isso troca o denominador da RQ2. Foi o que
    aconteceu no trial #72, que ficou com testes_total=0 embora a suite da k1
    tenha 9 testes. Nesses casos vale a ultima medicao que coletou a suite
    inteira, e o participante ve o aviso no terminal.
    """
    if total_esperado and novo.total == total_esperado:
        return novo
    if not total_esperado and novo.coletou:
        return novo
    return anterior


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


def _leitor_stdin(fila: "queue.Queue[str]") -> None:
    """Thread daemon que le linhas de stdin e as coloca na fila.

    select.select() em stdin so funciona com sockets no Windows (falha com
    OSError WinError 10093); ler numa thread separada e portavel entre
    Windows, Mac e Linux.
    """
    for linha in sys.stdin:
        fila.put(linha)
    fila.put("")  # sinaliza EOF pro consumidor


def ler_comando(fila: "queue.Queue[str]", timeout_s: float) -> str | None:
    """Le um comando da fila respeitando o tempo restante do time-box.

    Devolve None quando o time-box estoura ou quando o stdin termina (caso em
    que o trial simplesmente corre ate o time-box).
    """
    if timeout_s <= 0:
        return None
    try:
        linha = fila.get(timeout=timeout_s)
    except queue.Empty:
        return None
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

    # Denominador da RQ2, medido sobre o esqueleto intacto antes de o relogio
    # comecar: nesse estado a suite coleta normalmente e todos os testes falham
    # com NotImplementedError.
    baseline = rodar_suite(trial)
    total_esperado = baseline.total

    inicio_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    eventos: list[str] = [f"inicio={inicio_iso}", f"suite={total_esperado} testes"]

    print(f"\nTrial: {integrante} | {kata} | {args.tratamento} | ordem {args.ordem}")
    print(f"Pasta: {trial}")
    print(f"Time-box: {formatar_restante(args.timebox)}")
    print(f"Suite: {total_esperado} testes de aceitacao")
    print("Edite solucao.py nessa pasta. Comandos: [t|Enter] testar  [s] status  [x] encerrar\n")

    fila_stdin: "queue.Queue[str]" = queue.Queue()
    threading.Thread(target=_leitor_stdin, args=(fila_stdin,), daemon=True).start()

    relogio = time.monotonic()
    fim = relogio + args.timebox
    ultimo = Resultado(passando=0, total=total_esperado, duracao_s=0.0, coletou=False)
    tempo_s = args.timebox
    censurado = 1

    while True:
        comando = ler_comando(fila_stdin, fim - time.monotonic())

        if comando is None:
            # Time-box estourado: preserva o estado observado neste instante.
            decorrido = time.monotonic() - relogio
            print(f"\n[{formatar_restante(decorrido)}] TIME-BOX. Rodando a suite uma ultima vez...")
            ultimo = consolidar(ultimo, rodar_suite(trial), total_esperado)
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
            ultimo = consolidar(ultimo, rodar_suite(trial), total_esperado)
            eventos.append(
                f"desistencia t={decorrido:.1f}s testes={ultimo.passando}/{ultimo.total}"
            )
            if ultimo.verde:
                # A verificacao do proprio x passou em tudo: o trial chegou ao
                # verde, e registrar como censurado em 2100 s jogaria fora o
                # time-to-green real (RQ1). Foi o que aconteceu em #73, #75 e
                # #76, corrigidos na mao depois.
                tempo_s = int(round(decorrido))
                censurado = 0
                eventos.append(f"verde no check do x t={decorrido:.1f}s")
                print(f"\nVERDE em {formatar_restante(decorrido)} ({tempo_s} s).")
            else:
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
        execucao = rodar_suite(trial)
        ultimo = consolidar(ultimo, execucao, total_esperado)
        if ultimo is not execucao:
            # A execucao nao coletou a suite inteira: o resultado exibido seria
            # inventado. O relogio continua correndo - isso e parte do trial.
            eventos.append(
                f"run t={disparo:.1f}s descartado: coletou {execucao.total} de "
                f"{total_esperado} testes"
            )
            print(
                f"[{formatar_restante(disparo)}] solucao.py nao pode ser importada "
                f"(coletou {execucao.total} de {total_esperado} testes). "
                f"Corrija o erro e rode de novo."
            )
        else:
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
    if total_esperado == 0:
        # Nenhuma execucao do trial conseguiu coletar a suite: sem denominador,
        # a taxa de sucesso da RQ2 nao existe. Gravar assim mesmo mantem o
        # registro bruto honesto, mas o valor precisa ser resolvido a mao.
        aviso = (
            f"ATENCAO: a suite da kata {kata} nao pode ser coletada nem com o "
            f"esqueleto intacto - testes_total=0 e a RQ2 fica sem denominador. "
            f"Confira trial_log.txt, corrija a linha em {saida} e registre a "
            f"correcao em trial.json."
        )
        eventos.append("aviso: suite nunca coletada (testes_total=0)")
        print(f"\n{aviso}")

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
