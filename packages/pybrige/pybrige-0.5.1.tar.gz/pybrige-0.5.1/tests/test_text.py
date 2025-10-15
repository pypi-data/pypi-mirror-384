import pytest
from pybrige.utils.text import (
    slugify,
    camel_to_snake,
    snake_to_camel,
    normalize_whitespace,
    remove_html_tags,
    extract_emails,
    extract_urls,
    validate_bi, # A correção

)
from pybrige import validate_json




@pytest.mark.parametrize("inp, out", [
    ("Olá Mundo!", "ola-mundo"),
    ("Python_3.12 release", "python-3-12-release"),
    ("hello@world", "hello-world"),
])
def test_slugify_ascii(inp, out):
    assert slugify(inp, allow_unicode=False) == out

@pytest.mark.parametrize("inp, out", [
    ("Olá Mundo!", "olá-mundo"),
    ("日本語 テキスト", "日本語-テキスト"),
])
def test_slugify_unicode(inp, out):
    assert slugify(inp, allow_unicode=True) == out

@pytest.mark.parametrize("inp, out", [
    ("CamelCase", "camel_case"),
    ("MyVariableName", "my_variable_name"),
])
def test_camel_to_snake(inp, out):
    assert camel_to_snake(inp) == out

@pytest.mark.parametrize("inp, out", [
    ("snake_case", "SnakeCase"),
    ("user_id", "UserId"), # Sem preservar
])
def test_snake_to_camel_default(inp, out):
    assert snake_to_camel(inp, preserve_acronyms=False) == out

@pytest.mark.parametrize("inp, out", [
    ("api_response_id", "APIResponseID"),
    ("url_for_http_request", "URLForHTTPRequest"),
])
def test_snake_to_camel_with_acronyms(inp, out):
    assert snake_to_camel(inp, preserve_acronyms=True) == out

def test_normalize_whitespace():
    assert normalize_whitespace("  muitos \n\t espaços  ") == "muitos espaços"

def test_remove_html_tags():
    assert remove_html_tags('<p class="main">Texto <b>importante</b></p>') == "Texto importante"

def test_extract_emails():
    text = "Emails: user.name@domain.com e outro@server.co.uk."
    assert sorted(extract_emails(text)) == sorted(["user.name@domain.com", "outro@server.co.uk"])

@pytest.mark.parametrize("inp, out", [
    ("Visite http://site.com.", ["http://site.com"]),
    ("Veja em https://google.com, por favor.", ["https://google.com"]),
    ("O link é https://example.com/path!", ["https://example.com/path"]),
    ("Múltiplos http://a.com e http://b.com?", ["http://a.com", "http://b.com"]),
])
def test_extract_urls_handles_trailing_punctuation(inp, out):
    """Verifica se a pontuação final é removida das URLs."""
    assert sorted(extract_urls(inp)) == sorted(out)

@pytest.mark.parametrize("bi, expected", [
    # Casos Válidos
    ("123456789012A", True),
    (" 123456789012 B ", True), # Com espaços
    ("123456-789012-C", True), # Com hífens

    # Casos Inválidos
    ("123456789012", False),      # Curto demais
    ("123456789012AB", False),    # Longo demais
    ("ABCDEFGHIJKLM", False),     # Letras no lugar de números
    ("1234567890123", False),      # Número no lugar da letra
    ("", False),                  # Vazio
    (1234567890123, False),      # Não é string
])
def test_validate_bi(bi, expected):
    """Testa a validação de BI de Moçambique com vários formatos."""
    assert validate_bi(bi) == expected    