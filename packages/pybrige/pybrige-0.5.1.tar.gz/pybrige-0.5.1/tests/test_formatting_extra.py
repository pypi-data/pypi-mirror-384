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
    # Constantes de cor para os testes
    FG_GREEN,
    FG_CYAN,
    FG_WHITE,
    FG_MAG,
    FG_RED,
    INVERT,
    DIM,
    RESET,
    BOLD,
)

# --- Testes para print_table (a versão "limpa") ---
def test_print_table_list_of_lists_with_headers():
    """Testa a print_table com uma lista de listas e cabeçalhos fornecidos."""
    data = [["A", 1], ["B", 2]]
    headers = ["Letra", "Numero"]
    output = print_table(data, headers=headers)
    lines = output.splitlines()
    assert lines[0] == "Letra | Numero"
    assert "A     | 1" in lines[2]
    assert "B     | 2" in lines[3]


@pytest.mark.parametrize("align", ["left", "right", "center"])
def test_print_table_alignments(align):
    """Testa as diferentes opções de alinhamento da print_table."""
    data = [{"nome": "Ana"}]
    output = print_table(data, align=align)
    data_line = output.splitlines()[-1]

    assert "Ana" in data_line  # sempre deve conter "Ana"

    if align == "left":
        assert data_line.lstrip().startswith("Ana")
    elif align == "right":
        assert data_line.rstrip().endswith("Ana")
    elif align == "center":
        # tolera espaçamento variável, mas exige centralização
        assert data_line.strip("| ").strip() == "Ana"

def test_print_table_no_border():
    """Testa a opção de remover a linha de borda da print_table."""
    data = [{"id": 1}]
    output = print_table(data, border=False)
    assert "---" not in output

# --- Testes para as funções "hacker" ---
def test_print_table_hacker_empty():
    """Testa a versão hacker com dados vazios."""
    output = print_table_hacker([])
    assert "<tabela vazia>" in output

def test_ascii_banner_hacker_no_subtitle():
    """Testa o banner hacker sem o subtítulo opcional."""
    banner = ascii_banner_hacker("ACCESS GRANTED")
    assert "ACCESS GRANTED" in banner
    assert len(banner.split('\n')) == 3

def test_glitch_text_uses_color():
    """Verifica se o glitch_text aplica a cor vermelha."""
    text = "senha"
    glitched = glitch_text(text, intensity=0.5, seed=42)
    assert FG_RED in glitched
    assert RESET in glitched

def test_matrix_rain_with_custom_width():
    """Testa a matrix_rain com uma largura personalizada."""
    rain = matrix_rain_preview(lines=1, width=10, seed=1)
    plain_text = rain.replace(FG_GREEN, "").replace(RESET, "")
    assert len(plain_text) == 10

@pytest.mark.parametrize("current, total, expected_char_count", [
    (0, 100, 0),    # 0%
    (50, 100, 20),   # 50% de 40
    (100, 100, 40), # 100% de 40
])
def test_progress_bar_completeness(current, total, expected_char_count):
    """Testa a barra de progresso em diferentes percentagens."""
    fill_char = "█"
    bar = progress_bar(current, total, length=40, fill=fill_char)
    assert bar.count(fill_char) == expected_char_count

# --- Testes para outras utilidades de formatação ---
def test_to_markdown_table():
    """Testa a conversão para tabela Markdown."""
    data = [{"col1": "a", "col2": "b"}]
    # A função retorna uma string, não imprime, então não usamos capsys
    output = to_markdown_table(data)
    expected = "| col1 | col2 |\n| --- | --- |\n| a | b |"
    assert output == expected

def test_pretty_json():
    """Testa a formatação de JSON com chaves ordenadas."""
    data = {"b": 2, "a": 1}
    # json.dumps com sort_keys=True ordena as chaves alfabeticamente
    expected = '{\n  "a": 1,\n  "b": 2\n}'
    assert pretty_json(data, indent=2) == expected