from __future__ import annotations


"""
pybrige - Um toolkit de produtividade para desenvolvedores em Python.
"""
from .core import (
    MissingEnvVarsError, VarSpec, EnvSpec,
    load_env, require_vars, setup_logging,
)

from .decorators import (
    retry, timer,
)
from .utils.io import (
    parse_csv, write_json, read_json,
    append_json_line, pretty_print_json,
    iter_json_lines, read_json_lines, tail_json_lines,
    count_file_lines, merge_json_files, validate_json,
)
# --- PASSO 2: Definir a versão oficial ---
# Atualizada para refletir a adição da função validate_bi
__version__ = "0.5.1"

__all__ = [
    "parse_csv",
    "extract_urls",
    "validate_bi", # <-- ADICIONE AQUI
    "write_json", "read_json", "append_json_line", "pretty_print_json",
    "iter_json_lines", "read_json_lines", "tail_json_lines",
    "count_file_lines", "merge_json_files", "validate_json",
]