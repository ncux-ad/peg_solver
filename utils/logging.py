"""
utils/logging.py

Централизованная система логирования - Фаза 7.4.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class SolverLogger:
    """Логгер для решателей."""
    
    def __init__(self, name: str = "peg_solver", level: int = logging.INFO):
        """
        Инициализирует логгер.
        
        Args:
            name: имя логгера
            level: уровень логирования
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Избегаем дублирования handlers
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            # Форматтер
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Логирует отладочное сообщение."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Логирует информационное сообщение."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Логирует предупреждение."""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Логирует ошибку."""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """Логирует критическую ошибку."""
        self.logger.critical(message, exc_info=exc_info)


# Глобальный логгер
_default_logger: Optional[SolverLogger] = None


def get_logger(name: str = "peg_solver", level: int = logging.INFO) -> SolverLogger:
    """
    Возвращает глобальный логгер или создаёт новый.
    
    Args:
        name: имя логгера
        level: уровень логирования
        
    Returns:
        SolverLogger
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = SolverLogger(name, level)
    return _default_logger


def setup_file_logging(log_file: str = "peg_solver.log", level: int = logging.INFO):
    """
    Настраивает логирование в файл.
    
    Args:
        log_file: путь к файлу лога
        level: уровень логирования
    """
    logger = get_logger()
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.logger.addHandler(file_handler)
