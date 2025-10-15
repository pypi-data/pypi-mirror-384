# --- src/pybrige/core/logging.py ---
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

class ColoredFormatter(logging.Formatter):
    """
    Formatter que adiciona cores ao console com base no nível do log.
    """
    GREY = "\x1b[38;20m"
    BLUE = "\x1b[34;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    FORMAT = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
    LOG_COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: BLUE,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def __init__(self, fmt: str | None = None, datefmt: str | None = None, style: str = '%', validate: bool = True):
        super().__init__(fmt if fmt else self.FORMAT, datefmt, style, validate)

    def format(self, record):
        log_color = self.LOG_COLORS.get(record.levelno, self.GREY)
        formatted_message = super().format(record)
        return f"{log_color}{formatted_message}{self.RESET}"


def supports_color() -> bool:
    """
    Verifica se o terminal suporta cores ANSI.
    """
    return sys.stderr.isatty() and os.name != "nt"


def setup_logging(
    level: int = logging.INFO,
    colors: bool = True,
    file: str | None = None,
    logger_name: str | None = None,
    force_overwrite: bool = True,
    stream: bool | None = None,
    datefmt: str = "%H:%M:%S",
    fmt: str | None = None,
    max_bytes: int = 5_000_000,  # 5 MB
    backup_count: int = 3,
) -> logging.Logger:
    """
    Configura o sistema de logging do Python.

    Args:
        level (int): Nível de logging (ex: logging.INFO, logging.DEBUG)
        colors (bool): Se deve usar cores no console.
        file (str | None): Caminho para ficheiro de log (opcional).
        logger_name (str | None): Nome do logger (None = root logger).
        force_overwrite (bool): Remove handlers existentes antes de configurar.
        stream (bool | None): Controla o StreamHandler (True/False/None).
        datefmt (str): Formato da data/hora.
        fmt (str | None): Formato customizado da mensagem.
        max_bytes (int): Tamanho máximo do ficheiro antes de rodar.
        backup_count (int): Quantos ficheiros antigos manter.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Determinar se deve usar cores
    if colors and not supports_color():
        colors = False

    # Remover handlers antigos se necessário
    if force_overwrite:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    # Formatter base
    format_str = fmt or "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
    stream_formatter = (
        ColoredFormatter(format_str, datefmt)
        if colors else logging.Formatter(format_str, datefmt)
    )
    file_formatter = logging.Formatter(format_str, datefmt)

    # Adicionar StreamHandler
    add_stream_handler = (stream is True) or (stream is None and not file)
    if add_stream_handler and not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(level)
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)

    # Adicionar FileHandler ou RotatingFileHandler
    if file:
        os.makedirs(os.path.dirname(file), exist_ok=True)
        file_handler = RotatingFileHandler(
            file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Configurar propagação
    if logger_name and not logger.handlers:
        logger.propagate = True
    elif not logger_name:
        logger.propagate = False

    # Log inicial
    logger.debug(f"Logger '{logger_name or 'root'}' configurado com nível: {logging.getLevelName(level)}")
    return logger
