from __future__ import annotations
import os
import logging
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence, TypeVar, Literal, Optional, Dict, List


# ----------------------------
# Extras compatíveis
# ----------------------------
def load_config(path: str, safe: bool = False, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Lê configuração de um arquivo JSON.
    Se safe=True retorna {} ou `default` em caso de erro.
    """
    p = Path(path)
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        if safe:
            return default or {}
        raise


def load_env_vars(required: List[str]) -> Dict[str, str]:
    """
    Versão simplificada: garante apenas que todas as variáveis listadas existem.
    Retorna dict {var: valor}.
    """
    vals: Dict[str, str] = {}
    missing: List[str] = []
    for key in required:
        v = os.getenv(key)
        if v is None or v.strip() == "":
            missing.append(key)
        else:
            vals[key] = v
    if missing:
        raise MissingEnvVarsError(missing=missing)
    return vals


def merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Faz merge recursivo de configs, dando precedência ao override.
    """
    result = base.copy()
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = merge_config(result[k], v)  # recursão
        else:
            result[k] = v
    return result


# ----------------------------
# Exceptions
# ----------------------------
@dataclass
class MissingEnvVarsError(Exception):
    missing: List[str] = field(default_factory=list)
    invalid: List[str] = field(default_factory=list)
    details: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        parts: List[str] = []
        if self.missing:
            parts.append(f"Missing: {sorted(self.missing)}")
        if self.invalid:
            parts.append(f"Invalid: {sorted(self.invalid)}")
        if self.details:
            hints = "; ".join(f"{k}: {v}" for k, v in self.details.items())
            parts.append(f"Hints: {hints}")
        return " | ".join(parts) or "Environment validation failed"


# ----------------------------
# Types & helpers
# ----------------------------
ParseFn = Callable[[str], Any]
ValidatorFn = Callable[[Any], None]
T = TypeVar("T")

def _parse_bool(s: str) -> bool:
    truthy = {"1", "true", "yes", "y", "on"}
    falsy = {"0", "false", "no", "n", "off"}
    v = s.strip().lower()
    if v in truthy:
        return True
    if v in falsy:
        return False
    raise ValueError("expected boolean (true/false, 1/0, yes/no, on/off)")


def _parse_list(sep: str = ",") -> ParseFn:
    def _inner(s: str) -> List[str]:
        return [p.strip() for p in s.split(sep) if p.strip() != ""]
    return _inner


# Mapping de parsers padrão
DEFAULT_CASTERS: Mapping[str, ParseFn] = {
    "str": lambda s: s,
    "int": lambda s: int(s.strip()),
    "float": lambda s: float(s.strip()),
    "bool": _parse_bool,
    "list": _parse_list(","),  # string -> lista por vírgula
}


@dataclass(frozen=True)
class VarSpec:
    name: str
    type: Literal["str", "int", "float", "bool", "list"] = "str"
    required: bool = True
    default: Any = None
    parser: Optional[ParseFn] = None
    validator: Optional[ValidatorFn] = None
    help: str = ""  # dica para mensagem de erro
    sep: str = ","  # separador para listas


@dataclass
class EnvSpec:
    vars: Sequence[VarSpec]
    prefix: str = ""                # ex.: "APP_"
    use_dotenv: bool = True         # tenta load_dotenv() se disponível
    logger: Optional[logging.Logger] = None

    def _get_logger(self) -> logging.Logger:
        return self.logger or logging.getLogger(__name__)


# ----------------------------
# Core API
# ----------------------------
def load_env(spec: EnvSpec) -> Dict[str, Any]:
    """
    Valida e carrega variáveis de ambiente conforme o schema (EnvSpec).
    Retorna um dict com valores já convertidos (tipados).
    Lança MissingEnvVarsError se algo obrigatório faltar ou for inválido.
    """
    log = spec._get_logger()

    if spec.use_dotenv:
        try:
            from dotenv import load_dotenv  # import local
            load_dotenv()
            log.debug("Loaded .env (python-dotenv)")
        except Exception as e:
            log.debug(f"Skipping dotenv load: {e}")

    missing: List[str] = []
    invalid: List[str] = []
    hints: Dict[str, str] = {}
    result: Dict[str, Any] = {}

    for vs in spec.vars:
        env_name = f"{spec.prefix}{vs.name}" if spec.prefix else vs.name
        raw = os.getenv(env_name)

        if raw is None or raw.strip() == "":
            if vs.required and vs.default is None:
                missing.append(env_name)
                if vs.help:
                    hints[env_name] = vs.help
                continue
            value = vs.default
            result[vs.name] = value
            log.debug(f"{env_name} missing → using default={value!r}")
            continue

        try:
            if vs.parser is not None:
                value = vs.parser(raw)
            else:
                if vs.type == "list":
                    value = _parse_list(vs.sep)(raw)
                else:
                    caster = DEFAULT_CASTERS[vs.type]
                    value = caster(raw)
        except Exception as e:
            invalid.append(env_name)
            hints[env_name] = f"Failed to parse as {vs.type}: {e}"
            continue

        try:
            if vs.validator is not None:
                vs.validator(value)
        except Exception as e:
            invalid.append(env_name)
            hints[env_name] = f"Validation failed: {e}"
            continue

        result[vs.name] = value
        log.debug(f"{env_name} ok → {value!r}")

    if missing or invalid:
        raise MissingEnvVarsError(missing=missing, invalid=invalid, details=hints)

    return result


# ----------------------------
# API compatível com versões anteriores
# ----------------------------
def require_vars(vars: Iterable[str]) -> None:
    missing = []
    for var in vars:
        v = os.getenv(var)
        if v is None or v.strip() == "":
            missing.append(var)
    if missing:
        raise MissingEnvVarsError(missing=missing)


__all__ = [
    "EnvSpec",
    "VarSpec",
    "load_env",
    "require_vars",
    "MissingEnvVarsError",
    "load_config",
    "load_env_vars",
    "merge_config",
]
