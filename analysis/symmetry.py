"""
analysis/symmetry.py

Работа с симметриями доски.
"""

from typing import FrozenSet, Tuple

Position = Tuple[int, int]


def rotate_90(positions: FrozenSet[Position], size: int = 7) -> FrozenSet[Position]:
    """Поворот на 90° по часовой стрелке."""
    return frozenset((c, size - 1 - r) for r, c in positions)


def flip_horizontal(positions: FrozenSet[Position], size: int = 7) -> FrozenSet[Position]:
    """Отражение по горизонтали."""
    return frozenset((r, size - 1 - c) for r, c in positions)


def flip_vertical(positions: FrozenSet[Position], size: int = 7) -> FrozenSet[Position]:
    """Отражение по вертикали."""
    return frozenset((size - 1 - r, c) for r, c in positions)


def get_all_symmetries(positions: FrozenSet[Position], size: int = 7) -> list:
    """
    Генерирует все 8 симметрий позиции.
    (4 поворота × 2 отражения)
    """
    symmetries = []
    current = positions
    
    for _ in range(4):
        symmetries.append(current)
        symmetries.append(flip_horizontal(current, size))
        current = rotate_90(current, size)
    
    return symmetries


def get_symmetry_canonical(positions: FrozenSet[Position], size: int = 7) -> FrozenSet[Position]:
    """
    Возвращает каноническую форму (минимальную из симметрий).
    Используется для сокращения visited set.
    """
    symmetries = get_all_symmetries(positions, size)
    return min(symmetries, key=lambda s: tuple(sorted(s)))


def count_symmetries(positions: FrozenSet[Position], size: int = 7) -> int:
    """
    Считает уникальные симметрии позиции.
    Если позиция симметрична, число < 8.
    """
    symmetries = get_all_symmetries(positions, size)
    return len(set(tuple(sorted(s)) for s in symmetries))
