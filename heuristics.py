"""
heuristics.py

Продвинутые эвристические функции для A* поиска в Peg Solitaire.
"""

from typing import Tuple, TYPE_CHECKING
from invariants import count_isolated_pegs, count_mobility, ENGLISH_PAGODA_WEIGHTS, pagoda_value

if TYPE_CHECKING:
    from board import Board

Position = Tuple[int, int]


def heuristic_peg_count(board: 'Board') -> int:
    """
    Базовая эвристика: количество колышков - 1.
    Минимум ходов для победы = pegs - 1.
    """
    return board.peg_count() - 1


def heuristic_distance_to_center(board: 'Board', center: Position) -> float:
    """
    Суммарное манхэттенское расстояние всех колышков до центра.
    Чем ближе к центру — тем лучше.
    """
    cr, cc = center
    return sum(abs(r - cr) + abs(c - cc) for r, c in board.pegs)


def heuristic_isolated_penalty(board: 'Board') -> int:
    """
    Штраф за изолированные колышки.
    Изолированный колышек труднее убрать.
    """
    return 10 * count_isolated_pegs(board.pegs)


def heuristic_mobility_bonus(board: 'Board') -> float:
    """
    Бонус за мобильность (количество доступных ходов).
    Больше ходов = больше гибкости = лучше.
    Возвращает отрицательное значение (бонус уменьшает приоритет в min-heap).
    """
    mobility = count_mobility(board)
    # Нормализуем: максимум ~50 ходов для полной доски
    return -mobility * 0.5


def heuristic_edge_penalty(board: 'Board') -> int:
    """
    Штраф за колышки на краях доски.
    Колышки на краях сложнее использовать.
    """
    penalty = 0
    for r, c in board.pegs:
        # Проверяем, на краю ли колышек
        if r == 0 or r == board.rows - 1 or c == 0 or c == board.cols - 1:
            penalty += 2
    return penalty


def heuristic_cluster_bonus(board: 'Board') -> float:
    """
    Бонус за кластеризацию колышков.
    Колышки рядом друг с другом легче обрабатывать.
    """
    if board.peg_count() <= 1:
        return 0

    total_neighbors = 0
    for r, c in board.pegs:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if (r + dr, c + dc) in board.pegs:
                total_neighbors += 1

    # Возвращаем отрицательное значение (бонус)
    return -total_neighbors * 0.3


def heuristic_pagoda_potential(board: 'Board', target: Position) -> float:
    """
    Оценка на основе pagoda function.
    Чем ближе к целевому значению — тем лучше.
    """
    current = pagoda_value(board.pegs, ENGLISH_PAGODA_WEIGHTS)
    target_value = ENGLISH_PAGODA_WEIGHTS.get(target, 0)
    return (current - target_value) * 0.1


def combined_heuristic(board: 'Board', steps: int, center: Position) -> float:
    """
    Комбинированная эвристика для A*.
    f(n) = g(n) + h(n), где g = steps, h = эвристическая оценка.
    """
    # Базовые компоненты
    h = heuristic_peg_count(board)

    # Дополнительные факторы с весами
    h += heuristic_distance_to_center(board, center) * 0.3
    h += heuristic_isolated_penalty(board)
    h += heuristic_mobility_bonus(board)
    h += heuristic_edge_penalty(board) * 0.5
    h += heuristic_cluster_bonus(board)

    return steps + h


def combined_heuristic_aggressive(board: 'Board', steps: int, center: Position) -> float:
    """
    Агрессивная эвристика — быстрее находит решение, но может быть неоптимальной.
    Увеличиваем веса эвристик относительно g(n).
    """
    h = heuristic_peg_count(board) * 2
    h += heuristic_distance_to_center(board, center) * 0.5
    h += heuristic_isolated_penalty(board) * 1.5
    h += heuristic_mobility_bonus(board) * 2

    return steps + h


# === Legacy функции для обратной совместимости ===

def heuristic_basic(pegs: int, steps: int) -> int:
    """Legacy: базовая эвристика."""
    return pegs + steps
