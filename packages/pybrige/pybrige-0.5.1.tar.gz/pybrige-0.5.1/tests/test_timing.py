import logging
import re
import pytest
from pybrige import timer

# REMOVEMOS A FIXTURE DAQUI

def test_timer_logs_execution_time(caplog):
    # JÁ NÃO PRECISAMOS de chamar setup_logging() aqui.

    @timer()
    def dummy():
        return 123
    with caplog.at_level(logging.INFO):
        result = dummy()
    
    assert result == 123
    # A mensagem de log deve estar em caplog.text
    assert re.search(r"Função 'dummy' executou em \d+\.\d{4}s", caplog.text)


def test_timer_with_custom_template(caplog):
    @timer(template="[{func_name}] took {elapsed:.2f}s")
    def dummy():
        return "ok"

    with caplog.at_level(logging.INFO):
        dummy()

    assert "dummy" in caplog.text
    assert "took" in caplog.text


def test_timer_with_custom_level(caplog):
    @timer(level=logging.WARNING)
    def dummy():
        return 1

    # Usamos .at_level(logging.WARNING) para capturar este nível
    with caplog.at_level(logging.WARNING):
        dummy()
    
    assert "WARNING" in caplog.records[0].levelname
    assert "dummy" in caplog.text


def test_timer_logs_even_on_exception(caplog):
    @timer()
    def faulty():
        raise ValueError("erro simulado")

    with pytest.raises(ValueError):
        with caplog.at_level(logging.INFO):
            faulty()

    # Mesmo com exceção, o log deve estar presente
    assert "faulty" in caplog.text
    assert "executou em" in caplog.text
