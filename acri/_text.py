"""_text — tokenization shared by corpus (indexing) and compass (scoring).

Internal to the package: both sides must tokenize identically or BM25 scores
against a corpus the query was never consistently split against.
"""
from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Standard English function words (the NLTK stoplist's non-contraction
# core), filtered before scoring. Started as a smaller ad-hoc set; expanded
# to this external, non-cherry-picked list after "into" — missing from the
# original set — tied github_merge_pull_request with translate/salesforce
# tools that happened to also contain "into". A hand-patched one-word-at-a-
# time list invites tuning to whichever queries you happen to be looking at;
# a standard external stoplist doesn't. See assay/diagnose.py.
_STOPWORDS = frozenset("""
    a an the is are was were be been being am of in on at to for with and or
    but this that these those what which who whom me my you your it its we
    they do does did into from by about up down out off over under again
    further then once here there when where why how all any both each few
    more most other some such no nor not only own same so than too very s t
    can will just now if because as until while against between during
    before after above below
""".split())


def tokenize(text: str) -> list[str]:
    # Strip apostrophes before splitting: "user's" -> "users" as one token,
    # not "user" + a stray "s" that then matches every other possessive.
    text = text.lower().replace("'", "").replace("’", "")
    return [t for t in _TOKEN_RE.findall(text) if t not in _STOPWORDS]
