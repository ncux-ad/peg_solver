"""
peg_io - Ввод/вывод для Peg Solitaire

Экспортирует:
- Парсинг входных данных
- Визуализация доски
- Кэширование решений
"""

from .parser import parse_input, create_english_board
from .visualizer import display_board, format_solution
from .cache import load_solutions, save_solution, get_cached_solution

__all__ = [
    'parse_input',
    'create_english_board',
    'display_board',
    'format_solution',
    'load_solutions',
    'save_solution',
    'get_cached_solution'
]
