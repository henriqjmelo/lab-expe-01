"""Testes de pipeline/selecao.py, pipeline/repositorio.py e pipeline/executar.py (issue #139).

Um cliente falso responde por caminho; nada aqui faz chamada de rede.
"""

from __future__ import annotations

import csv
from datetime import date

import pytest

from metricas.cfr import Deploy
from metricas.recuperacao import Run
from pipeline import executar
from pipeline.coleta_runs import ResultadoRuns
from pipeline.github_client import GitHubAPIError
from pipeline.repositorio import (
    Janela,
    comparar,
    deploys_por_unidade,
    metricas_da_unidade,
    metricas_dos_runs,
    montar_com_commits,
)
from pipeline.selecao import (
    Avaliacao,
    Funil,
    avaliar_candidatos,
    buscar_candidatos,
    consulta_busca,
    contar_contribuidores,
    embaralhar,
    tem_actions,
)

JANELA = Janela(date(2025, 1, 1), date(2025, 12, 31))


class ClienteFalso:
    def __init__(self, gets=None, paginas=None, headers=None, graphql=None):
        self.gets = gets or {}
        self.paginas = paginas or {}
        self.headers = headers or {}
        self._graphql = graphql or {"data": {"repository": None}}
        self.chamadas = []

    def _resposta(self, caminho, params):
        self.chamadas.append((caminho, params))
        resposta = self.gets.get(caminho)
        if isinstance(resposta, Exception):
            raise resposta
        if callable(resposta):
            return resposta(params)
        return resposta

    def get(self, caminho, params=None):
        return self._resposta(caminho, params)

    def requisitar(self, caminho, params=None):
        return self._resposta(caminho, params), self.headers.get(caminho, {})

    def paginar(self, caminho, params=None, *, chave=None):
        self.chamadas.append((caminho, params))
        valor = self.paginas.get(caminho, [])
        if callable(valor):
            valor = valor(params)
        yield from valor

    def graphql(self, consulta, variaveis):
        return self._graphql


# --- selecao ---------------------------------------------------------------

def test_consulta_busca_por_faixa():
    assert consulta_busca((1000, 1999), date(2025, 1, 1)) == "stars:1000..1999 archived:false pushed:>=2025-01-01"
    assert consulta_busca((50000, None), date(2025, 1, 1)).startswith("stars:>=50000 ")


def item(nome, estrelas=1500):
    owner, repo = nome.split("/")
    return {
        "full_name": nome, "name": repo, "owner": {"login": owner}, "stargazers_count": estrelas,
        "language": None, "default_branch": "main", "created_at": "2020-01-01T00:00:00Z",
    }


def test_buscar_candidatos_junta_faixas_sem_repetir():
    def por_faixa(params):
        return [item("a/x"), item("b/y")] if "1000..1999" in params["q"] else [item("b/y"), item("c/z")]

    cliente = ClienteFalso(paginas={"search/repositories": por_faixa})
    candidatos = buscar_candidatos(cliente, [(1000, 1999), (2000, None)], date(2025, 1, 1))
    assert [c["full_name"] for c in candidatos] == ["a/x", "b/y", "c/z"]
    assert candidatos[0]["linguagem"] == ""


def test_embaralhar_e_reprodutivel():
    base = [{"full_name": str(i)} for i in range(20)]
    assert embaralhar(base, 42) == embaralhar(base, 42)
    assert embaralhar(base, 42) != base


def test_tem_actions():
    assert tem_actions(ClienteFalso(gets={"repos/o/r/actions/workflows": {"total_count": 2}}), "o", "r")
    assert not tem_actions(ClienteFalso(gets={"repos/o/r/actions/workflows": {"total_count": 0}}), "o", "r")


def test_contribuidores_pela_ultima_pagina_do_link():
    link = (
        '<https://api.github.com/repositories/1/contributors?per_page=1&anon=true&page=2>; rel="next", '
        '<https://api.github.com/repositories/1/contributors?per_page=1&anon=true&page=347>; rel="last"'
    )
    cliente = ClienteFalso(gets={"repos/o/r/contributors": [{}]}, headers={"repos/o/r/contributors": {"Link": link}})
    assert contar_contribuidores(cliente, "o", "r") == 347


