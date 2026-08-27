"""config — parses acri.yaml. docs/decisions.md: "declarative configuration".

Declares capabilities and limits, never control flow -- no steps/on_error/
conditionals, on purpose (see decisions.md). Requires PyYAML: `pip install
pyacri[yaml]`. Not imported from acri/__init__.py, so `import acri` alone never
needs it -- the core library stays dependency-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_SUPPORTED_VERSION = 1


@dataclass(frozen=True)
class ModelsConfig:
    default: str | None = None
    cheap: str | None = None


@dataclass(frozen=True)
class SandboxConfig:  # v1.1 resource/network/volume limits -- see acri.sandbox.sandboxed()
    image: str
    memory: str = "256m"
    cpus: float = 0.5
    network: bool = True
    volumes: dict[str, str] | None = None  # host path -> container path


@dataclass(frozen=True)
class McpEntry:
    name: str
    command: list[str] | None = None
    url: str | None = None
    sandbox: SandboxConfig | None = None  # command: entries only -- see _mcp_entry


@dataclass(frozen=True)
class Limits:
    timeout_ms: int | None = None
    max_cost_per_task_usd: float | None = None


@dataclass(frozen=True)
class Config:
    """Parsed acri.yaml. `k` and `limits` mirror acri.run()'s own parameters --
    limits aren't enforced yet (that's v1.0's held-back remainder)."""

    version: int
    models: ModelsConfig = field(default_factory=ModelsConfig)
    mcp: list[McpEntry] = field(default_factory=list)
    k: int = 5
    limits: Limits = field(default_factory=Limits)
    builtin: list[str] = field(default_factory=list)  # opt-in acri.builtin tool names


def _mcp_entry(raw: dict[str, Any]) -> McpEntry:
    command, url = raw.get("command"), raw.get("url")
    if bool(command) == bool(url):
        raise ValueError(f"mcp entry {raw.get('name')!r} needs exactly one of command or url")
    sandbox = raw.get("sandbox")
    if sandbox and not command:
        raise ValueError(f"mcp entry {raw.get('name')!r}: sandbox needs command, not url")
    return McpEntry(name=raw["name"], command=command, url=url,
                     sandbox=SandboxConfig(**sandbox) if sandbox else None)


def from_yaml(path: str | Path) -> Config:
    """Load and validate an acri.yaml. Raises ValueError on an unsupported
    version or a malformed mcp entry; yaml.YAMLError on invalid YAML."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    version = data.get("version")
    if version != _SUPPORTED_VERSION:
        raise ValueError(f"unsupported acri.yaml version: {version!r} (expected {_SUPPORTED_VERSION})")
    models = data.get("models") or {}
    resolve = data.get("resolve") or {}
    limits = data.get("limits") or {}
    return Config(
        version=version,
        models=ModelsConfig(default=models.get("default"), cheap=models.get("cheap")),
        mcp=[_mcp_entry(m) for m in data.get("mcp") or []],
        k=resolve.get("k", 5),
        limits=Limits(timeout_ms=limits.get("timeout_ms"), max_cost_per_task_usd=limits.get("max_cost_per_task_usd")),
        builtin=list((data.get("tools") or {}).get("builtin") or []),
    )
