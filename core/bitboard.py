"""
core/bitboard.py

Сверхбыстрое представление доски через битовые маски.
Для английской доски (33 позиции) — один 64-bit int.
"""

import sys
from typing import List, Tuple, Optional
from functools import lru_cache

# Быстрый popcount (подсчёт битов)
if sys.version_info >= (3, 10):
    # Python 3.10+ имеет встроенный bit_count() (использует CPU popcount)
    def _popcount(x: int) -> int:
        return x.bit_count()
else:
    # Fallback для старых версий Python
    def _popcount(x: int) -> int:
        """Быстрый подсчёт битов (popcount) для Python < 3.10."""
        x = x - ((x >> 1) & 0x5555555555555555)
        x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
        x = (x + (x >> 4)) & 0x0F0F0F0F0F0F0F0F
        return ((x * 0x0101010101010101) >> 56) & 0xFF

# Валидные позиции английской доски (33 клетки)
ENGLISH_VALID_POSITIONS = frozenset([
    2, 3, 4, 9, 10, 11,
    14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27,
    28, 29, 30, 31, 32, 33, 34,
    37, 38, 39, 44, 45, 46
])

VALID_MASK = sum(1 << pos for pos in ENGLISH_VALID_POSITIONS)
CENTER_POS = 24
ENGLISH_START = VALID_MASK ^ (1 << CENTER_POS)
ENGLISH_GOAL = 1 << CENTER_POS


def pos_to_coords(pos: int) -> Tuple[int, int]:
    """Линейная позиция → (row, col)."""
    return pos // 7, pos % 7


def coords_to_pos(row: int, col: int) -> int:
    """(row, col) → линейная позиция."""
    return row * 7 + col


def _rotate_90_pegs(pegs: int) -> int:
    """Поворот на 90° (работает напрямую с pegs, без создания объекта)."""
    new_pegs = 0
    for pos in ENGLISH_VALID_POSITIONS:
        if pegs & (1 << pos):
            r, c = pos // 7, pos % 7
            nr, nc = c, 6 - r
            new_pos = nr * 7 + nc
            if new_pos in ENGLISH_VALID_POSITIONS:
                new_pegs |= (1 << new_pos)
    return new_pegs


def _flip_h_pegs(pegs: int) -> int:
    """Горизонтальное отражение (работает напрямую с pegs, без создания объекта)."""
    new_pegs = 0
    for pos in ENGLISH_VALID_POSITIONS:
        if pegs & (1 << pos):
            r, c = pos // 7, pos % 7
            new_pos = r * 7 + (6 - c)
            if new_pos in ENGLISH_VALID_POSITIONS:
                new_pegs |= (1 << new_pos)
    return new_pegs


