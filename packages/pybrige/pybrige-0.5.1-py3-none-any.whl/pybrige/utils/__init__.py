from __future__ import annotations

print("DEBUG: A executar o __init__.py de UTILS")
from .dicts import safe_get
from .formatting import print_table
from .io import write_json, read_json, append_json_line, pretty_print_json
from .text import (
    slugify, camel_to_snake, snake_to_camel,
    normalize_whitespace, remove_html_tags,
    extract_emails, extract_urls,
    validate_bi, # <-- Adicione aqui

)

__all__ = [
    "safe_get",
    "print_table",
    "write_json", "read_json", "append_json_line", "pretty_print_json",
    "slugify", "camel_to_snake", "snake_to_camel",
    "normalize_whitespace", "remove_html_tags",
    "extract_emails", "extract_urls",
]
