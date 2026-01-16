"""
core/fast_bitboard_py.py

Чистая Python версия быстрых функций.
Используется если Cython не доступен.

Для максимальной производительности установите Cython:
    pip install cython
    python setup.py build_ext --inplace
"""

from typing import List, Tuple

# Валидная маска английской доски
VALID_MASK = sum(1 << pos for pos in [
    2, 3, 4, 9, 10, 11,
    14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27,
    28, 29, 30, 31, 32, 33, 34,
    37, 38, 39, 44, 45, 46
])

VALID_POSITIONS = [
    2, 3, 4, 9, 10, 11,
    14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27,
    28, 29, 30, 31, 32, 33, 34,
    37, 38, 39, 44, 45, 46
]


def fast_peg_count(pegs: int) -> int:
    """Подсчёт колышков."""
    return bin(pegs).count('1')


def fast_has_peg(pegs: int, pos: int) -> bool:
    """Проверка наличия колышка."""
    return bool(pegs & (1 << pos))


def fast_apply_move(pegs: int, from_pos: int, jumped: int, to_pos: int) -> int:
    """Применяет ход — 3 XOR операции."""
    return pegs ^ (1 << from_pos) ^ (1 << jumped) ^ (1 << to_pos)


def fast_get_moves(pegs: int) -> List[Tuple[int, int, int]]:
    """Генерирует все допустимые ходы."""
    moves = []
    holes = VALID_MASK & ~pegs
    
    # Горизонтальные
    can_right = pegs & (pegs >> 1) & (holes >> 2)
    can_left = pegs & (pegs << 1) & (holes << 2)
    
    # Вертикальные
    can_down = pegs & (pegs >> 7) & (holes >> 14)
    can_up = pegs & (pegs << 7) & (holes << 14)
    
    for pos in VALID_POSITIONS:
        if can_right & (1 << pos) and pos % 7 <= 4:
            moves.append((pos, pos + 1, pos + 2))
        
        if can_left & (1 << pos) and pos % 7 >= 2:
            moves.append((pos, pos - 1, pos - 2))
        
        if can_down & (1 << pos) and pos // 7 <= 4:
            moves.append((pos, pos + 7, pos + 14))
        
        if can_up & (1 << pos) and pos // 7 >= 2:
            moves.append((pos, pos - 7, pos - 14))
    
    return moves


def fast_is_dead(pegs: int) -> bool:
    """Проверка тупика."""
    if bin(pegs).count('1') <= 1:
        return False
    
    holes = VALID_MASK & ~pegs
    
    if pegs & (pegs >> 1) & (holes >> 2):
        return False
    if pegs & (pegs << 1) & (holes << 2):
        return False
    if pegs & (pegs >> 7) & (holes >> 14):
        return False
    if pegs & (pegs << 7) & (holes << 14):
        return False
    
    return True


# Zobrist таблица
import random
random.seed(42)
ZOBRIST_TABLE = {pos: random.getrandbits(64) for pos in VALID_POSITIONS}


def fast_zobrist_hash(pegs: int) -> int:
    """Вычисляет Zobrist хеш."""
    h = 0
    for pos in VALID_POSITIONS:
        if pegs & (1 << pos):
            h ^= ZOBRIST_TABLE[pos]
    return h


def fast_update_zobrist(current_hash: int, from_pos: int, jumped: int, to_pos: int) -> int:
    """Инкрементальное обновление."""
    return current_hash ^ ZOBRIST_TABLE[from_pos] ^ ZOBRIST_TABLE[jumped] ^ ZOBRIST_TABLE[to_pos]


class FastBitBoard:
    """Быстрый BitBoard (Python fallback)."""
    __slots__ = ('pegs', 'zobrist_hash', 'count')
    
    def __init__(self, pegs: int, zobrist_hash: int = 0):
        self.pegs = pegs
        self.count = fast_peg_count(pegs)
        self.zobrist_hash = zobrist_hash or fast_zobrist_hash(pegs)
    
    def apply_move(self, from_pos: int, jumped: int, to_pos: int) -> 'FastBitBoard':
        new_pegs = fast_apply_move(self.pegs, from_pos, jumped, to_pos)
        new_hash = fast_update_zobrist(self.zobrist_hash, from_pos, jumped, to_pos)
        return FastBitBoard(new_pegs, new_hash)
    
    def get_moves(self):
        return fast_get_moves(self.pegs)
    
    def is_solved(self) -> bool:
        return self.count == 1
    
    def is_dead(self) -> bool:
        return fast_is_dead(self.pegs)
    
    def __hash__(self):
        return self.zobrist_hash
    
    def __eq__(self, other):
        if not isinstance(other, FastBitBoard):
            return False
        return self.pegs == other.pegs
    
    def __repr__(self):
        return f"FastBitBoard({self.count} pegs)"
