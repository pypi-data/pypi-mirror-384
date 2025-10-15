import pytest
import logging
from pybrige import retry

# --- Teste para 'exceptions' ---
def test_retry_only_for_specific_exceptions(mocker):
    """Verifica se o retry só é acionado para as exceções listadas."""
    mock_func = mocker.Mock(side_effect=[IOError("Falha de I/O"), "sucesso"])

    # Decora para tentar novamente APENAS em caso de IOError
    @retry(tries=3, delay=0, exceptions=(IOError,))
    def decorated_func():
        return mock_func()

    result = decorated_func()
    assert result == "sucesso"
    assert mock_func.call_count == 2 # Deve tentar 2 vezes

    # Agora, testa com uma exceção NÃO listada
    mock_func_2 = mocker.Mock(side_effect=TypeError("Erro de tipo"))
    
    @retry(tries=3, delay=0, exceptions=(IOError,))
    def decorated_func_2():
        return mock_func_2()

    with pytest.raises(TypeError):
        decorated_func_2()
    
    mock_func_2.assert_called_once() # Deve falhar na primeira tentativa

# --- Teste para 'sleep_func' ---
def test_retry_uses_custom_sleep_function(mocker):
    """Verifica se a função de sleep personalizada é chamada."""
    mock_sleep = mocker.Mock()
    mock_func = mocker.Mock(side_effect=[Exception("falha"), "sucesso"])

    @retry(tries=2, delay=5, sleep_func=mock_sleep)
    def decorated_func():
        return mock_func()

    decorated_func()

    mock_sleep.assert_called_once_with(5) # Garante que sleep foi chamado com o delay correto

# --- Teste para 'log_success' ---
def test_retry_logs_success_message(caplog, mocker):
    """Verifica se a mensagem de sucesso é logada quando 'log_success=True'."""
    mock_func = mocker.Mock(side_effect=[Exception("falha"), "sucesso"])

    @retry(tries=2, delay=0, log_success=True)
    def decorated_func():
        return mock_func()
    
    with caplog.at_level(logging.INFO):
        decorated_func()

    assert "executada com sucesso após retries" in caplog.text

# --- Teste de falha final (continua válido) ---
def test_retry_fails_after_all_tries(mocker):
    """Verifica se a exceção é levantada após todas as tentativas."""
    mock_func = mocker.Mock(side_effect=ValueError("Erro persistente"))

    @retry(tries=3, delay=0)
    def decorated_func():
        return mock_func()

    with pytest.raises(ValueError):
        decorated_func()
    
    assert mock_func.call_count == 3
