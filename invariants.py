"""
invariants.py

Pagoda functions и инварианты для pruning недостижимых состояний.
Pagoda function — классический метод доказательства невозможности решения.
"""

from typing import Dict, Tuple, FrozenSet, TYPE_CHECKING

if TYPE_CHECKING:
    from board import Board

Position = Tuple[int, int]


# Классические веса Pagoda для английской доски 7x7 (крест)
# Веса подобраны так, чтобы любой ход не увеличивал сумму
ENGLISH_PAGODA_WEIGHTS: Dict[Position, float] = {
    # Центральный крест имеет положительные веса
    # Углы и края — отрицательные или нулевые
    (0, 2): 1, (0, 3): 2, (0, 4): 1,
    (1, 2): 2, (1, 3): 4, (1, 4): 2,
    (2, 0): 1, (2, 1): 2, (2, 2): 3, (2, 3): 4, (2, 4): 3, (2, 5): 2, (2, 6): 1,
    (3, 0): 2, (3, 1): 4, (3, 2): 4, (3, 3): 6, (3, 4): 4, (3, 5): 4, (3, 6): 2,
    (4, 0): 1, (4, 1): 2, (4, 2): 3, (4, 3): 4, (4, 4): 3, (4, 5): 2, (4, 6): 1,
    (5, 2): 2, (5, 3): 4, (5, 4): 2,
    (6, 2): 1, (6, 3): 2, (6, 4): 1,
}


def create_pagoda_weights(rows: int, cols: int, center: Tuple[int, int]) -> Dict[Position, float]:
    """
    Создаёт pagoda-веса на основе расстояния до центра.
    Более точная функция для произвольных досок.
    """
    weights = {}
    cr, cc = center
    max_dist = max(rows, cols)

    for r in range(rows):
        for c in range(cols):
            dist = abs(r - cr) + abs(c - cc)
            # Веса убывают от центра
            weights[(r, c)] = max(0, max_dist - dist)

    return weights


def pagoda_value(pegs: FrozenSet[Position], weights: Dict[Position, float]) -> float:
    """
    Вычисляет значение pagoda-функции для набора колышков.
    """
    return sum(weights.get(pos, 0) for pos in pegs)


def is_solvable_by_pagoda(board: 'Board', target_pos: Position,
                          weights: Dict[Position, float] = None) -> bool:
    """
    Проверяет, может ли позиция быть решена до единственного колышка в target_pos.
    Использует pagoda function для раннего отсечения.

    Принцип: если текущее значение pagoda меньше значения целевой позиции,
    решение невозможно (pagoda никогда не увеличивается при ходах).
    """
    if weights is None:
        weights = ENGLISH_PAGODA_WEIGHTS

    current_value = pagoda_value(board.pegs, weights)
    target_value = weights.get(target_pos, 0)

    return current_value >= target_value


def count_isolated_pegs(pegs: FrozenSet[Position]) -> int:
    """
    Подсчёт изолированных колышков (без соседей).
    Оптимизировано для frozenset.
    """
    count = 0
    for r, c in pegs:
        has_neighbor = any(
            (r + dr, c + dc) in pegs
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        )
        if not has_neighbor:
            count += 1
    return count


def count_mobility(board: 'Board') -> int:
    """
    Считает количество доступных ходов (mobility).
    Высокая мобильность = больше возможностей = лучше.
    """
    return len(board.get_all_moves())


def is_dead_position(board: 'Board') -> bool:
    """
    Проверяет, является ли позиция "мёртвой" (нет ходов, но больше 1 колышка).
    """
    return board.peg_count() > 1 and count_mobility(board) == 0


def get_symmetry_canonical(pegs: FrozenSet[Position], rows: int, cols: int) -> FrozenSet[Position]:
    """
    Возвращает каноническую форму позиции с учётом симметрий.
    Для квадратной доски есть 8 симметрий (4 поворота × 2 отражения).
    Выбирает лексикографически минимальную.
    """
    if rows != cols:
        return pegs  # Только для квадратных досок

    def rotate_90(positions: FrozenSet[Position]) -> FrozenSet[Position]:
        return frozenset((c, rows - 1 - r) for r, c in positions)

    def flip_horizontal(positions: FrozenSet[Position]) -> FrozenSet[Position]:
        return frozenset((r, cols - 1 - c) for r, c in positions)

    # Генерируем все 8 симметрий
    symmetries = []
    current = pegs
    for _ in range(4):
        symmetries.append(current)
        symmetries.append(flip_horizontal(current))
        current = rotate_90(current)

    # Возвращаем минимальную (для каноничности)
    return min(symmetries, key=lambda s: tuple(sorted(s)))
