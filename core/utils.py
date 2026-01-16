"""
core/utils.py

Общие утилиты и константы для Peg Solitaire.
"""

from typing import List, Tuple

# Направления движения: вверх, вниз, влево, вправо
DIRECTIONS: List[Tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Символы для отображения
PEG = '●'       # Колышек
HOLE = '○'      # Пустое место (можно прыгнуть)
EMPTY = '▫'     # Недоступная клетка


def board_to_str(board: List[List[str]]) -> str:
    """Преобразует доску в строку для хеширования."""
    return ''.join(''.join(row) for row in board)


def str_to_board(s: str, rows: int, cols: int) -> List[List[str]]:
    """Обратное преобразование строки в доску."""
    return [list(s[i*cols:(i+1)*cols]) for i in range(rows)]


def index_to_pos(row: int, col: int) -> str:
    """Индекс (row, col) → шахматная нотация (A1, B2, ...)."""
    return f"{chr(col + ord('A'))}{row + 1}"


def pos_to_index(pos: str) -> Tuple[int, int]:
    """Шахматная нотация → индекс."""
    col = ord(pos[0].upper()) - ord('A')
    row = int(pos[1:]) - 1
    return row, col


def count_pegs(board: List[List[str]]) -> int:
    """Подсчёт количества колышков на доске."""
    return sum(row.count(PEG) for row in board)


def is_valid_position(r: int, c: int, rows: int, cols: int) -> bool:
    """Проверяет, находится ли позиция в пределах доски."""
    return 0 <= r < rows and 0 <= c < cols
