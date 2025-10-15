from typing import List  # já deve estar no topo
import os
import pytest
from pybrige.core.config import (
    EnvSpec,
    VarSpec,
    load_env,
    require_vars,
    MissingEnvVarsError,
)

# -------------------------------------------------------------------
# Testes para require_vars (checagem simples de variáveis de ambiente)
# -------------------------------------------------------------------

def test_require_vars_all_present(monkeypatch):
    monkeypatch.setenv("API_KEY", "123")
    monkeypatch.setenv("DB_URL", "sqlite:///:memory:")
    require_vars(["API_KEY", "DB_URL"])  # não deve lançar erro


def test_require_vars_missing(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(MissingEnvVarsError) as excinfo:
        require_vars(["MISSING_VAR"])
    assert "MISSING_VAR" in excinfo.value.missing


# -------------------------------------------------------------------
# Testes para load_env (configuração avançada com EnvSpec/VarSpec)
# -------------------------------------------------------------------

def test_load_env_happy_path(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("ALLOWED_HOSTS", "a.com,b.com")

    spec = EnvSpec(
        vars=[
            VarSpec("DEBUG", type="bool"),
            VarSpec("PORT", type="int"),
            VarSpec("ALLOWED_HOSTS", type="list"),
        ]
    )
    config = load_env(spec)

    assert config["DEBUG"] is True
    assert config["PORT"] == 8080
    assert config["ALLOWED_HOSTS"] == ["a.com", "b.com"]


def test_load_env_missing_required(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    spec = EnvSpec([VarSpec("SECRET_KEY", type="str", required=True)])
    with pytest.raises(MissingEnvVarsError) as excinfo:
        load_env(spec)
    assert "SECRET_KEY" in excinfo.value.missing


def test_load_env_with_default(monkeypatch):
    monkeypatch.delenv("TIMEOUT", raising=False)
    spec = EnvSpec([VarSpec("TIMEOUT", type="int", required=False, default=30)])
    config = load_env(spec)
    assert config["TIMEOUT"] == 30


def test_load_env_invalid_type(monkeypatch):
    """Falha no casting de tipo gera MissingEnvVarsError com detalhes."""
    monkeypatch.setenv("PORT", "not-a-number")
    spec = EnvSpec([VarSpec("PORT", type="int")])
    with pytest.raises(MissingEnvVarsError) as excinfo:
        load_env(spec)
    assert "PORT" in excinfo.value.invalid
    assert "Failed to parse as int" in excinfo.value.details["PORT"]


def test_load_env_custom_parser(monkeypatch):
    monkeypatch.setenv("CSV_VALUES", "1;2;3")

    def parse_csv(value: str) -> List[int]:
        return [int(x) for x in value.split(";")]

    spec = EnvSpec([VarSpec("CSV_VALUES", parser=parse_csv)])
    config = load_env(spec)
    assert config["CSV_VALUES"] == [1, 2, 3]


def test_load_env_validator_failure(monkeypatch):
    monkeypatch.setenv("AGE", "15")

    def validate_age(x: int):
        if x < 18:
            raise ValueError("Too young!")

    spec = EnvSpec([VarSpec("AGE", type="int", validator=validate_age)])
    with pytest.raises(MissingEnvVarsError) as excinfo:
        load_env(spec)
    assert "AGE" in excinfo.value.invalid
    assert "Too young!" in excinfo.value.details["AGE"]


def test_load_env_prefix(monkeypatch):
    monkeypatch.setenv("APP_HOST", "localhost")
    spec = EnvSpec([VarSpec("HOST", type="str")], prefix="APP_")
    config = load_env(spec)
    assert config["HOST"] == "localhost"
