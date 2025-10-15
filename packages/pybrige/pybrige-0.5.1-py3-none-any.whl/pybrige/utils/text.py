from __future__ import annotations

import re
import unicodedata
from typing import List


def slugify(text: str, allow_unicode: bool = False) -> str:
    """
    Converte uma string para slug (url-friendly).
    - Normaliza acentos.
    - Substitui espaços, underscores e caracteres inválidos por hífen.
    - Remove hífens repetidos e bordas.
    """
    text = str(text)
    if allow_unicode:
        text = unicodedata.normalize("NFKC", text).lower()
        text = re.sub(r"[\s_]+", "-", text)
        text = re.sub(r"[^\w\-]+", "-", text)  # converte inválidos em hífen
    else:
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = text.lower()
        text = re.sub(r"[\s_]+", "-", text)
        text = re.sub(r"[^\w\-]+", "-", text)  # converte inválidos em hífen
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def camel_to_snake(text: str) -> str:
    """Converte CamelCase → snake_case."""
    text = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    return text.lower()


def snake_to_camel(text: str, preserve_acronyms: bool = False) -> str:
    """
    Converte snake_case → CamelCase.
    - preserve_acronyms=True mantém siglas conhecidas em maiúsculo.
    """
    words = text.split("_")
    if preserve_acronyms:
        acronyms = {"id", "api", "http", "url"}
        return "".join(
            w.upper() if w.lower() in acronyms else w.capitalize()
            for w in words
        )
    return "".join(w.capitalize() for w in words)


def normalize_whitespace(text: str) -> str:
    """Remove espaços extras e normaliza para um espaço simples."""
    return re.sub(r"\s+", " ", text).strip()


def remove_html_tags(text: str) -> str:
    """Remove tags HTML da string."""
    return re.sub(r"<[^>]+>", "", text)


def extract_emails(text: str) -> List[str]:
    """Extrai todos os emails válidos de um texto."""
    return re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)


def extract_urls(text: str) -> List[str]:
    """
    Extrai todas as URLs de um texto.
    Remove pontuações finais comuns (. , ! ?).
    """
    urls = re.findall(r"https?://[^\s<>\"']+", text)
    return [u.rstrip(".,!?") for u in urls]

def validate_bi(bi_number: str) -> bool:
    """
    Valida o formato de um número de Bilhete de Identidade de Moçambique.

    Verifica se a string:
    - Tem 13 caracteres (após limpar espaços/hífens).
    - Os primeiros 12 são dígitos.
    - O último caractere é uma letra.

    Args:
        bi_number: O número do BI como uma string.

    Returns:
        True se o formato for válido, False caso contrário.
    """
    if not isinstance(bi_number, str):
        return False

    # Limpa o input de caracteres comuns de formatação
    cleaned_bi = bi_number.replace("-", "").replace(" ", "").strip()

    # 1. Verifica o comprimento
    if len(cleaned_bi) != 13:
        return False

    # 2. Verifica as partes numéricas e a letra final
    number_part = cleaned_bi[:12]
    letter_part = cleaned_bi[12]

    if not number_part.isdigit() or not letter_part.isalpha():
        return False

    return True