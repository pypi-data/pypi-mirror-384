import os
import pytest
from pybrige.core import config


def test_load_config_file_not_found(tmp_path, monkeypatch):
    """Config deve lançar FileNotFoundError se o arquivo não existir e safe=False."""
    fake = tmp_path / "notfound.json"
    with pytest.raises(FileNotFoundError):
        config.load_config(str(fake), safe=False)


def test_load_config_safe_returns_empty_dict(tmp_path):
    """Com safe=True e arquivo ausente, deve retornar {}."""
    fake = tmp_path / "notfound.json"
    result = config.load_config(str(fake), safe=True)
    assert result == {}


def test_env_var_loading(monkeypatch):
    """Testa carregamento de env vars obrigatórias."""
    monkeypatch.setenv("APP_MODE", "dev")
    monkeypatch.setenv("APP_SECRET", "xyz")

    required = ["APP_MODE", "APP_SECRET"]
    values = config.load_env_vars(required)
    assert values["APP_MODE"] == "dev"
    assert values["APP_SECRET"] == "xyz"


def test_missing_env_vars(monkeypatch):
    """Se env var estiver faltando, deve lançar erro."""
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.delenv("APP_SECRET", raising=False)

    with pytest.raises(config.MissingEnvVarsError):
        config.load_env_vars(["APP_MODE", "APP_SECRET"])


def test_merge_config_precedence(tmp_path):
    """Testa se merge de configs dá precedência ao override."""
    base = {"a": 1, "b": {"x": 10}}
    override = {"b": {"y": 20}, "c": 3}
    merged = config.merge_config(base, override)
    assert merged["a"] == 1
    assert merged["b"]["x"] == 10
    assert merged["b"]["y"] == 20
    assert merged["c"] == 3