def test_contribuidores_sem_link_e_lista_muito_grande():
    assert contar_contribuidores(ClienteFalso(gets={"repos/o/r/contributors": [{}]}), "o", "r") == 1
    erro = ClienteFalso(gets={"repos/o/r/contributors": GitHubAPIError(403, "u", "too large")})
    assert contar_contribuidores(erro, "o", "r") is None


def roteiro_de_avaliacoes():
    """Resultado programado por candidato: descarte (motivo, etapa) ou aceito."""
    return {
        "o/r0": ("sem_actions", "com_actions"),
        "o/r1": None,
        "o/r2": ("menos_de_5_releases", "min_5_releases"),
        "o/r3": None,
        "o/r4": ("erro_api", "amostra_final"),
        "o/r5": None,
        "o/r6": None,
    }


def avaliar_por_roteiro(roteiro, atraso=None):
    import time

    def avaliar(c):
        if atraso:
            time.sleep(atraso(c))
        r = roteiro.get(c["full_name"])
        if r is None:
            return Avaliacao(c, None, linha={"owner": "o", "repo": c["full_name"]})
        return Avaliacao(c, r[0], r[1])

    return avaliar


@pytest.mark.parametrize("workers", [1, 3, 8])
def test_avaliar_para_no_alvo_e_monta_o_funil(workers):
    candidatos = [{"full_name": f"o/r{i}"} for i in range(10)]
    funil = Funil()
    registrados = []
    avaliar_candidatos(
        candidatos, 3, funil, avaliar_por_roteiro(roteiro_de_avaliacoes()), registrados.append, workers=workers
    )
    assert funil.aceitos == 3
    assert funil.avaliados == 6
    assert [a.candidato["full_name"] for a in registrados] == ["o/r1", "o/r3", "o/r5"]
    linhas = {l["etapa"]: l for l in funil.linhas()}
    assert linhas["candidatos_busca"]["restantes"] == 10
    assert linhas["avaliados"]["descartados"] == 4
    assert linhas["com_actions"]["restantes"] == 5
    assert linhas["min_5_releases"]["restantes"] == 4
    assert linhas["min_50_runs"]["restantes"] == 4
    assert linhas["amostra_final"]["restantes"] == 3
    assert "1 por erro da API" in linhas["amostra_final"]["motivo"]


def test_paralelo_mantem_a_ordem_do_sorteio_mesmo_com_tempos_diferentes():
    # Os primeiros candidatos demoram mais: terminam depois dos seguintes, mas
    # o funil e a amostra seguem a ordem da fila, igual a execucao sequencial.
    candidatos = [{"full_name": f"o/r{i}"} for i in range(7)]
    atraso = lambda c: 0.05 if c["full_name"] in ("o/r0", "o/r1") else 0.0  # noqa: E731
    sequencial, paralelo = Funil(), Funil()
    reg_seq, reg_par = [], []
    roteiro = roteiro_de_avaliacoes()
    avaliar_candidatos(candidatos, 3, sequencial, avaliar_por_roteiro(roteiro), reg_seq.append, workers=1)
    avaliar_candidatos(candidatos, 3, paralelo, avaliar_por_roteiro(roteiro, atraso), reg_par.append, workers=4)
    assert paralelo.descartes == sequencial.descartes
    assert paralelo.linhas() == sequencial.linhas()
    assert [a.linha for a in reg_par] == [a.linha for a in reg_seq]


def test_paralelo_usa_varias_threads():
    import threading

    nomes = set()
    barreira = threading.Barrier(3, timeout=2)

    def avaliar(c):
        nomes.add(threading.current_thread().name)
        barreira.wait()  # so passa se 3 candidatos estiverem sendo avaliados ao mesmo tempo
        return Avaliacao(c, "sem_actions", "com_actions")

    candidatos = [{"full_name": f"o/r{i}"} for i in range(3)]
    avaliar_candidatos(candidatos, 1, Funil(), avaliar, lambda a: None, workers=3)
    assert len(nomes) == 3


def test_erro_numa_thread_chega_na_ordem_e_interrompe():
    candidatos = [{"full_name": f"o/r{i}"} for i in range(5)]
    funil = Funil()

    def avaliar(c):
        if c["full_name"] == "o/r2":
            raise RuntimeError("interrompe")
        return Avaliacao(c, "sem_actions", "com_actions")

    with pytest.raises(RuntimeError):
        avaliar_candidatos(candidatos, 10, funil, avaliar, lambda a: None, workers=3)
    # o/r0 e o/r1 ja tinham sido aplicados; nada depois do erro entra no funil.
    assert funil.avaliados == 2
    assert [d["full_name"] for d in funil.descartes] == ["o/r0", "o/r1"]


