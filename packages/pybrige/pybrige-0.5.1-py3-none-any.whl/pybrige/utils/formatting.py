from __future__ import annotations

# src/pybrige/utils/formatting.py
"""
formatting.py — utilities de formatação com estética "Mr. Robot / hacker".
Sem dependências externas. Saídas pensadas para terminais (ANSI capable).
"""

import json
import shutil
import textwrap
import random
import time
from typing import Any, Iterable, List, Dict, Union, Optional

# -----------------------
# Terminal utilities
# -----------------------
def _terminal_width(default: int = 80) -> int:
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return default

def _ansi(code: str) -> str:
    return f"\033[{code}m"

RESET = _ansi("0")
BOLD = _ansi("1")
DIM = _ansi("2")
INVERT = _ansi("7")
FG_GREEN = _ansi("32")
FG_CYAN = _ansi("36")
FG_WHITE = _ansi("37")
FG_MAG = _ansi("35")
FG_RED = _ansi("31")

# -----------------------
# Core table (clean)
# -----------------------
def print_table(
    data: Union[List[Dict[str, Any]], List[List[Any]]],
    headers: Optional[List[str]] = None,
    max_width: Optional[int] = None,
    align: str = "left",
    border: bool = True,
    sep: str = " | ",
) -> str:
    if not data:
        return "<tabela vazia>"

    if isinstance(data[0], dict):
        if not headers:
            headers = list(data[0].keys())
        rows = [[str(item.get(h, "")) for h in headers] for item in data]
    else:
        rows = [[str(x) for x in row] for row in data]
        if not headers:
            headers = [f"col{i+1}" for i in range(len(rows[0]))]

    rows = [headers] + rows
    col_widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    max_width = max_width or _terminal_width()
    def format_row(row: List[str]) -> str:
        formatted = []
        for i, cell in enumerate(row):
            if align == "right":
                cell = cell.rjust(col_widths[i])
            elif align == "center":
                cell = cell.center(col_widths[i])
            else:
                cell = cell.ljust(col_widths[i])
            formatted.append(cell)
        return sep.join(formatted)
    lines = [format_row(row) for row in rows]
    if border:
        border_line = "-" * min(max_width, sum(col_widths) + len(sep) * (len(col_widths) - 1))
        lines.insert(1, border_line)
    return "\n".join(lines)


# -----------------------
# Hacker-style table
# -----------------------
def print_table_hacker(
    data: Union[List[Dict[str, Any]], List[List[Any]]],
    headers: Optional[List[str]] = None,
    max_width: Optional[int] = None,
    align: str = "left",
) -> str:
    """
    Tabela com estética 'terminal hacker':
    - cores em verde/ciano
    - separadores estilo block
    - header invertido
    """
    raw = print_table(data, headers=headers, max_width=max_width, align=align, border=False, sep=" ░ ")
    # colorize header (first line) and use dim for rows
    lines = raw.splitlines()
    if not lines:
        return raw
    header = lines[0]
    rest = lines[1:]
    header = f"{INVERT}{FG_CYAN}{header}{RESET}"
    rest_colored = "\n".join(f"{DIM}{FG_GREEN}{ln}{RESET}" for ln in rest)
    return header + ("\n" + rest_colored if rest else "")


# -----------------------
# Markdown table
# -----------------------
def to_markdown_table(data: List[Dict[str, Any]]) -> str:
    if not data:
        return ""
    headers = list(data[0].keys())
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    rows = ["| " + " | ".join(str(item.get(h, "")) for h in headers) + " |" for item in data]
    return "\n".join([header_line, separator_line] + rows)


# -----------------------
# Pretty JSON
# -----------------------
def pretty_json(data: Any, indent: int = 2) -> str:
    return json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)


# -----------------------
# ASCII banner (hacker)
# -----------------------
def ascii_banner_hacker(title: str, subtitle: Optional[str] = None, width: Optional[int] = None) -> str:
    """
    Banner ASCII com borda e estilo 'hacker' (monospace).
    """
    width = width or min(_terminal_width(), max(40, len(title) + 10))
    top = f"{FG_MAG}{'=' * width}{RESET}"
    middle = f"{FG_WHITE}{BOLD}{title.center(width)}{RESET}"
    sub = f"{FG_CYAN}{subtitle.center(width)}{RESET}" if subtitle else ""
    bottom = f"{FG_MAG}{'=' * width}{RESET}"
    return "\n".join([top, middle, sub, bottom]) if subtitle else "\n".join([top, middle, bottom])


# -----------------------
# Boxed text (hacker)
# -----------------------
def boxed_text_hacker(text: str, width: Optional[int] = None, padding: int = 1) -> str:
    width = width or min(_terminal_width(), 80)
    inner_width = width - 4
    wrapped = textwrap.wrap(text, width=inner_width)
    line_top = f"{FG_CYAN}+{'─' * (inner_width)}+{RESET}"
    content = "\n".join(f"{FG_CYAN}| {RESET}{FG_WHITE}{line.ljust(inner_width)}{RESET}{FG_CYAN} |{RESET}" for line in wrapped)
    line_bot = f"{FG_CYAN}+{'─' * (inner_width)}+{RESET}"
    return "\n".join([line_top, content, line_bot])


# -----------------------
# Glitch text
# -----------------------
def glitch_text(text: str, intensity: float = 0.08, seed: Optional[int] = None) -> str:
    """
    Produz uma versão 'glitch' do texto trocando alguns caracteres por símbolos aleatórios.
    intensity: fração de caracteres corrompidos [0..1].
    """
    if seed is not None:
        random.seed(seed)
    symbols = list("░▒▓█▌▐▀▄▲▼●◼◻◽@#%?*")
    out = []
    for ch in text:
        if ch.isspace() or random.random() > intensity:
            out.append(ch)
        else:
            out.append(random.choice(symbols))
    return f"{FG_RED}{''.join(out)}{RESET}"


# -----------------------
# Matrix rain preview (small)
# -----------------------
def matrix_rain_preview(lines: int = 6, width: Optional[int] = None, seed: Optional[int] = None) -> str:
    width = width or min(_terminal_width(), 80)
    if seed is not None:
        random.seed(seed)
    chars = "01{}[]<>/\\|@#%$&*"  # mix binary + symbols
    out_lines = []
    for _ in range(lines):
        row = "".join(random.choice(chars) for _ in range(width))
        out_lines.append(f"{FG_GREEN}{row}{RESET}")
    return "\n".join(out_lines)


# -----------------------
# Progress bar (hacker)
# -----------------------
def progress_bar(
    current: int,
    total: int,
    length: int = 40,
    fill: str = "█",
    empty: str = "-",
    color: str = "green",
) -> str:
    ratio = min(max(current / total if total else 0, 0), 1)
    filled = int(ratio * length)
    bar = fill * filled + empty * (length - filled)
    col = FG_GREEN if color == "green" else FG_CYAN
    return f"{col}[{bar}]{RESET} {BOLD}{current}/{total}{RESET} ({ratio*100:.1f}%)"
