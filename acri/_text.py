"""_text — tokenization shared by corpus (indexing) and compass (scoring).

Internal to the package: both sides must tokenize identically or BM25 scores
against a corpus the query was never consistently split against.
"""
from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Function words filtered before scoring. Found via assay/recall.py: without
# this, a query sharing only "the"/"is"/"what" with a tool description still
# scores above zero, so pure-noise queries never come back empty — the
# resolver looks confident about a tool it has no real signal for.
_STOPWORDS = frozenset("""
    a an the is are was were be been am of in on at to for with and or but
    this that these those what which who me my you your it its we they
    do does did
""".split())


def tokenize(text: str) -> list[str]:
    # Strip apostrophes before splitting: "user's" -> "users" as one token,
    # not "user" + a stray "s" that then matches every other possessive.
    text = text.lower().replace("'", "").replace("’", "")
    return [t for t in _TOKEN_RE.findall(text) if t not in _STOPWORDS]
