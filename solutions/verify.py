"""
solutions/verify.py

Общая проверка решений для произвольных BitBoard (7x7, с вырезанными ячейками).
"""

from typing import List, Tuple

from core.bitboard import BitBoard
from core.utils import PEG, HOLE, EMPTY


Move = Tuple[int, int, int]


def verify_bitboard_solution(board: BitBoard, moves: List[Move], require_center: bool = False) -> bool:
    """
    Проверяет корректность решения на BitBoard с учётом valid_mask.

    Правила:
    - каждый ход должен быть допустимым:
      - from, jumped, to находятся в пределах 0..48;
      - все три клетки входят в board.valid_mask (клетка существует);
      - в from и jumped есть колышки, в to — дырка (валидная клетка без колышка);
    - после применения всех ходов остаётся ровно один колышек;
    - если require_center=True, единственный колышек должен быть в центре (позиция 24).
    """
    # Пустое решение недопустимо, если начальное состояние не уже решено
    if not moves:
        return board.peg_count() == 1

    pegs = board.pegs
    valid_mask = board.valid_mask

    for from_pos, jumped, to_pos in moves:
        # Проверяем диапазон позиций
        if not (0 <= from_pos < 49 and 0 <= jumped < 49 and 0 <= to_pos < 49):
            return False

        # Клетки должны существовать на доске
        if not ((valid_mask >> from_pos) & 1):
            return False
        if not ((valid_mask >> jumped) & 1):
            return False
        if not ((valid_mask >> to_pos) & 1):
            return False

        # В from и jumped должны быть колышки, в to — дырка (валидная клетка без колышка)
        if not (pegs >> from_pos) & 1:
            return False
        if not (pegs >> jumped) & 1:
            return False
        if (pegs >> to_pos) & 1:
            return False

        # Применяем ход
        pegs ^= (1 << from_pos) ^ (1 << jumped) ^ (1 << to_pos)

    # Подсчитываем количество колышков в финальном состоянии
    if pegs == 0:
        return False

    if hasattr(pegs, "bit_count"):
        peg_count = pegs.bit_count()
    else:
        # Fallback popcount для старых версий Python
        x = pegs
        x = x - ((x >> 1) & 0x5555555555555555)
        x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
        x = (x + (x >> 4)) & 0x0F0F0F0F0F0F0F0F
        peg_count = ((x * 0x0101010101010101) >> 56) & 0xFF

    if peg_count != 1:
        return False

    if require_center:
        # Единственный установленный бит должен быть в центре (24)
        return pegs == (1 << 24)

    return True


def bitboard_to_matrix(board: BitBoard) -> List[List[str]]:
    """
    Строит матрицу 7x7 из BitBoard для целей кэширования.

    Семантика:
    - Клетки внутри board.valid_mask существуют на доске:
      - если в позиции есть колышек → PEG ('●');
      - иначе → HOLE ('○');
    - Клетки вне board.valid_mask считаются вырезанными → EMPTY ('▫').
    """
    matrix: List[List[str]] = [[EMPTY for _ in range(7)] for _ in range(7)]
    pegs = board.pegs
    valid_mask = board.valid_mask

    for pos in range(49):
        r, c = divmod(pos, 7)
        if (valid_mask >> pos) & 1:
            if (pegs >> pos) & 1:
                matrix[r][c] = PEG
            else:
                matrix[r][c] = HOLE
        else:
            matrix[r][c] = EMPTY

    return matrix

