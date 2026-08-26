from acri.compass import resolve
from acri.corpus import Tool, index


def _corpus():
    return index([
        Tool(name="github_get_pull_request", description="fetch pull request details from github by number"),
        Tool(name="github_merge_pull_request", description="merge an approved pull request into the default branch"),
        Tool(name="postgres_query", description="execute sql against a postgres database table"),
        Tool(name="weather_forecast", description="fetch forecast temperature for a city location"),
    ])


def test_resolve_excludes_tools_with_no_shared_term():
    resolved = resolve("merge the github pull request", _corpus(), k=4)
    names = {r.tool.name for r in resolved}
    assert names == {"github_get_pull_request", "github_merge_pull_request"}


def test_resolve_ranks_the_stronger_match_first():
    resolved = resolve("merge the github pull request", _corpus(), k=4)
    assert resolved[0].tool.name == "github_merge_pull_request"


def test_resolve_confidence_is_relative_to_best_match():
    resolved = resolve("merge the github pull request", _corpus(), k=4)
    assert resolved[0].score == 1.0
    assert all(0.0 < r.score <= 1.0 for r in resolved)
    assert resolved == sorted(resolved, key=lambda r: r.score, reverse=True)


def test_resolve_returns_nothing_for_pure_noise():
    assert resolve("xyzzy plugh", _corpus(), k=5) == []


def test_resolve_respects_k():
    assert len(resolve("pull request", _corpus(), k=1)) == 1
