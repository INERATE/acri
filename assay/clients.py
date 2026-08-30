"""clients — construct a live provider client for accuracy.py, one per provider.

Just a thin wrapper over acri._client_factory (the same construction `acri up`
uses) keyed by acri.providers.PROVIDERS -- one table, so a new provider is one
entry there, not a duplicate copy here that can quietly drift out of sync.
"""
from __future__ import annotations

from acri._client_factory import client_for
from acri.providers import PROVIDERS

CLIENTS = {p: (lambda p=p: client_for(p)) for p in PROVIDERS}
