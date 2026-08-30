"""_template — the acri init scaffold. Split out of cli.py (word-cap): this
is static content, not CLI parsing/dispatch logic.
"""
from __future__ import annotations

TEMPLATE = """\
version: 1

models:
  default: gemini-2.5-flash
  # Any other provider: prefix the model with its name, e.g.
  # "anthropic/claude-sonnet-4-6" or "ollama/qwen2.5-coder:32b" -- full list
  # and a config example for each: README.md "Supported providers".
  # cheap: a stateless, prefix-free tier only -- classification, extraction,
  # summarizing a tool result. See docs/architecture.md #4.4. Optional.
  # cheap: gemini-2.5-flash-lite

mcp:
  # - name: github
  #   command: ["npx", "-y", "@modelcontextprotocol/server-github"]
  # - name: postgres
  #   url: http://localhost:3001

resolve:
  k: 5

limits:
  timeout_ms: 5000
  max_cost_per_task_usd: 0.05
"""
