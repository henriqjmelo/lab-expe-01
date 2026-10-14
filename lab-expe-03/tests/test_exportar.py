from __future__ import annotations

import csv
import gzip

import pytest

from metricas.lead_time import ReleaseComCommits
from pipeline.exportar import _gravar, linhas_commits, linhas_lead_time


def test_lead_time_por_release_exportado():
    montadas = [
        ReleaseComCommits("v1.0", "2025-03-01T00:00:00Z", ignorada=True),
        ReleaseComCommits("v1.1", "2025-03-15T00:00:00Z",
                          ["2025-03-02T00:00:00Z", "2025-03-10T00:00:00Z", "2025-03-14T00:00:00Z"]),
        ReleaseComCommits("v1.2", "2025-04-01T00:00:00Z", []),
    ]
    linhas = linhas_lead_time("o", "r", montadas)
    assert linhas[0]["ignorada"] is True and linhas[0]["lt_a_dias"] is None
    assert linhas[1]["lt_a_dias"] == pytest.approx(13)
    assert linhas[1]["lt_b_mediana_dias"] == pytest.approx(5)
    assert linhas[1]["n_commits"] == 3
    assert linhas[2]["n_commits"] == 0 and linhas[2]["lt_a_dias"] is None


def test_commits_com_primeira_linha_e_sha_revertido():
    brutos = [
        {"sha": "abc", "commit": {"author": {"date": "2025-01-01T00:00:00Z"},
                                  "message": 'Revert "feat: x"\n\nThis reverts commit 1234567890abcdef.'}},
        {"sha": "def", "commit": {"author": {"date": "2025-01-02T00:00:00Z"}, "message": "fix: y"}},
        {"sha": "ghi", "commit": {"author": {"date": "2025-01-03T00:00:00Z"}, "message": ""}},
    ]
    linhas = linhas_commits("o", "r", "v1", brutos)
    assert linhas[0]["mensagem"] == 'Revert "feat: x"'
    assert linhas[0]["reverte_sha"] == "1234567890abcdef"
    assert linhas[1]["reverte_sha"] == ""
    assert linhas[2]["mensagem"] == ""


def test_gravar_csv_simples_e_comprimido(tmp_path):
    linhas = [{"a": 1, "b": "x"}]
    _gravar(tmp_path / "t.csv", linhas, ("a", "b"))
    _gravar(tmp_path / "t.csv.gz", linhas, ("a", "b"))
    assert list(csv.DictReader(open(tmp_path / "t.csv"))) == [{"a": "1", "b": "x"}]
    assert list(csv.DictReader(gzip.open(tmp_path / "t.csv.gz", "rt"))) == [{"a": "1", "b": "x"}]


def test_gz_e_deterministico(tmp_path):
    _gravar(tmp_path / "a.csv.gz", [{"a": 1}], ("a",))
    _gravar(tmp_path / "b.csv.gz", [{"a": 1}], ("a",))
    assert (tmp_path / "a.csv.gz").read_bytes() == (tmp_path / "b.csv.gz").read_bytes()
