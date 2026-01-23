"""
utils/error_handling.py

Улучшенная обработка ошибок - Фаза 7.3.
"""

from typing import Optional, Callable, Any
from functools import wraps
import traceback

from .logging import get_logger


class SolverError(Exception):
    """Базовое исключение для решателей."""
    pass


class InvalidBoardError(SolverError):
    """Ошибка невалидной доски."""
    pass


class NoSolutionError(SolverError):
    """Ошибка отсутствия решения."""
    pass


class ValidationError(SolverError):
    """Ошибка валидации решения."""
    pass


class CacheError(SolverError):
    """Ошибка кэширования."""
    pass


def handle_errors(default_return: Any = None, log_error: bool = True):
    """
    Декоратор для обработки ошибок.
    
    Args:
        default_return: значение по умолчанию при ошибке
        log_error: логировать ли ошибку
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SolverError as e:
                if log_error:
                    logger = get_logger()
                    logger.error(f"{func.__name__}: {str(e)}")
                return default_return
            except Exception as e:
                if log_error:
                    logger = get_logger()
                    logger.error(
                        f"{func.__name__}: Неожиданная ошибка: {str(e)}",
                        exc_info=True
                    )
                return default_return
        return wrapper
    return decorator


def safe_solve(solver, board, default: Any = None):
    """
    Безопасное выполнение solve с обработкой ошибок.
    
    Args:
        solver: решатель
        board: доска
        default: значение по умолчанию при ошибке
        
    Returns:
        Решение или default
    """
    try:
        return solver.solve(board)
    except SolverError as e:
        logger = get_logger()
        logger.error(f"Ошибка решателя {solver.__class__.__name__}: {str(e)}")
        return default
    except Exception as e:
        logger = get_logger()
        logger.error(
            f"Неожиданная ошибка в {solver.__class__.__name__}: {str(e)}",
            exc_info=True
        )
        return default


def validate_board(board) -> bool:
    """
    Валидирует доску.
    
    Args:
        board: доска для валидации
        
    Returns:
        True если доска валидна
        
    Raises:
        InvalidBoardError: если доска невалидна
    """
    if board is None:
        raise InvalidBoardError("Доска не может быть None")
    
    if not hasattr(board, 'peg_count'):
        raise InvalidBoardError("Доска должна иметь метод peg_count()")
    
    peg_count = board.peg_count()
    if peg_count < 1:
        raise InvalidBoardError("Доска должна содержать хотя бы один колышек")
    
    if peg_count > 49:
        raise InvalidBoardError("Слишком много колышков (максимум 49)")
    
    return True
