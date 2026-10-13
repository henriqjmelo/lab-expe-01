"""Tags com data via GraphQL, para a variante "tag como unidade de deploy" da RQ 07 (issue #139).

Tags nao tem data propria: usa a data de autoria do commit apontado. Pela REST
isso custa uma chamada por tag (pipeline/coleta_releases.listar_tags_com_data);
na coleta completa, com repositorios de centenas de tags, a consulta GraphQL
abaixo traz 100 tags ja com a data por chamada. Tags anotadas apontam para um
objeto Tag, que por sua vez aponta para o commit.
"""

from __future__ import annotations

from pipeline.github_client import GitHubClient

CONSULTA_TAGS = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    refs(refPrefix: "refs/tags/", first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        target {
          __typename
          ... on Commit { oid authoredDate }
          ... on Tag { target { __typename ... on Commit { oid authoredDate } } }
        }
      }
    }
  }
}
"""


def _commit_da_tag(alvo: dict | None) -> dict | None:
    if not alvo:
        return None
    if alvo.get("__typename") == "Commit":
        return alvo
    if alvo.get("__typename") == "Tag":
        return _commit_da_tag(alvo.get("target"))
    return None


def listar_tags_graphql(cliente: GitHubClient, owner: str, repo: str) -> list[dict]:
    """[{name, sha, data}] em ordem cronologica. Tags que apontam para arvore/blob ficam de fora."""
    tags = []
    cursor = None
    while True:
        resposta = cliente.graphql(CONSULTA_TAGS, {"owner": owner, "name": repo, "cursor": cursor})
        repositorio = ((resposta or {}).get("data") or {}).get("repository")
        if not repositorio:
            break
        refs = repositorio["refs"]
        for no in refs["nodes"]:
            commit = _commit_da_tag(no.get("target"))
            if commit and commit.get("authoredDate"):
                tags.append({"name": no["name"], "sha": commit["oid"], "data": commit["authoredDate"]})
        if not refs["pageInfo"]["hasNextPage"]:
            break
        cursor = refs["pageInfo"]["endCursor"]
    return sorted(tags, key=lambda t: t["data"])