class BitBoard:
    """Битовое представление доски Peg Solitaire."""
    __slots__ = ('pegs', '_hash', '_count')

    def __init__(self, pegs: int):
        self.pegs = pegs
        self._hash = hash(pegs)
        self._count = _popcount(pegs)

    @classmethod
    def english_start(cls) -> 'BitBoard':
        """Стандартная английская доска."""
        return cls(ENGLISH_START)

    @classmethod
    def english_goal(cls) -> 'BitBoard':
        """Целевое состояние (1 колышек в центре)."""
        return cls(ENGLISH_GOAL)

    @classmethod
    def from_positions(cls, positions: List[Tuple[int, int]]) -> 'BitBoard':
        """Создаёт доску из списка координат."""
        pegs = 0
        for row, col in positions:
            pegs |= (1 << coords_to_pos(row, col))
        return cls(pegs)

    def peg_count(self) -> int:
        return self._count

    def has_peg(self, pos: int) -> bool:
        return bool(self.pegs & (1 << pos))

    def get_moves(self) -> List[Tuple[int, int, int]]:
        """
        Генерирует все допустимые ходы: (from, jumped, to).
        
        По умолчанию использует геометрию английского креста (33 клетки).
        Если на доске есть фишки за пределами ENGLISH_VALID_POSITIONS,
        считаем доску произвольной 7x7 и генерируем ходы по всем 49 клеткам.
        """
        # Проверяем, есть ли фишки вне английского креста
        if self.pegs & ~VALID_MASK:
            # Произвольная доска 7x7: все 49 клеток валидны
            moves: List[Tuple[int, int, int]] = []
            pegs = self.pegs
            full_mask = (1 << 49) - 1
            holes = full_mask & ~pegs

            for pos in range(49):
                if not (pegs >> pos) & 1:
                    continue
                r, c = divmod(pos, 7)

                # Вправо
                if c <= 4:
                    if ((pegs >> (pos + 1)) & 1) and ((holes >> (pos + 2)) & 1):
                        moves.append((pos, pos + 1, pos + 2))
                # Влево
                if c >= 2:
                    if ((pegs >> (pos - 1)) & 1) and ((holes >> (pos - 2)) & 1):
                        moves.append((pos, pos - 1, pos - 2))
                # Вниз
                if r <= 4:
                    if ((pegs >> (pos + 7)) & 1) and ((holes >> (pos + 14)) & 1):
                        moves.append((pos, pos + 7, pos + 14))
                # Вверх
                if r >= 2:
                    if ((pegs >> (pos - 7)) & 1) and ((holes >> (pos - 14)) & 1):
                        moves.append((pos, pos - 7, pos - 14))

            return moves

        # Классическая английская доска (крест из 33 клеток)
        moves: List[Tuple[int, int, int]] = []
        pegs = self.pegs
        holes = VALID_MASK & ~pegs

        # Горизонтальные
        can_right = pegs & (pegs >> 1) & (holes >> 2)
        can_left = pegs & (pegs << 1) & (holes << 2)
        
        # Вертикальные
        can_down = pegs & (pegs >> 7) & (holes >> 14)
        can_up = pegs & (pegs << 7) & (holes << 14)
        
        # Один проход по позициям вместо двух
        for pos in ENGLISH_VALID_POSITIONS:
            # Горизонтальные ходы
            if can_right & (1 << pos) and pos % 7 <= 4:
                moves.append((pos, pos + 1, pos + 2))
            if can_left & (1 << pos) and pos % 7 >= 2:
                moves.append((pos, pos - 1, pos - 2))
            
            # Вертикальные ходы
            if can_down & (1 << pos) and pos // 7 <= 4:
                to = pos + 14
                if to in ENGLISH_VALID_POSITIONS:
                    moves.append((pos, pos + 7, to))
            if can_up & (1 << pos) and pos // 7 >= 2:
                to = pos - 14
                if to in ENGLISH_VALID_POSITIONS:
                    moves.append((pos, pos - 7, to))

        return moves

    def apply_move(self, from_pos: int, jumped: int, to_pos: int) -> 'BitBoard':
        """Применяет ход — O(1) XOR операции."""
        new_pegs = self.pegs ^ (1 << from_pos) ^ (1 << jumped) ^ (1 << to_pos)
        return BitBoard(new_pegs)

    def is_solved(self) -> bool:
        return self._count == 1

    def is_goal(self) -> bool:
        return self.pegs == ENGLISH_GOAL

    def is_dead(self) -> bool:
        """Проверка тупика (оптимизированная версия)."""
        if self._count <= 1:
            return False

        pegs = self.pegs

        # Произвольная доска 7x7: проверяем ходы по всем 49 клеткам
        if pegs & ~VALID_MASK:
            full_mask = (1 << 49) - 1
            holes = full_mask & ~pegs

            for pos in range(49):
                if not (pegs >> pos) & 1:
                    continue
                r, c = divmod(pos, 7)

                # Вправо
                if c <= 4:
                    if ((pegs >> (pos + 1)) & 1) and ((holes >> (pos + 2)) & 1):
                        return False
                # Влево
                if c >= 2:
                    if ((pegs >> (pos - 1)) & 1) and ((holes >> (pos - 2)) & 1):
                        return False
                # Вниз
                if r <= 4:
                    if ((pegs >> (pos + 7)) & 1) and ((holes >> (pos + 14)) & 1):
                        return False
                # Вверх
                if r >= 2:
                    if ((pegs >> (pos - 7)) & 1) and ((holes >> (pos - 14)) & 1):
                        return False

            return True

        # Классическая английская доска (крест из 33 клеток)
        holes = VALID_MASK & ~pegs
        
        # Проверяем, есть ли хоть один ход (битовые операции)
        can_move = (pegs & (pegs >> 1) & (holes >> 2)) or \
                   (pegs & (pegs << 1) & (holes << 2)) or \
                   (pegs & (pegs >> 7) & (holes >> 14)) or \
                   (pegs & (pegs << 7) & (holes << 14))
        return not bool(can_move)

    def canonical(self) -> 'BitBoard':
        """
        Каноническая форма (минимальная из 8 симметрий).
        
        Для классической английской доски (33 клетки) используем все 8 симметрий.
        Для произвольной 7x7 доски (есть фишки вне ENGLISH_VALID_POSITIONS)
        симметрии английского креста неприменимы, поэтому возвращаем доску как есть.
        """
        # Для произвольной доски 7x7 не применяем симметрии английского креста
        if self.pegs & ~VALID_MASK:
            return self

        # Оптимизация: вычисляем все варианты напрямую через pegs, без создания объектов
        variants_pegs = [self.pegs]
        current_pegs = self.pegs
        
        # 3 поворота на 90°
        for _ in range(3):
            current_pegs = _rotate_90_pegs(current_pegs)
            variants_pegs.append(current_pegs)
        
        # Отражение
        flipped_pegs = _flip_h_pegs(self.pegs)
        variants_pegs.append(flipped_pegs)
        current_pegs = flipped_pegs
        
        # 3 поворота отражённой версии
        for _ in range(3):
            current_pegs = _rotate_90_pegs(current_pegs)
            variants_pegs.append(current_pegs)
        
        # Находим минимальный и создаём объект только один раз
        min_pegs = min(variants_pegs)
        if min_pegs == self.pegs:
            return self
        return BitBoard(min_pegs)

    def _rotate_90(self) -> 'BitBoard':
        """Поворот на 90° (для обратной совместимости)."""
        return BitBoard(_rotate_90_pegs(self.pegs))

    def _flip_h(self) -> 'BitBoard':
        """Горизонтальное отражение (для обратной совместимости)."""
        return BitBoard(_flip_h_pegs(self.pegs))

    def to_string(self) -> str:
        """
        Текстовое представление доски.
        
        - Для классической английской доски рисует крест (пустые клетки вне ENGLISH_VALID_POSITIONS).
        - Для произвольной 7x7 доски рисует полное поле 7x7 (все 49 клеток видны).
        """
        lines = []
        generic = bool(self.pegs & ~VALID_MASK)
        for r in range(7):
            row = ""
            for c in range(7):
                pos = r * 7 + c
                if generic:
                    # Полная 7x7: показываем и валидные, и "нестандартные" клетки
                    row += ("● " if self.has_peg(pos) else "○ ")
                else:
                    # Классический крест: как раньше
                    if pos not in ENGLISH_VALID_POSITIONS:
                        row += "  "
                    elif self.has_peg(pos):
                        row += "● "
                    else:
                        row += "○ "
            lines.append(row.rstrip())
        return "\n".join(lines)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other) -> bool:
        return isinstance(other, BitBoard) and self.pegs == other.pegs

    def __lt__(self, other: 'BitBoard') -> bool:
        return self.pegs < other.pegs

    def __repr__(self) -> str:
        return f"BitBoard({self._count} pegs)"
