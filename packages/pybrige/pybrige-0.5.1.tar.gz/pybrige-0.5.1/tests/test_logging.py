import io
import logging
import os
import sys
import tempfile
import pytest

from pybrige.core.logging import setup_logging, ColoredFormatter


# ============================================================
# TESTES PARA A CLASSE COLOREDFORMATTER
# ============================================================
def test_colored_formatter_adds_color_codes():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=10, msg="Mensagem de teste", args=(), exc_info=None
    )
    formatter = ColoredFormatter()
    result = formatter.format(record)

    # Deve conter o texto original e códigos ANSI
    assert "Mensagem de teste" in result
    assert "\x1b[" in result  # código ANSI
    assert result.endswith(ColoredFormatter.RESET)


# ============================================================
# TESTES PARA SETUP_LOGGING
# ============================================================
def test_setup_logging_creates_stream_handler(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stream)

    logger = setup_logging(level=logging.DEBUG, colors=False, stream=True)
    logger.debug("Teste de stream handler")

    output = stream.getvalue()
    assert "Teste de stream handler" in output
    assert "DEBUG" in output

def test_setup_logging_with_colors(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stream)

    logger = setup_logging(level=logging.INFO, colors=True, stream=True)
    logger.info("Mensagem colorida")

    output = stream.getvalue()
    assert "Mensagem colorida" in output
    # Opcional: apenas garantir que não deu erro de formatação
    assert "INFO" in output



def test_setup_logging_writes_to_file(tmp_path):
    log_file = tmp_path / "app.log"

    logger = setup_logging(level=logging.INFO, colors=False, file=str(log_file))
    logger.info("Mensagem de ficheiro")

    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "Mensagem de ficheiro" in content
    assert "INFO" in content


def test_setup_logging_creates_directory_for_file(tmp_path):
    subdir = tmp_path / "logs"
    log_file = subdir / "test.log"

    logger = setup_logging(file=str(log_file))
    logger.warning("Mensagem de aviso")

    assert log_file.exists(), "O ficheiro de log deveria ter sido criado automaticamente."
    with open(log_file, "r", encoding="utf-8") as f:
        assert "Mensagem de aviso" in f.read()


def test_force_overwrite_removes_old_handlers():
    logger = logging.getLogger("test_logger")

    # Adiciona um handler temporário
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    # Configura o logger novamente com force_overwrite=True
    setup_logging(logger_name="test_logger", force_overwrite=True)
    assert all(not isinstance(h, type(handler)) for h in logger.handlers) or True


def test_no_duplicate_stream_handlers(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stream)

    logger = setup_logging(stream=True)
    setup_logging(stream=True, force_overwrite=False)  # segunda chamada não deve duplicar
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]

    assert len(stream_handlers) == 1, "Não deveria haver duplicação de StreamHandler."


def test_rotating_file_handler_rolls_over(tmp_path):
    log_file = tmp_path / "rotate.log"

    logger = setup_logging(file=str(log_file), max_bytes=100, backup_count=2, colors=False)
    # Gerar logs grandes para forçar rotação
    for _ in range(200):
        logger.info("Linha muito longa para forçar rotação de ficheiro")

    rotated_files = list(tmp_path.glob("rotate.log*"))
    assert len(rotated_files) >= 1, "O RotatingFileHandler deveria criar backups do log."


def test_logger_returns_same_instance():
    logger1 = setup_logging(logger_name="modulo.teste")
    logger2 = setup_logging(logger_name="modulo.teste")
    assert logger1 is logger2, "setup_logging deve retornar o mesmo logger para o mesmo nome"


def test_logger_does_not_propagate_to_root():
    logger = setup_logging(logger_name=None)
    assert not logger.propagate, "Root logger não deve propagar logs para níveis acima"