# --- repositorio -------------------------------------------------------------

def test_janela_iso():
    assert JANELA.inicio_iso == "2025-01-01T00:00:00Z"
    assert JANELA.fim_iso == "2026-01-01T00:00:00Z"


def test_deploys_por_unidade():
    releases = [
        {"tag_name": "v2", "published_at": "2025-03-01T00:00:00Z", "draft": False, "prerelease": False},
        {"tag_name": "v2-rc", "published_at": "2025-02-01T00:00:00Z", "draft": False, "prerelease": True},
        {"tag_name": "rascunho", "published_at": None, "draft": True, "prerelease": False},
        {"tag_name": "v1", "published_at": "2025-01-10T00:00:00Z", "draft": False, "prerelease": False},
    ]
    tags = [{"name": "v1", "data": "2025-01-09T00:00:00Z"}]
    u = deploys_por_unidade(releases, tags)
    assert [d.tag_name for d in u["release"]] == ["v1", "v2"]
    assert [d.tag_name for d in u["release_pre"]] == ["v1", "v2-rc", "v2"]
    assert u["tag"] == [Deploy("v1", "2025-01-09T00:00:00Z")]


def compare(commits_por_par):
    gets = {}
    for (base, head), datas in commits_por_par.items():
        caminho = f"repos/o/r/compare/{base}...{head}"
        if datas is None:
            gets[caminho] = GitHubAPIError(404, caminho)
        else:
            gets[caminho] = {"commits": [{"commit": {"author": {"date": d}}} for d in datas]}
    return ClienteFalso(gets=gets)


def test_montar_com_commits_so_compara_deploys_da_janela():
    deploys = [
        Deploy("v0", "2024-06-01T00:00:00Z"),  # fora: so serve de base
        Deploy("v1", "2025-03-15T00:00:00Z"),
        Deploy("v2", "2025-05-01T00:00:00Z"),
    ]
    cliente = compare({("v0", "v1"): ["2025-03-02T00:00:00Z"], ("v1", "v2"): None})
    montadas, n_404, _ = montar_com_commits(cliente, "o", "r", deploys, JANELA)
    assert [m.tag_name for m in montadas] == ["v1", "v2"]
    assert montadas[0].commits_datas == ["2025-03-02T00:00:00Z"]
    assert montadas[1].ignorada
    assert n_404 == 1
    assert len(cliente.chamadas) == 2


def test_compare_grande_e_ignorado_sem_baixar_as_outras_paginas():
    deploys = [Deploy("v10.9.7", "2025-03-01T00:00:00Z"), Deploy("pkg@11.0.0", "2025-03-02T00:00:00Z")]
    cliente = ClienteFalso(gets={"repos/o/r/compare/v10.9.7...pkg%4011.0.0": {"total_commits": 5000, "commits": []}})
    montadas, n_404, n_grandes = montar_com_commits(cliente, "o", "r", deploys, JANELA)
    assert montadas[1].ignorada
    assert (n_404, n_grandes) == (0, 1)
    assert len(cliente.chamadas) == 1


def test_compare_paginado_junta_as_paginas():
    def paginas(params):
        n = 100 if params["page"] == 1 else 3
        return {"total_commits": 103, "commits": [{"commit": {"author": {"date": "2025-03-01T00:00:00Z"}}}] * n}

    cliente = ClienteFalso(gets={"repos/o/r/compare/a...b": paginas})
    assert len(comparar(cliente, "o", "r", "a", "b")) == 103


def test_compare_outro_erro_propaga():
    cliente = ClienteFalso(gets={"repos/o/r/compare/a...b": GitHubAPIError(500, "u")})
    with pytest.raises(GitHubAPIError):
        comparar(cliente, "o", "r", "a", "b")


def test_primeiro_deploy_da_historia_e_ignorado_sem_chamar_compare():
    cliente = compare({})
    montadas, _, _ = montar_com_commits(cliente, "o", "r", [Deploy("v1", "2025-03-15T00:00:00Z")], JANELA)
    assert montadas[0].ignorada
    assert cliente.chamadas == []


