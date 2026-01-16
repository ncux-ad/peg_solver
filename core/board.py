"""
core/board.py

Представление доски через frozenset.
"""

from typing import FrozenSet, Tuple, Optional, List
from .utils import DIRECTIONS, PEG, HOLE, EMPTY, index_to_pos

Position = Tuple[int, int]


class Board:
    """
    Иммутабельное представление доски через frozenset.
    Хранит только позиции колышков — эффективно по памяти.
    """
    __slots__ = ('pegs', 'holes', 'rows', 'cols', '_hash')

    def __init__(self, pegs: FrozenSet[Position], holes: FrozenSet[Position],
                 rows: int = 7, cols: int = 7):
        self.pegs = pegs
        self.holes = holes
        self.rows = rows
        self.cols = cols
        self._hash = hash(self.pegs)

    @classmethod
    def from_matrix(cls, matrix: List[List[str]]) -> 'Board':
        """Создаёт Board из матричного представления."""
        pegs = set()
        holes = set()
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        for r in range(rows):
            for c in range(cols):
                if matrix[r][c] == PEG:
                    pegs.add((r, c))
                elif matrix[r][c] == HOLE:
                    holes.add((r, c))
        return cls(frozenset(pegs), frozenset(holes), rows, cols)

    def to_matrix(self) -> List[List[str]]:
        """Конвертирует обратно в матрицу."""
        matrix = [[EMPTY for _ in range(self.cols)] for _ in range(self.rows)]
        for r, c in self.pegs:
            matrix[r][c] = PEG
        for r, c in self.holes:
            matrix[r][c] = HOLE
        return matrix

    def peg_count(self) -> int:
        """Количество колышков — O(1)."""
        return len(self.pegs)

    def is_valid_move(self, r: int, c: int, dr: int, dc: int) -> bool:
        """Проверка допустимости хода."""
        r1, c1 = r + dr, c + dc
        r2, c2 = r + 2 * dr, c + 2 * dc
        return (
            (r, c) in self.pegs and
            (r1, c1) in self.pegs and
            (r2, c2) in self.holes
        )

    def apply_move(self, r: int, c: int, dr: int, dc: int) -> 'Board':
        """Возвращает новую доску после хода."""
        r1, c1 = r + dr, c + dc
        r2, c2 = r + 2 * dr, c + 2 * dc
        new_pegs = (self.pegs - {(r, c), (r1, c1)}) | {(r2, c2)}
        new_holes = (self.holes - {(r2, c2)}) | {(r, c), (r1, c1)}
        return Board(new_pegs, new_holes, self.rows, self.cols)

    def get_all_moves(self) -> List[Tuple[int, int, int, int]]:
        """Генерирует все допустимые ходы."""
        moves = []
        for r, c in self.pegs:
            for dr, dc in DIRECTIONS:
                if self.is_valid_move(r, c, dr, dc):
                    moves.append((r, c, dr, dc))
        return moves

    def reverse_move(self, r: int, c: int, dr: int, dc: int) -> Optional['Board']:
        """Обратный ход для reverse solver."""
        r1, c1 = r + dr, c + dc
        r2, c2 = r + 2 * dr, c + 2 * dc
        if (r, c) not in self.holes or (r1, c1) not in self.holes or (r2, c2) not in self.pegs:
            return None
        new_pegs = (self.pegs - {(r2, c2)}) | {(r, c), (r1, c1)}
        new_holes = (self.holes - {(r, c), (r1, c1)}) | {(r2, c2)}
        return Board(new_pegs, new_holes, self.rows, self.cols)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return False
        return self.pegs == other.pegs

    def __repr__(self) -> str:
        return f"Board({self.peg_count()} pegs)"
