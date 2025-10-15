import pytest
from pybrige.utils.formatting import (
    print_table,
    print_table_hacker,
    to_markdown_table,
    pretty_json,
    ascii_banner_hacker,
    boxed_text_hacker,
    glitch_text,
    matrix_rain_preview,
    progress_bar,
    FG_GREEN,
    FG_CYAN,
    FG_WHITE,
    FG_MAG,
    FG_RED,
    INVERT,
    DIM,
    RESET,
)

# ------------------------
# print_table & print_table_hacker
# ------------------------
def test_print_table_basic():
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    table = print_table(data)
    assert "Alice" in table and "Bob" in table
    assert "-" in table  # border line presente

def test_print_table_no_border():
    data = [[1, "Alice"], [2, "Bob"]]
    table = print_table(data, border=False, headers=["id", "name"])
    assert "Alice" in table
    assert "-" not in table  # sem borda

def test_print_table_hacker_styles():
    data = [{"id": 1, "status": "ONLINE"}]
    styled = print_table_hacker(data)
    assert INVERT in styled and FG_CYAN in styled
    assert DIM in styled and FG_GREEN in styled
    assert "ONLINE" in styled

# ------------------------
# to_markdown_table
# ------------------------
def test_to_markdown_table_normal():
    data = [{"id": 1, "name": "Alice"}]
    md = to_markdown_table(data)
    assert "| id | name |" in md
    assert "---" in md
    assert "| 1 | Alice |" in md

def test_to_markdown_table_empty():
    assert to_markdown_table([]) == ""

# ------------------------
# pretty_json
# ------------------------
def test_pretty_json_sorted_keys():
    obj = {"z": 1, "a": 2}
    result = pretty_json(obj)
    assert result.strip().startswith("{")
    assert '"a"' in result and '"z"' in result
    # checa se está indentado
    assert "\n  " in result

# ------------------------
# ascii_banner_hacker
# ------------------------
def test_ascii_banner_hacker_with_and_without_subtitle():
    banner1 = ascii_banner_hacker("F SOCIETY", subtitle="we are everyone")
    assert "F SOCIETY" in banner1
    assert "we are everyone" in banner1
    assert FG_MAG in banner1 and FG_WHITE in banner1 and FG_CYAN in banner1

    banner2 = ascii_banner_hacker("NO SUB")
    assert "NO SUB" in banner2
    assert "===" in banner2
    assert "we are everyone" not in banner2

# ------------------------
# boxed_text_hacker
# ------------------------
def test_boxed_text_hacker_wrapping():
    text = "Este é um texto muito longo que deve quebrar em mais de uma linha"
    box = boxed_text_hacker(text, width=30)
    assert "Este é um texto" in box
    assert "linha" in box
    assert "─" in box
    assert FG_CYAN in box and FG_WHITE in box

# ------------------------
# glitch_text
# ------------------------
def test_glitch_text_with_and_without_intensity():
    txt = "password"
    g0 = glitch_text(txt, intensity=0, seed=123)
    assert g0.endswith(RESET)  # mantém cores mesmo sem glitch
    assert "password" in g0  # sem alteração

    g1 = glitch_text(txt, intensity=0.5, seed=123)
    g2 = glitch_text(txt, intensity=0.5, seed=123)
    assert g1 == g2  # determinístico com seed
    assert g1 != g0  # com alteração
    assert FG_RED in g1

# ------------------------
# matrix_rain_preview
# ------------------------
def test_matrix_rain_preview_with_and_without_seed():
    r1 = matrix_rain_preview(lines=3, width=10, seed=42)
    r2 = matrix_rain_preview(lines=3, width=10, seed=42)
    assert r1 == r2  # determinístico com seed
    assert len(r1.split("\n")) == 3
    assert FG_GREEN in r1

    # sem seed, ainda deve ter o número certo de linhas
    r3 = matrix_rain_preview(lines=2, width=5)
    assert len(r3.split("\n")) == 2

# ------------------------
# progress_bar
# ------------------------
def test_progress_bar_cases():
    # barra vazia
    bar0 = progress_bar(0, 100, length=10)
    assert "[----------]" in bar0
    assert "0/100" in bar0

    # barra cheia
    bar_full = progress_bar(100, 100, length=10)
    assert "[██████████]" in bar_full
    assert "100/100" in bar_full

    # sem total (evita ZeroDivisionError)
    bar_zero_total = progress_bar(5, 0, length=10)
    assert "5/0" in bar_zero_total
    assert "%" in bar_zero_total

    # cor customizada
    bar_cyan = progress_bar(50, 100, color="cyan")
    assert FG_CYAN in bar_cyan
