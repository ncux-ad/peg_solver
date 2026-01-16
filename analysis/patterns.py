"""
analysis/patterns.py

Шаблоны (паттерны) для жадного решения.
"""

from typing import Optional, Tuple, List
from copy import deepcopy


def match_line_of_three(board: List[List[str]]) -> Optional[Tuple[int, int, int, int]]:
    """Находит три клетки подряд: ●●○ или ○●●."""
    rows, cols = len(board), len(board[0])
    
    for r in range(rows):
        for c in range(cols - 2):
            if board[r][c] == board[r][c+1] == '●' and board[r][c+2] == '○':
                return (r, c, 0, 1)
            if board[r][c] == '○' and board[r][c+1] == board[r][c+2] == '●':
                return (r, c+2, 0, -1)
    
    for c in range(cols):
        for r in range(rows - 2):
            if board[r][c] == board[r+1][c] == '●' and board[r+2][c] == '○':
                return (r, c, 1, 0)
            if board[r][c] == '○' and board[r+1][c] == board[r+2][c] == '●':
                return (r+2, c, -1, 0)
    
    return None


def match_line_of_four(board: List[List[str]]) -> Optional[Tuple[int, int, int, int]]:
    """Находит ●●●○ или ○●●●."""
    rows, cols = len(board), len(board[0])
    
    for r in range(rows):
        for c in range(cols - 3):
            if all(board[r][c+i] == '●' for i in range(3)) and board[r][c+3] == '○':
                return (r, c, 0, 1)
            if board[r][c] == '○' and all(board[r][c+i] == '●' for i in range(1, 4)):
                return (r, c+3, 0, -1)
    
    for c in range(cols):
        for r in range(rows - 3):
            if all(board[r+i][c] == '●' for i in range(3)) and board[r+3][c] == '○':
                return (r, c, 1, 0)
            if board[r][c] == '○' and all(board[r+i][c] == '●' for i in range(1, 4)):
                return (r+3, c, -1, 0)
    
    return None


def match_patterns(board: List[List[str]]) -> Optional[Tuple[int, int, int, int]]:
    """Ищет любой подходящий паттерн."""
    patterns = [match_line_of_four, match_line_of_three]
    
    for pattern_fn in patterns:
        result = pattern_fn(board)
        if result:
            return result
    
    return None


def apply_pattern_sequence(board: List[List[str]]) -> Optional[List[str]]:
    """
    Жадно применяет паттерны пока возможно.
    Возвращает список ходов если решено, иначе None.
    """
    path = []
    board = deepcopy(board)
    
    while True:
        match = match_patterns(board)
        if not match:
            break
        
        r, c, dr, dc = match
        # Применяем ход
        r2, c2 = r + 2*dr, c + 2*dc
        board[r][c] = '○'
        board[r + dr][c + dc] = '○'
        board[r2][c2] = '●'
        
        from core.utils import index_to_pos
        move_str = f"{index_to_pos(r, c)} → {index_to_pos(r2, c2)}"
        path.append(move_str)
    
    peg_count = sum(row.count('●') for row in board)
    return path if peg_count == 1 else None
