"""
heuristics/pagoda.py

Pagoda function — классический метод pruning для Peg Solitaire.
"""

from core.bitboard import BitBoard, CENTER_POS

# Классические веса Pagoda для английской доски
PAGODA_WEIGHTS = {
    2: 1, 3: 2, 4: 1,
    9: 2, 10: 4, 11: 2,
    14: 1, 15: 2, 16: 3, 17: 4, 18: 3, 19: 2, 20: 1,
    21: 2, 22: 4, 23: 4, 24: 6, 25: 4, 26: 4, 27: 2,
    28: 1, 29: 2, 30: 3, 31: 4, 32: 3, 33: 2, 34: 1,
    37: 2, 38: 4, 39: 2,
    44: 1, 45: 2, 46: 1,
}


def pagoda_value(board: BitBoard) -> int:
    """
    Вычисляет значение Pagoda функции.
    
    Pagoda никогда не увеличивается при ходе.
    Если текущее значение < целевого — решение невозможно.
    """
    total = 0
    for pos, weight in PAGODA_WEIGHTS.items():
        if board.has_peg(pos):
            total += weight
    return total


def is_solvable_by_pagoda(board: BitBoard, target_pos: int = CENTER_POS) -> bool:
    """
    Проверяет, может ли позиция быть решена.
    
    Если pagoda(current) < pagoda(target) — решение невозможно.
    """
    current = pagoda_value(board)
    target = PAGODA_WEIGHTS.get(target_pos, 0)
    return current >= target
