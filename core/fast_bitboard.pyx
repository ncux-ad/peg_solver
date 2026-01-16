# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""
core/fast_bitboard.pyx

Cython-оптимизированные функции для BitBoard.
Ускорение в 50-100x по сравнению с чистым Python.
"""

from libc.stdint cimport uint64_t, int32_t
from cpython cimport array
import array

# Валидные позиции английской доски
cdef uint64_t VALID_MASK = 0x1010101817C3E3E3E17C3810ULL
cdef int CENTER_POS = 24

# Позиции для быстрой генерации ходов
cdef int[33] VALID_POSITIONS = [
    2, 3, 4, 9, 10, 11,
    14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27,
    28, 29, 30, 31, 32, 33, 34,
    37, 38, 39, 44, 45, 46, -1
]


cdef inline int popcount64(uint64_t x) nogil:
    """Быстрый подсчёт битов (popcount)."""
    x = x - ((x >> 1) & 0x5555555555555555ULL)
    x = (x & 0x3333333333333333ULL) + ((x >> 2) & 0x3333333333333333ULL)
    x = (x + (x >> 4)) & 0x0F0F0F0F0F0F0F0FULL
    return (x * 0x0101010101010101ULL) >> 56


cpdef int fast_peg_count(uint64_t pegs):
    """Подсчёт колышков — O(1)."""
    return popcount64(pegs)


cpdef bint fast_has_peg(uint64_t pegs, int pos):
    """Проверка наличия колышка."""
    return (pegs >> pos) & 1


cpdef uint64_t fast_apply_move(uint64_t pegs, int from_pos, int jumped, int to_pos):
    """
    Применяет ход — 3 XOR операции.
    
    Returns:
        Новая битовая маска
    """
    return pegs ^ (1ULL << from_pos) ^ (1ULL << jumped) ^ (1ULL << to_pos)


cpdef list fast_get_moves(uint64_t pegs):
    """
    Генерирует все допустимые ходы.
    
    Returns:
        Список кортежей (from, jumped, to)
    """
    cdef list moves = []
    cdef uint64_t holes = VALID_MASK & ~pegs
    cdef uint64_t can_right, can_left, can_down, can_up
    cdef int pos, to_pos
    cdef int i
    
    # Горизонтальные ходы
    can_right = pegs & (pegs >> 1) & (holes >> 2)
    can_left = pegs & (pegs << 1) & (holes << 2)
    
    # Вертикальные ходы
    can_down = pegs & (pegs >> 7) & (holes >> 14)
    can_up = pegs & (pegs << 7) & (holes << 14)
    
    i = 0
    while VALID_POSITIONS[i] >= 0:
        pos = VALID_POSITIONS[i]
        
        # Вправо
        if (can_right >> pos) & 1:
            if pos % 7 <= 4:
                moves.append((pos, pos + 1, pos + 2))
        
        # Влево
        if (can_left >> pos) & 1:
            if pos % 7 >= 2:
                moves.append((pos, pos - 1, pos - 2))
        
        # Вниз
        if (can_down >> pos) & 1:
            if pos // 7 <= 4:
                to_pos = pos + 14
                moves.append((pos, pos + 7, to_pos))
        
        # Вверх
        if (can_up >> pos) & 1:
            if pos // 7 >= 2:
                to_pos = pos - 14
                moves.append((pos, pos - 7, to_pos))
        
        i += 1
    
    return moves


cpdef bint fast_is_dead(uint64_t pegs):
    """Проверка тупика: нет ходов, но > 1 колышка."""
    if popcount64(pegs) <= 1:
        return False
    
    cdef uint64_t holes = VALID_MASK & ~pegs
    cdef uint64_t can_move
    
    # Проверяем, есть ли хоть один ход
    can_move = pegs & (pegs >> 1) & (holes >> 2)  # right
    if can_move:
        return False
    
    can_move = pegs & (pegs << 1) & (holes << 2)  # left
    if can_move:
        return False
    
    can_move = pegs & (pegs >> 7) & (holes >> 14)  # down
    if can_move:
        return False
    
    can_move = pegs & (pegs << 7) & (holes << 14)  # up
    if can_move:
        return False
    
    return True


# =====================================================
# ZOBRIST HASHING (Cython версия)
# =====================================================

cdef uint64_t[64] ZOBRIST_TABLE

def init_zobrist():
    """Инициализация Zobrist таблицы."""
    import random
    random.seed(42)
    
    cdef int i
    for i in range(64):
        ZOBRIST_TABLE[i] = random.getrandbits(64)

# Инициализируем при импорте
init_zobrist()


cpdef uint64_t fast_zobrist_hash(uint64_t pegs):
    """Вычисляет Zobrist хеш."""
    cdef uint64_t h = 0
    cdef int i = 0
    
    while VALID_POSITIONS[i] >= 0:
        if (pegs >> VALID_POSITIONS[i]) & 1:
            h ^= ZOBRIST_TABLE[VALID_POSITIONS[i]]
        i += 1
    
    return h


cpdef uint64_t fast_update_zobrist(uint64_t current_hash, int from_pos, int jumped, int to_pos):
    """Инкрементальное обновление Zobrist хеша."""
    return current_hash ^ ZOBRIST_TABLE[from_pos] ^ ZOBRIST_TABLE[jumped] ^ ZOBRIST_TABLE[to_pos]


# =====================================================
# DFS РЕШАТЕЛЬ (полностью на Cython)
# =====================================================

cdef class FastBitBoard:
    """
    Быстрый BitBoard на Cython.
    """
    cdef public uint64_t pegs
    cdef public uint64_t zobrist_hash
    cdef public int count
    
    def __init__(self, uint64_t pegs, uint64_t zobrist_hash=0):
        self.pegs = pegs
        self.count = popcount64(pegs)
        if zobrist_hash == 0:
            self.zobrist_hash = fast_zobrist_hash(pegs)
        else:
            self.zobrist_hash = zobrist_hash
    
    cpdef FastBitBoard apply_move(self, int from_pos, int jumped, int to_pos):
        cdef uint64_t new_pegs = fast_apply_move(self.pegs, from_pos, jumped, to_pos)
        cdef uint64_t new_hash = fast_update_zobrist(self.zobrist_hash, from_pos, jumped, to_pos)
        return FastBitBoard(new_pegs, new_hash)
    
    cpdef list get_moves(self):
        return fast_get_moves(self.pegs)
    
    cpdef bint is_solved(self):
        return self.count == 1
    
    cpdef bint is_dead(self):
        return fast_is_dead(self.pegs)
    
    def __hash__(self):
        return self.zobrist_hash
    
    def __eq__(self, other):
        if not isinstance(other, FastBitBoard):
            return False
        return self.pegs == (<FastBitBoard>other).pegs