def test_tag_com_caractere_especial_vai_codificada_na_url():
    deploys = [Deploy("pkg/a b", "2025-03-01T00:00:00Z"), Deploy("pkg/c", "2025-03-02T00:00:00Z")]
    cliente = compare({("pkg/a%20b", "pkg/c"): []})
    montar_com_commits(cliente, "o", "r", deploys, JANELA)
    assert cliente.chamadas[0][0] == "repos/o/r/compare/pkg/a%20b...pkg/c"


def test_metricas_da_unidade_exemplo_do_enunciado():
    deploys = [Deploy("v1.0.0", "2025-01-02T00:00:00Z"), Deploy("v1.1.0", "2025-03-15T00:00:00Z")]
    cliente = compare({
        ("v1.0.0", "v1.1.0"): ["2025-03-02T00:00:00Z", "2025-03-10T00:00:00Z", "2025-03-14T00:00:00Z"],
    })
    linha = metricas_da_unidade(cliente, "o", "r", "release", deploys, JANELA, max_compares=10)
    assert linha["n_release"] == 2
    assert linha["lt_a_release_dias"] == 13
    assert linha["lt_b_release_dias"] == 5
    assert linha["lt_release_n_avaliadas"] == 1
    assert linha["lt_release_omitido"] is False
    assert linha["cfr_b_release"] == 0.0
    assert linha["df_release_semana"] == pytest.approx(2 / (365 / 7))


def test_metricas_da_unidade_acima_do_limite_de_compares_omite_lead_time():
    deploys = [Deploy(f"t{i}", f"2025-02-{i + 1:02d}T00:00:00Z") for i in range(5)]
    cliente = compare({})
    linha = metricas_da_unidade(cliente, "o", "r", "tag", deploys, JANELA, max_compares=3)
    assert linha["lt_tag_omitido"] is True
    assert linha["lt_a_tag_dias"] is None
    assert linha["n_tag"] == 5
    assert cliente.chamadas == []


def test_metricas_dos_runs():
    runs = ResultadoRuns(
        runs=[
            Run(1, "success", "2025-03-10T09:00:00Z", "2025-03-10T09:00:00Z"),
            Run(1, "failure", "2025-03-10T10:00:00Z", "2025-03-10T10:00:00Z"),
            Run(1, "success", "2025-03-10T11:00:00Z", "2025-03-10T11:00:00Z"),
            Run(1, "cancelled", "2025-03-10T12:00:00Z", "2025-03-10T12:00:00Z"),
        ],
        meses_no_teto=2,
    )
    linha = metricas_dos_runs(runs)
    assert linha["n_runs_validos"] == 3
    assert linha["n_runs_ignorados"] == 1
    assert linha["cfr_a"] == pytest.approx(1 / 3)
    assert linha["recuperacao_mediana_horas"] == pytest.approx(1.0)
    assert linha["meses_no_teto_runs"] == 2


# --- executar (ponta a ponta com cliente falso) ------------------------------

CONFIG = """
janela: {inicio: 2025-01-01, fim: 2025-12-31}
amostra: {alvo: 1, semente: 1}
busca: {faixas_estrelas: [[1000, null]]}
inclusao: {min_releases: 2, min_runs_validos: 3}
coleta: {max_compares_por_unidade: 50, cache: .cache}
saida:
  dataset: out/dataset.csv
  repositorios: out/repos.csv
  funil: out/funil.csv
  descartes: out/descartes.csv
"""


def releases_ok():
    return [
        {"tag_name": "v1.0.0", "published_at": "2025-02-01T00:00:00Z", "draft": False, "prerelease": False},
        {"tag_name": "v1.0.1", "published_at": "2025-02-03T00:00:00Z", "draft": False, "prerelease": False},
    ]


def runs_ok(params):
    if params["created"].startswith("2025-03"):
        runs = [
            {"workflow_id": 1, "conclusion": c, "run_started_at": f"2025-03-0{i + 1}T00:00:00Z",
             "created_at": f"2025-03-0{i + 1}T00:00:00Z", "updated_at": f"2025-03-0{i + 1}T00:00:00Z"}
            for i, c in enumerate(["success", "failure", "success"])
        ]
        return {"total_count": 3, "workflow_runs": runs}
    return {"total_count": 0, "workflow_runs": []}


