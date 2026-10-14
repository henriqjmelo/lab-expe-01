from __future__ import annotations

from datetime import timedelta

import pytest

from metricas.ci import cfr_ci_com_reexecucoes, tempo_feedback
from metricas.fluxo import distribuicao_trabalho, tipo_commit
from metricas.recuperacao import Run
from metricas.revert import CommitDeRelease, ReleaseAvaliavel, cfr_revert, releases_revertidas


def run(conclusion, tentativa=1, inicio="2025-03-10T10:00:00Z", fim="2025-03-10T10:12:00Z"):
    return Run(1, conclusion, inicio, fim, run_attempt=tentativa, head_sha="abc")


def test_cfr_com_reexecucoes_e_um_limite_pessimista():
    runs = [run("success"), run("success", 2), run("failure"), run("failure", 3), run("cancelled", 2)]
    r = cfr_ci_com_reexecucoes(runs)
    assert r["n_validos"] == 4
    assert r["cfr"] == pytest.approx(2 / 4)
    assert r["cfr_com_reexecucoes"] == pytest.approx(3 / 4)
    assert r["taxa_reexecucao"] == pytest.approx(2 / 4)
    assert (r["n_reexecutados_sucesso"], r["n_reexecutados_falha"]) == (1, 1)


def test_cfr_com_reexecucoes_sem_runs_validos():
    r = cfr_ci_com_reexecucoes([run("skipped")])
    assert r["cfr"] is None and r["cfr_com_reexecucoes"] is None and r["taxa_reexecucao"] is None


def test_tempo_feedback_mediana_em_minutos_so_dos_validos():
    runs = [
        run("success", fim="2025-03-10T10:10:00Z"),
        run("failure", fim="2025-03-10T10:30:00Z"),
        run("cancelled", fim="2025-03-10T15:00:00Z"),
        run("success", inicio="2025-03-10T10:00:00Z", fim="2025-03-10T09:00:00Z"),
    ]
    assert tempo_feedback(runs) == {"n_runs": 2, "mediana_minutos": pytest.approx(20)}
    assert tempo_feedback([])["mediana_minutos"] is None


RELEASES = [
    ReleaseAvaliavel("v1", "2025-03-01T00:00:00Z"),
    ReleaseAvaliavel("v2", "2025-03-10T00:00:00Z"),
    ReleaseAvaliavel("v3", "2025-06-01T00:00:00Z"),
    ReleaseAvaliavel("v4", "2025-12-20T00:00:00Z"),
]


def test_release_revertida_por_commit_de_release_seguinte():
    commits = [
        CommitDeRelease("aaaaaaa111", "v1"),
        CommitDeRelease("bbbbbbb222", "v2", reverte=["aaaaaaa"]),
        CommitDeRelease("ccccccc333", "v3", reverte=["bbbbbbb222"]),
    ]
    revertidas = releases_revertidas(RELEASES, commits)
    assert revertidas == {"v1": timedelta(days=9)}


def test_revert_dentro_da_mesma_release_nao_conta():
    commits = [CommitDeRelease("aaaaaaa111", "v1"), CommitDeRelease("ddddddd444", "v1", reverte=["aaaaaaa111"])]
    assert releases_revertidas(RELEASES, commits) == {}


def test_revert_de_sha_desconhecido_ou_curto_demais_e_ignorado():
    commits = [CommitDeRelease("aaaaaaa111", "v1"), CommitDeRelease("bbbbbbb222", "v2", reverte=["ffffff", "abc"])]
    assert releases_revertidas(RELEASES, commits) == {}


def test_cfr_revert_com_censura_no_fim_da_janela():
    commits = [CommitDeRelease("aaaaaaa111", "v1"), CommitDeRelease("bbbbbbb222", "v2", reverte=["aaaaaaa111"])]
    releases = [*RELEASES, ReleaseAvaliavel("v0", "2025-02-01T00:00:00Z", avaliavel=False)]
    r = cfr_revert(releases, commits, fim="2026-01-01T00:00:00Z")
    assert r == {"n_avaliadas": 3, "n_revertidas": 1, "n_censuradas": 1, "cfr": pytest.approx(1 / 3)}


def test_cfr_revert_sem_releases():
    assert cfr_revert([], [], fim="2026-01-01T00:00:00Z")["cfr"] is None


@pytest.mark.parametrize(
    "mensagem, tipo",
    [
        ("feat: novo endpoint", "feat"),
        ("fix(api): corrige timeout", "fix"),
        ("refactor!: muda contrato", "refactor"),
        ('Revert "feat: x"', "revert"),
        ("revert: desfaz y", "revert"),
        ("Fix typo", None),
        ("wip: algo", None),
        ("", None),
        (None, None),
        (float("nan"), None),
    ],
)
def test_tipo_commit(mensagem, tipo):
    assert tipo_commit(mensagem) == tipo


def test_distribuicao_trabalho():
    r = distribuicao_trabalho(["feat: a", "fix: b", "fix: c", "atualiza readme", 'Revert "fix: c"'])
    assert r["n_commits"] == 5
    assert r["prop_convencional"] == pytest.approx(4 / 5)
    assert r["adota_convencional"] is True
    assert r["prop_fix"] == pytest.approx(2 / 4)
    assert r["prop_feat"] == pytest.approx(1 / 4)
    assert r["prop_revert"] == pytest.approx(1 / 5)


def test_distribuicao_trabalho_sem_padrao_ou_vazia():
    assert distribuicao_trabalho(["atualiza", "corrige"])["prop_fix"] is None
    assert distribuicao_trabalho(["atualiza"])["adota_convencional"] is False
    assert distribuicao_trabalho([])["prop_convencional"] is None
