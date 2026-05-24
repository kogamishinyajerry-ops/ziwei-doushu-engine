from pathlib import Path
import importlib
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_requests_is_declared_runtime_dependency():
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert any(
        line.strip().startswith("requests")
        for line in requirements.splitlines()
    )
    assert importlib.import_module("requests")


def test_auto_provider_uses_openai_key_with_openai_endpoint(monkeypatch):
    from ziwei.analysis.llm_prompt import _get_api_config

    for key in ("MINIMAX_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")

    key, url, model, provider = _get_api_config()

    assert key == "openai-test-key"
    assert url == "https://api.openai.com/v1"
    assert model == "gpt-4o"
    assert provider == "openai"


def test_auto_provider_priority_is_minimax_deepseek_openai(monkeypatch):
    from ziwei.analysis.llm_prompt import _get_api_config

    monkeypatch.setenv("MINIMAX_API_KEY", "minimax-test-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")

    key, _, _, provider = _get_api_config()

    assert key == "minimax-test-key"
    assert provider == "minimax"

    monkeypatch.delenv("MINIMAX_API_KEY")
    key, _, _, provider = _get_api_config()

    assert key == "deepseek-test-key"
    assert provider == "deepseek"

    monkeypatch.delenv("DEEPSEEK_API_KEY")
    key, _, _, provider = _get_api_config()

    assert key == "openai-test-key"
    assert provider == "openai"
