"""
patterns.py

Шаблоны (паттерны) для жадного решения Peg Solitaire.
Паттерны позволяют быстро делать "очевидные" ходы.
"""

from typing import Optional, Tuple, List, Callable
from copy import deepcopy

Move = Tuple[int, int, int, int]  # (row, col, dr, dc)
PatternMatcher = Callable[[List[List[str]]], Optional[Move]]


def match_line_of_three(board: List[List[str]]) -> Optional[Move]:
    """
    Находит три клетки подряд: ●●○ или ○●●
    Возвращает позицию и направление для хода.
    """
    rows, cols = len(board), len(board[0])

    # Горизонтальные
    for r in range(rows):
        for c in range(cols - 2):
            if board[r][c] == board[r][c+1] == '●' and board[r][c+2] == '○':
                return (r, c, 0, 1)
            if board[r][c] == '○' and board[r][c+1] == board[r][c+2] == '●':
                return (r, c+2, 0, -1)

    # Вертикальные
    for c in range(cols):
        for r in range(rows - 2):
            if board[r][c] == board[r+1][c] == '●' and board[r+2][c] == '○':
                return (r, c, 1, 0)
            if board[r][c] == '○' and board[r+1][c] == board[r+2][c] == '●':
                return (r+2, c, -1, 0)

    return None


def match_line_of_four(board: List[List[str]]) -> Optional[Move]:
    """
    Находит ●●●○ или ○●●● — можно сделать два хода подряд.
    """
    rows, cols = len(board), len(board[0])

    for r in range(rows):
        for c in range(cols - 3):
            if board[r][c] == board[r][c+1] == board[r][c+2] == '●' and board[r][c+3] == '○':
                return (r, c, 0, 1)
            if board[r][c] == '○' and board[r][c+1] == board[r][c+2] == board[r][c+3] == '●':
                return (r, c+3, 0, -1)

    for c in range(cols):
        for r in range(rows - 3):
            if board[r][c] == board[r+1][c] == board[r+2][c] == '●' and board[r+3][c] == '○':
                return (r, c, 1, 0)
            if board[r][c] == '○' and board[r+1][c] == board[r+2][c] == board[r+3][c] == '●':
                return (r+3, c, -1, 0)

    return None


def match_square_2x2(board: List[List[str]]) -> Optional[Move]:
    """
    Паттерн 2x2 с тремя колышками и одной пустотой.
    """
    rows, cols = len(board), len(board[0])

    for r in range(rows - 1):
        for c in range(cols - 1):
            block = [board[r][c], board[r][c+1], board[r+1][c], board[r+1][c+1]]
            if block.count('●') == 3 and block.count('○') == 1:
                if board[r][c] == '○' and board[r][c+1] == board[r+1][c] == '●':
                    return (r+1, c, -1, 0)
                if board[r+1][c+1] == '○' and board[r][c+1] == board[r+1][c] == '●':
                    return (r, c+1, 1, 0)
                if board[r][c+1] == '○' and board[r][c] == board[r+1][c+1] == '●':
                    return (r+1, c+1, -1, 0)
                if board[r+1][c] == '○' and board[r][c] == board[r+1][c+1] == '●':
                    return (r, c, 1, 0)

    return None


def match_edge_cleanup(board: List[List[str]]) -> Optional[Move]:
    """
    Находит возможность убрать колышек на краю.
    """
    rows, cols = len(board), len(board[0])

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == '●':
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    r1, c1 = r + dr, c + dc
                    r2, c2 = r + 2*dr, c + 2*dc
                    if 0 <= r2 < rows and 0 <= c2 < cols:
                        if 0 <= r1 < rows and 0 <= c1 < cols:
                            if board[r1][c1] == '●' and board[r2][c2] == '○':
                                return (r, c, dr, dc)

    return None


def match_l_shape(board: List[List[str]]) -> Optional[Move]:
    """
    L-образный паттерн: часто встречается в углах.
    """
    rows, cols = len(board), len(board[0])

    # Проверяем L-образные конфигурации
    for r in range(rows - 2):
        for c in range(cols - 2):
            # Несколько вариантов L
            if (board[r][c] == '●' and board[r+1][c] == '●' and
                board[r+2][c] == '●' and board[r+2][c+1] == '●'):
                if c + 2 < cols and board[r+2][c+2] == '○':
                    return (r+2, c, 0, 1)

    return None


def available_patterns() -> List[PatternMatcher]:
    """Возвращает список функций-паттернов в порядке приоритета."""
    return [
        match_line_of_four,   # Длинные линии сначала
        match_line_of_three,
        match_square_2x2,
        match_l_shape,
        match_edge_cleanup,   # Края в конце
    ]


def apply_move_matrix(board: List[List[str]], r: int, c: int, dr: int, dc: int) -> List[List[str]]:
    """Применяет ход на матричной доске."""
    new_board = deepcopy(board)
    r1, c1 = r + dr, c + dc
    r2, c2 = r + 2*dr, c + 2*dc
    new_board[r][c] = '○'
    new_board[r1][c1] = '○'
    new_board[r2][c2] = '●'
    return new_board


def index_to_pos(row: int, col: int) -> str:
    """Индекс → символьная позиция."""
    return f"{chr(col + ord('A'))}{row + 1}"


def apply_pattern_sequence(board: List[List[str]]) -> Optional[List[str]]:
    """
    Жадно применяет паттерны пока возможно.
    Возвращает список ходов если удалось решить, иначе None.
    """
    path = []
    patterns = available_patterns()

    while True:
        matched = False

        for pattern_fn in patterns:
            match = pattern_fn(board)
            if match:
                r, c, dr, dc = match
                board = apply_move_matrix(board, r, c, dr, dc)
                move_str = f"{index_to_pos(r, c)} → {index_to_pos(r + 2*dr, c + 2*dc)}"
                path.append(move_str)
                matched = True
                break

        if not matched:
            break

    # Проверяем, решена ли головоломка
    peg_count = sum(row.count('●') for row in board)
    if peg_count == 1:
        return path

    return None
