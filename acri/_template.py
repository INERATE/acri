"""_template — the acri init scaffold. Split out of cli.py (word-cap): this
is static content, not CLI parsing/dispatch logic.
"""
from __future__ import annotations

# One reasonable example model per provider -- not the dispatch table
# (acri.providers.PROVIDERS), just what _wizard.py pre-fills so a first
# acri.yaml is runnable immediately. Every entry is the explicit
# "provider/model" form: README.md "Supported providers" has the full list.
DEFAULT_MODEL = {
    "gemini": "gemini/gemini-2.5-flash", "vertex": "vertex/gemini-2.5-flash",
    "openai": "openai/gpt-5.6-luna", "anthropic": "anthropic/claude-sonnet-5",
    "bedrock": "bedrock/anthropic.claude-sonnet-5",
    "cloudflare": "cloudflare/@cf/meta/llama-3.3-70b-instruct",
    "openrouter": "openrouter/meta-llama/llama-3.3-70b-instruct",
    "nvidia": "nvidia/meta/llama-3.3-70b-instruct", "grok": "grok/grok-4",
    "ollama": "ollama/qwen2.5-coder:32b", "vllm": "vllm/your-model", "lmstudio": "lmstudio/your-model",
}

TEMPLATE = """\
version: 1

models:
  # "provider/model" -- any provider, not just this example. Swap for
  # "anthropic/claude-sonnet-5", "ollama/qwen2.5-coder:32b", "bedrock/...",
  # or any of the others: README.md "Supported providers" has one line each.
  default: gemini/gemini-2.5-flash
  # cheap: a stateless, prefix-free tier only -- classification, extraction,
  # summarizing a tool result. See docs/architecture.md #4.4. Optional.
  # cheap: gemini/gemini-2.5-flash-lite

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
