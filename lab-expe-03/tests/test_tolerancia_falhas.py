"""Testes da tolerancia a falhas da coleta (issue #139): retentativas por
repositorio, erro transitorio que interrompe sem descartar, erro inesperado que
vira descarte e CSVs parciais."""

from __future__ import annotations

import http.client
from datetime import date

import pytest

from pipeline import executar
from pipeline.executar import ColetaInterrompida, Config, Coleta, erro_transitorio
from pipeline.github_client import GitHubAPIError
from pipeline.repositorio import Janela
from pipeline.selecao import Avaliacao


def config(tmp_path, **extra):
    base = dict(
        janela=Janela(date(2025, 1, 1), date(2025, 12, 31)),
        alvo=10,
        semente=1,
        faixas=[(1000, None)],
        min_releases=1,
        min_runs=1,
        max_compares=10,
        cache=tmp_path / ".cache",
        saida={n: tmp_path / f"{n}.csv" for n in ("dataset", "repositorios", "funil", "descartes")},
        espera_retentativa=30.0,
    )
    base.update(extra)
    return Config(**base)


CANDIDATO = {"full_name": "o/r", "owner": "o", "repo": "r", "default_branch": "main"}


class ClienteSequencia:
    """actions/workflows responde a sequencia programada (erro ou valor), um item por chamada."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)

    def get(self, caminho, params=None):
        resposta = self.respostas.pop(0)
        if isinstance(resposta, BaseException):
            raise resposta
        return resposta


@pytest.mark.parametrize(
    "erro, esperado",
    [
        (GitHubAPIError(502, "u"), True),
        (GitHubAPIError(0, "u", "sem rede"), True),
        (GitHubAPIError(403, "u", "secondary rate limit"), True),
        (GitHubAPIError(403, "u", "Repository access blocked"), False),
        (GitHubAPIError(404, "u"), False),
        (GitHubAPIError(451, "u"), False),
        (http.client.IncompleteRead(b""), True),
        (ConnectionResetError(), True),
        (KeyError("x"), False),
    ],
)
def test_classificacao_de_erro_transitorio(erro, esperado):
    assert erro_transitorio(erro) is esperado


def test_erro_transitorio_tenta_de_novo_e_segue(tmp_path):
    esperas = []
    cliente = ClienteSequencia(GitHubAPIError(502, "u"), {"total_count": 0})
    coleta = Coleta(cliente, config(tmp_path), log=lambda _: None, dormir=esperas.append)
    assert coleta.avaliar(CANDIDATO).motivo == "sem_actions"
    assert esperas == [30.0]


def test_erro_transitorio_persistente_interrompe_sem_descartar(tmp_path):
    esperas = []
    cliente = ClienteSequencia(*[GitHubAPIError(503, "u")] * 3)
    coleta = Coleta(cliente, config(tmp_path), log=lambda _: None, dormir=esperas.append)
    with pytest.raises(ColetaInterrompida):
        coleta.avaliar(CANDIDATO)
    assert esperas == [30.0, 60.0]
    assert coleta.funil.descartes == []


def test_erro_inesperado_repetido_vira_descarte(tmp_path):
    coleta = Coleta(ClienteSequencia(), config(tmp_path), log=lambda _: None, dormir=lambda _: None)
    coleta._avaliar = lambda c, estado: (_ for _ in ()).throw(KeyError("default_branch"))
    avaliacao = coleta.avaliar(CANDIDATO)
    assert (avaliacao.motivo, avaliacao.etapa) == ("erro_inesperado", "com_actions")
    coleta.funil.descartar(CANDIDATO, avaliacao.etapa, avaliacao.motivo)
    assert "erro inesperado" in coleta.funil.linhas()[2]["motivo"]


def test_erro_permanente_descarta_sem_retentativa(tmp_path):
    esperas = []
    cliente = ClienteSequencia(GitHubAPIError(451, "u", "bloqueado"))
    coleta = Coleta(cliente, config(tmp_path), log=lambda _: None, dormir=esperas.append)
    assert coleta.avaliar(CANDIDATO).motivo == "erro_api"
    assert esperas == []


def test_grava_csvs_parciais_a_cada_n_aceitos(tmp_path):
    cfg = config(tmp_path, gravar_parcial_a_cada=2)
    coleta = Coleta(None, cfg, log=lambda _: None)
    coleta.registrar(Avaliacao({}, None, linha={"owner": "a", "repo": "1"}))
    assert not cfg.saida["dataset"].exists()
    coleta.registrar(Avaliacao({}, None, linha={"owner": "a", "repo": "2"}))
    assert len(cfg.saida["dataset"].read_text().splitlines()) == 3


def test_main_devolve_75_e_grava_parcial_em_erro_transitorio(tmp_path, monkeypatch):
    (tmp_path / "c.yaml").write_text(
        "janela: {inicio: 2025-01-01, fim: 2025-12-31}\n"
        "amostra: {alvo: 1, semente: 1}\n"
        "busca: {faixas_estrelas: [[1000, null]]}\n"
        "inclusao: {min_releases: 1, min_runs_validos: 1}\n"
        "coleta: {max_compares_por_unidade: 1, cache: .cache}\n"
        "saida: {dataset: d.csv, repositorios: r.csv, funil: f.csv, descartes: x.csv}\n"
    )
    monkeypatch.setenv("GITHUB_TOKEN", "t")

    def falha(self):
        raise ColetaInterrompida("o/r: HTTP 502")

    monkeypatch.setattr(Coleta, "rodar", falha)
    assert executar.main(["--config", str(tmp_path / "c.yaml")]) == executar.SAIDA_TRANSITORIA
    assert (tmp_path / "f.csv").exists()


def test_main_devolve_130_no_ctrl_c(tmp_path, monkeypatch):
    (tmp_path / "c.yaml").write_text(
        "janela: {inicio: 2025-01-01, fim: 2025-12-31}\n"
        "amostra: {alvo: 1, semente: 1}\n"
        "busca: {faixas_estrelas: [[1000, null]]}\n"
        "inclusao: {min_releases: 1, min_runs_validos: 1}\n"
        "coleta: {max_compares_por_unidade: 1, cache: .cache}\n"
        "saida: {dataset: d.csv, repositorios: r.csv, funil: f.csv, descartes: x.csv}\n"
    )
    monkeypatch.setenv("GITHUB_TOKEN", "t")

    def interrompe(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(Coleta, "rodar", interrompe)
    assert executar.main(["--config", str(tmp_path / "c.yaml")]) == executar.SAIDA_INTERROMPIDA


def test_gravar_csv_e_atomico(tmp_path):
    destino = tmp_path / "x.csv"
    executar.gravar_csv(destino, [{"a": 1}], ["a"])
    assert destino.read_text().splitlines() == ["a", "1"]
    assert not (tmp_path / "x.csv.tmp").exists()
