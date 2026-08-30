import pytest

from acri.credentials import model_id_for, provider_for


def test_provider_for_infers_from_a_bare_model_name():
    assert provider_for("gemini-2.5-flash") == "gemini"
    assert provider_for("gpt-4o-mini") == "openai"


def test_provider_for_reads_an_explicit_prefix():
    assert provider_for("anthropic/claude-sonnet-5") == "anthropic"
    assert provider_for("ollama/qwen2.5-coder:32b") == "ollama"


def test_provider_for_splits_on_the_first_slash_only():
    # OpenRouter/NVIDIA model ids are themselves "vendor/model" -- the prefix
    # split must not eat into that.
    assert provider_for("openrouter/meta-llama/llama-3.3-70b-instruct") == "openrouter"


def test_model_id_for_strips_the_provider_prefix():
    assert model_id_for("anthropic/claude-sonnet-5") == "claude-sonnet-5"


def test_model_id_for_keeps_a_vendor_slash_intact():
    assert model_id_for("openrouter/meta-llama/llama-3.3-70b-instruct") == "meta-llama/llama-3.3-70b-instruct"


def test_model_id_for_is_a_no_op_on_a_bare_name():
    assert model_id_for("gemini-2.5-flash") == "gemini-2.5-flash"


def test_missing_env_vars_rejects_a_typo_d_provider(tmp_path):
    from acri.config import Config, ModelsConfig
    from acri.credentials import missing_env_vars

    config = Config(version=1, models=ModelsConfig(default="opennrouter/some-model"))
    with pytest.raises(ValueError, match="unknown provider"):
        missing_env_vars(config)


def test_missing_env_vars_treats_a_local_provider_as_needing_no_key(monkeypatch):
    from acri.config import Config, ModelsConfig
    from acri.credentials import missing_env_vars

    config = Config(version=1, models=ModelsConfig(default="ollama/qwen2.5-coder:32b"))
    assert missing_env_vars(config) == []
