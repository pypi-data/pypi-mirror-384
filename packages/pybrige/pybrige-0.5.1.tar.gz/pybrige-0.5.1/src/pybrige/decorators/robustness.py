from __future__ import annotations

import time
import logging
import functools
from typing import Callable, Any, TypeVar, Tuple, Type

F = TypeVar("F", bound=Callable[..., Any])
def retry(
    tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    sleep_func: Callable[[float], None] = time.sleep,
    log_success: bool = False,
    logger: logging.Logger = logging.getLogger(),
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            remaining, current_delay = tries, delay

            while remaining > 0:
                try:
                    result = func(*args, **kwargs)
                    if log_success:
                        attempts_done = tries - remaining + 1
                        if attempts_done > 1:
                            logger.info(
                                f"Função '{func.__name__}' executada com sucesso após retries."
                            )
                        else:
                            logger.info(
                                f"Função '{func.__name__}' executada com sucesso."
                            )
                    return result
                except exceptions as e:
                    remaining -= 1
                    if remaining == 0:
                        logger.error(
                            f"Função '{func.__name__}' falhou após {tries} tentativas. "
                            f"Último erro: {e}"
                        )
                        raise
                    logger.warning(
                        f"Função '{func.__name__}' falhou com o erro: {e}. "
                        f"Tentando novamente em {current_delay:.2f}s... "
                        f"({remaining} tentativas restantes)"
                    )
                    sleep_func(current_delay)
                    current_delay *= backoff
        return wrapper  # type: ignore
    return decorator
