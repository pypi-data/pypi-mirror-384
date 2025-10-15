from __future__ import annotations

import time
import functools
import logging
from typing import Callable, Any, TypeVar
from datetime import datetime

F = TypeVar("F", bound=Callable[..., Any])

def timer(
    level: int = logging.INFO,
    template: str = "[{timestamp}] Função '{func_name}' executou em {elapsed:.4f}s",
    logger: logging.Logger = logging.getLogger()
) -> Callable[[F], F]:
    """
    Um decorator configurável que mede e loga o tempo de execução de uma função,
    incluindo um timestamp da execução.

    Args:
        level (int, optional): Nível de logging a ser usado. Default = logging.INFO.
        template (str, optional): Formato da mensagem. Variáveis disponíveis:
                                  {timestamp}, {func_name}, {elapsed}.
        logger (logging.Logger, optional): Instância do logger a ser usada.
                                           Default = logger raiz.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_timestamp = datetime.now()
            start_time = time.perf_counter()

            try:
                return func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time

                timestamp_str = start_timestamp.strftime("%Y-%m-%d %H:%M:%S")

                log_message = template.format(
                    timestamp=timestamp_str,
                    func_name=func.__name__,
                    elapsed=elapsed_time
                )

                logger.log(level, log_message)

        return wrapper  # type: ignore
    return decorator
