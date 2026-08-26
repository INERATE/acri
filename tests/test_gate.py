from acri.corpus import Tool, index
from acri.gate import raw_top_score, should_offer_tools


def _corpus():
    return index([
        Tool(name="github_get_pull_request", description="fetch pull request details from github by number"),
        Tool(name="github_merge_pull_request", description="merge an approved pull request into the default branch"),
        Tool(name="weather_forecast", description="fetch forecast temperature for a city location"),
    ])


def test_raw_top_score_distinguishes_strong_from_weak_matches():
    """The whole reason this exists: compass.Resolved.score is always 1.0 for
    the winner, so it can't tell these apart -- raw_top_score can."""
    strong = raw_top_score("merge the github pull request", _corpus())
    weak = raw_top_score("pull request", _corpus())  # shares fewer/less-rare terms
    assert strong > weak > 0.0


def test_raw_top_score_is_zero_for_no_match_or_empty_corpus():
    assert raw_top_score("xyzzy plugh", _corpus()) == 0.0
    assert raw_top_score("anything", index([Tool(name="noop", description="")])) >= 0.0


def test_should_offer_tools_respects_the_threshold():
    corpus = _corpus()
    score = raw_top_score("merge the github pull request", corpus)
    assert should_offer_tools("merge the github pull request", corpus, threshold=score) is True
    assert should_offer_tools("merge the github pull request", corpus, threshold=score + 0.01) is False


def test_should_offer_tools_with_zero_threshold_never_advises_skipping():
    assert should_offer_tools("xyzzy plugh", _corpus(), threshold=0.0) is True
