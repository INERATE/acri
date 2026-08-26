from acri.corpus import Tool, index
from acri.escape_hatch import find_more_tools


def _corpus():
    return index([
        Tool(name="github_get_pull_request", description="fetch pull request details from github by number"),
        Tool(name="github_merge_pull_request", description="merge an approved pull request into the default branch"),
        Tool(name="postgres_query", description="execute sql against a postgres database table"),
    ])


def test_find_more_tools_excludes_names_already_offered():
    found = find_more_tools("pull request", _corpus(), exclude=["github_get_pull_request"], k=4)
    assert {t["name"] for t in found} == {"github_merge_pull_request"}


def test_find_more_tools_returns_name_and_description():
    found = find_more_tools("postgres sql", _corpus(), k=1)
    assert found == [{"name": "postgres_query", "description": "execute sql against a postgres database table"}]


def test_find_more_tools_respects_k_after_excluding():
    found = find_more_tools("pull request", _corpus(), exclude=[], k=1)
    assert len(found) == 1