def test_ler_config_resolve_caminhos(tmp_path):
    (tmp_path / "c.yaml").write_text(CONFIG)
    cfg = executar.ler_config(tmp_path / "c.yaml")
    assert cfg.janela.fim == date(2025, 12, 31)
    assert cfg.faixas == [(1000, None)]
    assert cfg.saida["dataset"] == tmp_path / "out/dataset.csv"


@pytest.mark.parametrize("threads", [1, 3])
def test_coleta_ponta_a_ponta_gera_os_csvs(tmp_path, threads):
    (tmp_path / "c.yaml").write_text(CONFIG)
    cfg = executar.ler_config(tmp_path / "c.yaml")
    cfg.alvo = 2
    cfg.threads = threads
    cliente = ClienteFalso(
        paginas={
            "search/repositories": [item("a/semactions"), item("b/poucas"), item("c/ok"), item("d/erro")],
            "repos/c/ok/releases": releases_ok(),
            "repos/b/poucas/releases": releases_ok()[:1],
            "repos/d/erro/releases": releases_ok(),
        },
        gets={
            "repos/a/semactions/actions/workflows": {"total_count": 0},
            "repos/b/poucas/actions/workflows": {"total_count": 1},
            "repos/c/ok/actions/workflows": {"total_count": 1},
            "repos/d/erro/actions/workflows": {"total_count": 1},
            "repos/c/ok/actions/runs": runs_ok,
            "repos/d/erro/actions/runs": GitHubAPIError(451, "u", "bloqueado"),
            "repos/c/ok/compare/v1.0.0...v1.0.1": {"commits": [{"commit": {"author": {"date": "2025-02-02T00:00:00Z"}}}]},
            "repos/c/ok/contributors": [{}],
        },
    )
    coleta = executar.Coleta(cliente, cfg, log=lambda _: None)
    coleta.rodar()
    executar.gravar_saidas(coleta)

    with cfg.saida["dataset"].open() as f:
        linhas = list(csv.DictReader(f))
    assert [(l["owner"], l["repo"]) for l in linhas] == [("c", "ok")]
    assert list(linhas[0]) == executar.colunas_dataset()
    assert linhas[0]["cfr_a"] == str(1 / 3)
    assert linhas[0]["lt_a_release_dias"] == "1.0"

    with cfg.saida["funil"].open() as f:
        funil = {l["etapa"]: int(l["restantes"]) for l in csv.DictReader(f)}
    assert funil == {
        "candidatos_busca": 4, "avaliados": 4, "com_actions": 3,
        "min_5_releases": 2, "min_50_runs": 1, "amostra_final": 1,
    }
    with cfg.saida["descartes"].open() as f:
        motivos = {l["full_name"]: l["motivo"] for l in csv.DictReader(f)}
    assert motivos == {"a/semactions": "sem_actions", "b/poucas": "menos_de_5_releases", "d/erro": "erro_api"}


def test_idade_em_anos():
    assert executar.idade_anos("2020-12-31T00:00:00Z", date(2025, 12, 31)) == pytest.approx(5.0, abs=0.01)


def test_fila_adiantada_maior_nao_muda_o_resultado():
    candidatos = [{"full_name": f"o/r{i}"} for i in range(7)]
    roteiro = roteiro_de_avaliacoes()
    base, largo = Funil(), Funil()
    avaliar_candidatos(candidatos, 3, base, avaliar_por_roteiro(roteiro), lambda a: None, workers=1)
    avaliar_candidatos(candidatos, 3, largo, avaliar_por_roteiro(roteiro), lambda a: None, workers=3, adiantar=30)
    assert largo.descartes == base.descartes
    assert largo.linhas() == base.linhas()


def test_compare_422_diff_demorado_conta_como_grande():
    erro = GitHubAPIError(422, "u", "Server Error: Sorry, this diff is taking too long to generate.")
    cliente = ClienteFalso(gets={"repos/o/r/compare/a...b": erro})
    assert comparar(cliente, "o", "r", "a", "b") == "truncado"


def test_compare_422_de_outro_tipo_propaga():
    cliente = ClienteFalso(gets={"repos/o/r/compare/a...b": GitHubAPIError(422, "u", "Validation Failed")})
    with pytest.raises(GitHubAPIError):
        comparar(cliente, "o", "r", "a", "b")
