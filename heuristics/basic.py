"""
heuristics/basic.py

Базовые эвристические функции.
"""

from core.bitboard import BitBoard, ENGLISH_VALID_POSITIONS


def heuristic_peg_count(board: BitBoard) -> int:
    """
    Базовая эвристика: количество колышков - 1.
    Это минимум ходов для победы.
    """
    return board.peg_count() - 1


def heuristic_distance_to_center(board: BitBoard, center: tuple = (3, 3)) -> float:
    """
    Суммарное манхэттенское расстояние колышков до центра.
    Чем ближе к центру — тем лучше.
    """
    cr, cc = center
    total = 0
    for pos in ENGLISH_VALID_POSITIONS:
        if board.has_peg(pos):
            r, c = pos // 7, pos % 7
            total += abs(r - cr) + abs(c - cc)
    return total


def combined_heuristic(board: BitBoard, steps: int, aggressive: bool = False) -> float:
    """
    Комбинированная эвристика для A*.
    
    f(n) = g(n) + h(n)
    """
    from .advanced import heuristic_mobility, heuristic_isolated
    
    h = heuristic_peg_count(board)
    
    if aggressive:
        h *= 2
        h += heuristic_distance_to_center(board) * 0.5
        h += heuristic_isolated(board) * 1.5
        h -= heuristic_mobility(board) * 2
    else:
        h += heuristic_distance_to_center(board) * 0.3
        h += heuristic_isolated(board) * 0.5
        h -= heuristic_mobility(board) * 0.5
    
    return steps + h
