#!/usr/bin/env python3
"""Consolidacao do dataset de trials do Lab02 (issue #85).

Le o registro bruto gravado por src/timer.py (data/trials_raw.csv), valida a
integridade do desenho experimental e escreve data/trials.csv, que e a entrada
unica da analise da S03.

O que a validacao protege, alem do "18 linhas sem nulos" do criterio da issue:

    - testes_total precisa bater com a suite congelada da kata (issue #59);
      uma execucao que falhou na coleta grava 0/0 e apagaria o denominador
      da RQ2 em silencio;
    - tempo no time-box exige censurado=1, e trial nao censurado exige que
      todos os testes passem - as duas formas de encerrar previstas no
      protocolo;
    - cada (integrante, kata, tratamento) precisa existir e estar na ordem
      congelada na tabela de contrabalanceamento (secao 4 do DESENHO.md).

Nenhum trial e descartado: censura e desvio de protocolo entram no dataset
marcados. Trial re-executado (timer --refazer) vale pelo registro mais recente,
e o descarte e sempre reportado.

Uso:
    python src/consolida.py                  # exige os 18 trials
    python src/consolida.py --parcial        # escreve o que ja foi coletado
    python src/consolida.py --conferir       # so valida, nao escreve
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

TIME_BOX_S = 2100  # DESENHO.md, secao 3
INTEGRANTES = ("guilherme", "gabriel", "henrique")
TRATAMENTOS = ("com-ia", "sem-ia")

TOTAL_ESPERADO = 18
POR_TRATAMENTO = 9
POR_CELULA = 3

# Numero de testes de cada suite congelada na issue #59 (DESENHO.md, secao 4).
# Serve de conferencia: o valor gravado continua vindo da execucao real.
TESTES_POR_KATA = {"k1": 9, "k2": 9, "k3": 8, "k4": 9, "k5": 9, "k6": 9}

# Ordem congelada antes da coleta (DESENHO.md, secao 4 - contrabalanceamento).
PLANO = {
    "guilherme": {("k1", "com-ia"): 1, ("k2", "sem-ia"): 2, ("k3", "com-ia"): 3,
                  ("k4", "sem-ia"): 4, ("k5", "com-ia"): 5, ("k6", "sem-ia"): 6},
    "gabriel": {("k1", "sem-ia"): 1, ("k2", "com-ia"): 2, ("k3", "sem-ia"): 3,
                ("k4", "com-ia"): 4, ("k5", "sem-ia"): 5, ("k6", "com-ia"): 6},
    "henrique": {("k6", "com-ia"): 1, ("k5", "sem-ia"): 2, ("k4", "com-ia"): 3,
                 ("k3", "sem-ia"): 4, ("k2", "com-ia"): 5, ("k1", "sem-ia"): 6},
}

# Schema consumido pela S03 (issue #85). A chave (integrante, kata, tratamento)
# e a mesma de data/metricas.csv, para permitir o join na analise da RQ3.
COLUNAS = (
    "integrante",
    "kata",
    "tratamento",
    "ordem",
    "tempo_s",
    "testes_passando",
    "testes_total",
    "taxa_sucesso",
    "censurado",
    "n_prompts",
)


def raiz_lab() -> Path:
    return Path(__file__).resolve().parent.parent


def ler_bruto(caminho: Path) -> list[dict]:
    if not caminho.is_file():
        raise SystemExit(
            f"{caminho} nao existe - ele e gerado por src/timer.py a cada trial encerrado."
        )
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        # numero da linha no arquivo: a primeira linha de dados e a 2
        linhas = [
            {**registro, "_linha": numero}
            for numero, registro in enumerate(csv.DictReader(arquivo), start=2)
        ]
    if not linhas:
        raise SystemExit(f"{caminho} nao tem nenhum trial registrado.")
    return linhas


def dados_do_trial(raiz: Path, integrante: str, kata: str, tratamento: str) -> dict:
    """Le trial.json da pasta do trial, quando existe.

    O timer nao registra n_prompts (metrica exploratoria da RQ1) nem correcao
    manual; os dois entram no trial.json da pasta e sao lidos aqui.
    """
    caminho = raiz / "trials" / f"{integrante}__{kata}__{tratamento}" / "trial.json"
    if not caminho.is_file():
        return {}
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def deduplicar(linhas: list[dict], avisos: list[str]) -> list[dict]:
    """Um trial refeito gera duas linhas; vale a mais recente.

    O arquivo bruto continua com as duas - o que sai daqui e sempre reportado,
    nunca some em silencio.
    """
    posicoes: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for i, linha in enumerate(linhas):
        posicoes[(linha["integrante"], linha["kata"], linha["tratamento"])].append(i)

    manter = set()
    for chave, indices in posicoes.items():
        manter.add(indices[-1])
        if len(indices) > 1:
            descartadas = ", ".join(str(linhas[i]["_linha"]) for i in indices[:-1])
            avisos.append(
                f"{' '.join(chave)}: {len(indices)} registros; vale a linha "
                f"{linhas[indices[-1]]['_linha']}, superseded linha(s) {descartadas}"
            )
    return [linha for i, linha in enumerate(linhas) if i in manter]


def validar(linha: dict, raiz: Path, erros: list[str], avisos: list[str]) -> dict | None:
    """Valida e normaliza um trial. Devolve None se a linha for inaproveitavel."""
    onde = f"linha {linha['_linha']}"

    integrante = (linha.get("integrante") or "").strip().lower()
    kata = (linha.get("kata") or "").strip().lower()
    tratamento = (linha.get("tratamento") or "").strip().lower()

    if integrante not in INTEGRANTES:
        erros.append(f"{onde}: integrante invalido ({linha.get('integrante')!r})")
        return None
    if kata not in TESTES_POR_KATA:
        erros.append(f"{onde}: kata invalida ({linha.get('kata')!r})")
        return None
    if tratamento not in TRATAMENTOS:
        erros.append(f"{onde}: tratamento invalido ({linha.get('tratamento')!r})")
        return None

    onde = f"{onde} ({integrante} {kata} {tratamento})"

    ordem_planejada = PLANO[integrante].get((kata, tratamento))
    if ordem_planejada is None:
        erros.append(f"{onde}: combinacao fora do contrabalanceamento (DESENHO.md, secao 4)")
        return None

    try:
        ordem = int(linha["ordem"])
        tempo_s = int(float(linha["tempo_s"]))
        passando = int(linha["testes_passando"])
        total = int(linha["testes_total"])
        censurado = int(linha["censurado"])
    except (KeyError, TypeError, ValueError):
        erros.append(f"{onde}: campo numerico ausente ou invalido (ordem/tempo/testes/censura)")
        return None

    if censurado not in (0, 1):
        erros.append(f"{onde}: censurado deve ser 0 ou 1, veio {linha['censurado']!r}")
        return None

    if ordem != ordem_planejada:
        avisos.append(
            f"{onde}: ordem {ordem} difere da planejada ({ordem_planejada}) - "
            "desvio a registrar na issue do trial"
        )

    esperado = TESTES_POR_KATA[kata]
    if total != esperado:
        erros.append(
            f"{onde}: testes_total={total}, mas a suite congelada da {kata} tem {esperado} "
            f"(issue #59). total=0 e execucao que falhou na coleta, nao trial com zero testes: "
            f"o denominador da RQ2 nao pode ser lido dessa linha"
        )
        return None
    if not 0 <= passando <= total:
        erros.append(f"{onde}: testes_passando={passando} fora de [0, {total}]")
        return None

    if not 0 <= tempo_s <= TIME_BOX_S:
        erros.append(f"{onde}: tempo_s={tempo_s} fora de [0, {TIME_BOX_S}]")
        return None
    if tempo_s == TIME_BOX_S and censurado != 1:
        erros.append(f"{onde}: tempo no time-box ({TIME_BOX_S} s) exige censurado=1")
        return None
    if censurado == 0 and passando != total:
        erros.append(
            f"{onde}: trial nao censurado com {passando}/{total} - sem censura so fecha "
            "quem passa em todos os testes"
        )
        return None
    if censurado == 1 and passando == total and tempo_s == TIME_BOX_S:
        avisos.append(
            f"{onde}: censurado com {passando}/{total} no time-box. Se o verde saiu antes, "
            "o tempo real esta em trial_log.txt e o registro precisa de correcao"
        )

    trial = dados_do_trial(raiz, integrante, kata, tratamento)
    if trial.get("correcao_manual"):
        avisos.append(f"{onde}: correcao manual registrada em trial.json - citar na metodologia")

    n_prompts = trial.get("n_prompts", "")
    if tratamento == "sem-ia" and str(n_prompts).strip():
        erros.append(
            f"{onde}: n_prompts preenchido em trial sem-IA. Se houve uso de assistente, "
            "e desvio de protocolo e precisa estar registrado na issue do trial"
        )
        return None

    return {
        "integrante": integrante,
        "kata": kata,
        "tratamento": tratamento,
        "ordem": ordem,
        "tempo_s": tempo_s,
        "testes_passando": passando,
        "testes_total": total,
        "taxa_sucesso": round(passando / total, 4),
        "censurado": censurado,
        "n_prompts": n_prompts if str(n_prompts).strip() else "",
    }


def validar_desenho(trials: list[dict]) -> list[str]:
    """Confere a estrutura crossover: 18 trials, 9 por tratamento, 3 por celula."""
    problemas: list[str] = []

    if len(trials) != TOTAL_ESPERADO:
        problemas.append(f"esperados {TOTAL_ESPERADO} trials, encontrados {len(trials)}")

    por_tratamento = Counter(t["tratamento"] for t in trials)
    for tratamento in TRATAMENTOS:
        obtido = por_tratamento.get(tratamento, 0)
        if obtido != POR_TRATAMENTO:
            problemas.append(f"{tratamento}: {obtido} trials (esperados {POR_TRATAMENTO})")

    celulas = Counter((t["integrante"], t["tratamento"]) for t in trials)
    ausentes = []
    for integrante in INTEGRANTES:
        for tratamento in TRATAMENTOS:
            obtido = celulas.get((integrante, tratamento), 0)
            if obtido != POR_CELULA:
                problemas.append(
                    f"{integrante} / {tratamento}: {obtido} trials (esperados {POR_CELULA})"
                )
        for (kata, tratamento) in PLANO[integrante]:
            existe = any(
                t["integrante"] == integrante
                and t["kata"] == kata
                and t["tratamento"] == tratamento
                for t in trials
            )
            if not existe:
                ausentes.append(f"{integrante} {kata} {tratamento}")

    if ausentes:
        problemas.append(f"trials ausentes ({len(ausentes)}): {', '.join(ausentes)}")
    return problemas


def escrever_csv(destino: Path, trials: list[dict]) -> None:
    ordenados = sorted(trials, key=lambda t: (INTEGRANTES.index(t["integrante"]), t["ordem"]))
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(COLUNAS))
        escritor.writeheader()
        escritor.writerows(ordenados)


def resumo(trials: list[dict]) -> None:
    print()
    print(f"{'integrante':<12}{'com-ia':>8}{'sem-ia':>8}{'censurados':>12}")
    print("-" * 40)
    for integrante in INTEGRANTES:
        seus = [t for t in trials if t["integrante"] == integrante]
        com = sum(1 for t in seus if t["tratamento"] == "com-ia")
        sem = sum(1 for t in seus if t["tratamento"] == "sem-ia")
        cens = sum(1 for t in seus if t["censurado"] == 1)
        print(f"{integrante:<12}{com:>8}{sem:>8}{cens:>12}")
    print("-" * 40)
    print(
        f"{'total':<12}"
        f"{sum(1 for t in trials if t['tratamento'] == 'com-ia'):>8}"
        f"{sum(1 for t in trials if t['tratamento'] == 'sem-ia'):>8}"
        f"{sum(1 for t in trials if t['censurado'] == 1):>12}"
    )


def main() -> int:
    raiz = raiz_lab()
    parser = argparse.ArgumentParser(
        description="Consolida data/trials_raw.csv em data/trials.csv (issue #85)."
    )
    parser.add_argument("--entrada", type=Path, default=raiz / "data" / "trials_raw.csv")
    parser.add_argument("--saida", type=Path, default=raiz / "data" / "trials.csv")
    parser.add_argument("--parcial", action="store_true",
                        help="escreve mesmo com menos de 18 trials (uso durante a S02)")
    parser.add_argument("--conferir", action="store_true", help="so valida, nao escreve")
    args = parser.parse_args()

    erros: list[str] = []
    avisos: list[str] = []

    trials = []
    for linha in deduplicar(ler_bruto(args.entrada), avisos):
        validada = validar(linha, raiz, erros, avisos)
        if validada is not None:
            trials.append(validada)

    problemas_desenho = validar_desenho(trials)

    for aviso in avisos:
        print(f"aviso: {aviso}", file=sys.stderr)
    for erro in erros:
        print(f"ERRO: {erro}", file=sys.stderr)

    if erros:
        print(
            f"\n{len(erros)} erro(s) de integridade. Corrija {args.entrada} "
            "(e o trial.json correspondente) antes de consolidar.",
            file=sys.stderr,
        )
        return 1

    incompleto = bool(problemas_desenho)
    if incompleto:
        rotulo = "aviso" if args.parcial else "ERRO"
        for problema in problemas_desenho:
            print(f"{rotulo}: {problema}", file=sys.stderr)
        if not args.parcial:
            print(
                "\nDataset incompleto. Use --parcial para gerar o CSV do que ja foi coletado.",
                file=sys.stderr,
            )
            return 1

    resumo(trials)

    if args.conferir:
        print(f"\nValidacao concluida: {len(trials)} trials. Nada foi escrito (--conferir).")
        return 0

    escrever_csv(args.saida, trials)
    print(f"\n{args.saida}: {len(trials)} trials ({'PARCIAL' if incompleto else 'completo'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
