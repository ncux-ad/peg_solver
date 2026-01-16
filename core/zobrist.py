"""
core/zobrist.py

Zobrist Hashing — инкрементальное хеширование состояний.

Преимущества:
- O(1) обновление хеша при ходе (3 XOR операции)
- Нет пересчёта всего состояния
- Идеально для DFS/IDA* с backtracking
"""

import random
from typing import Dict, Tuple

from .bitboard import ENGLISH_VALID_POSITIONS

# Инициализация генератора для воспроизводимости
random.seed(42)

# Zobrist таблица: для каждой позиции — случайное 64-bit число
# Когда колышек есть — XOR с этим числом
ZOBRIST_TABLE: Dict[int, int] = {
    pos: random.getrandbits(64) for pos in ENGLISH_VALID_POSITIONS
}


def compute_zobrist_hash(pegs: int) -> int:
    """
    Вычисляет Zobrist хеш для битовой маски колышков.
    
    Args:
        pegs: битовая маска позиций колышков
        
    Returns:
        64-bit Zobrist хеш
    """
    h = 0
    for pos in ENGLISH_VALID_POSITIONS:
        if pegs & (1 << pos):
            h ^= ZOBRIST_TABLE[pos]
    return h


def update_zobrist_hash(current_hash: int, from_pos: int, jumped_pos: int, to_pos: int) -> int:
    """
    Инкрементально обновляет Zobrist хеш после хода.
    
    Ход: from_pos → to_pos (перепрыгивая jumped_pos)
    - Убираем колышек с from_pos: XOR
    - Убираем колышек с jumped_pos: XOR
    - Добавляем колышек на to_pos: XOR
    
    Всего 3 XOR операции = O(1)!
    
    Args:
        current_hash: текущий хеш
        from_pos, jumped_pos, to_pos: позиции хода
        
    Returns:
        Новый хеш
    """
    new_hash = current_hash
    new_hash ^= ZOBRIST_TABLE[from_pos]   # убираем
    new_hash ^= ZOBRIST_TABLE[jumped_pos] # убираем
    new_hash ^= ZOBRIST_TABLE[to_pos]     # добавляем
    return new_hash


class ZobristBitBoard:
    """
    BitBoard с Zobrist хешированием.
    
    Хеш обновляется инкрементально при каждом ходе.
    Идеально для поиска с backtracking.
    """
    __slots__ = ('pegs', 'zobrist_hash', '_count')
    
    def __init__(self, pegs: int, zobrist_hash: int = None):
        self.pegs = pegs
        self._count = bin(pegs).count('1')
        
        if zobrist_hash is None:
            self.zobrist_hash = compute_zobrist_hash(pegs)
        else:
            self.zobrist_hash = zobrist_hash
    
    @classmethod
    def english_start(cls) -> 'ZobristBitBoard':
        """Стандартная английская доска."""
        from .bitboard import ENGLISH_START
        return cls(ENGLISH_START)
    
    def peg_count(self) -> int:
        return self._count
    
    def has_peg(self, pos: int) -> bool:
        return bool(self.pegs & (1 << pos))
    
    def apply_move(self, from_pos: int, jumped: int, to_pos: int) -> 'ZobristBitBoard':
        """
        Применяет ход с инкрементальным обновлением хеша.
        """
        new_pegs = self.pegs ^ (1 << from_pos) ^ (1 << jumped) ^ (1 << to_pos)
        new_hash = update_zobrist_hash(self.zobrist_hash, from_pos, jumped, to_pos)
        return ZobristBitBoard(new_pegs, new_hash)
    
    def get_moves(self):
        """Генерирует все допустимые ходы."""
        from .bitboard import VALID_MASK
        
        moves = []
        pegs = self.pegs
        holes = VALID_MASK & ~pegs
        
        # Горизонтальные
        can_right = pegs & (pegs >> 1) & (holes >> 2)
        can_left = pegs & (pegs << 1) & (holes << 2)
        for pos in ENGLISH_VALID_POSITIONS:
            if can_right & (1 << pos) and pos % 7 <= 4:
                moves.append((pos, pos + 1, pos + 2))
            if can_left & (1 << pos) and pos % 7 >= 2:
                moves.append((pos, pos - 1, pos - 2))
        
        # Вертикальные
        can_down = pegs & (pegs >> 7) & (holes >> 14)
        can_up = pegs & (pegs << 7) & (holes << 14)
        for pos in ENGLISH_VALID_POSITIONS:
            if can_down & (1 << pos) and pos // 7 <= 4:
                to = pos + 14
                if to in ENGLISH_VALID_POSITIONS:
                    moves.append((pos, pos + 7, to))
            if can_up & (1 << pos) and pos // 7 >= 2:
                to = pos - 14
                if to in ENGLISH_VALID_POSITIONS:
                    moves.append((pos, pos - 7, to))
        
        return moves
    
    def is_solved(self) -> bool:
        return self._count == 1
    
    def __hash__(self) -> int:
        # Используем Zobrist хеш напрямую!
        return self.zobrist_hash
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, ZobristBitBoard):
            return False
        # Сначала сравниваем хеши (быстро), потом pegs (на случай коллизии)
        return self.zobrist_hash == other.zobrist_hash and self.pegs == other.pegs
    
    def __repr__(self) -> str:
        return f"ZobristBitBoard({self._count} pegs, hash={self.zobrist_hash:016x})"


# =====================================================
# БЕНЧМАРК: сравнение обычного vs Zobrist хеширования
# =====================================================

def benchmark_hashing():
    """Сравнивает скорость обычного и Zobrist хеширования."""
    import time
    from .bitboard import BitBoard
    
    iterations = 100000
    
    # Обычный BitBoard
    board = BitBoard.english_start()
    start = time.time()
    for _ in range(iterations):
        h = hash(board.pegs)
    normal_time = time.time() - start
    
    # Zobrist
    zboard = ZobristBitBoard.english_start()
    moves = zboard.get_moves()
    
    start = time.time()
    for _ in range(iterations):
        # Симуляция хода и получения хеша
        if moves:
            new_board = zboard.apply_move(*moves[0])
            h = new_board.zobrist_hash
    zobrist_time = time.time() - start
    
    print(f"Normal hash: {normal_time:.3f}s ({iterations} iterations)")
    print(f"Zobrist hash: {zobrist_time:.3f}s ({iterations} iterations)")
    print(f"Speedup: {normal_time / zobrist_time:.2f}x")


if __name__ == "__main__":
    print("Zobrist Hashing Test")
    print("=" * 40)
    
    board = ZobristBitBoard.english_start()
    print(f"Start: {board}")
    print(f"Hash: {board.zobrist_hash:016x}")
    
    moves = board.get_moves()
    print(f"Moves available: {len(moves)}")
    
    if moves:
        move = moves[0]
        new_board = board.apply_move(*move)
        print(f"\nAfter move {move}:")
        print(f"Board: {new_board}")
        print(f"Hash: {new_board.zobrist_hash:016x}")
        
        # Проверка: хеш должен измениться
        print(f"\nHash changed: {board.zobrist_hash != new_board.zobrist_hash}")
