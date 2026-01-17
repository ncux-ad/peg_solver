"""
solvers/optimized_utils.py

Оптимизированные утилиты для решателей.
Автоматически использует Rust/Numba/Cython версии, если доступны.
"""

from typing import TYPE_CHECKING
from core.bitboard import BitBoard, ENGLISH_VALID_POSITIONS, CENTER_POS

if TYPE_CHECKING:
    pass

# Попытка импортировать оптимизированные версии
try:
    from core.rust_fast import rust_evaluate_position, USING_RUST as RUST_AVAILABLE
except ImportError:
    RUST_AVAILABLE = False
    rust_evaluate_position = None

try:
    from heuristics.fast_pagoda import evaluate_position_fast, NUMBA_AVAILABLE
except ImportError:
    NUMBA_AVAILABLE = False
    evaluate_position_fast = None


def evaluate_position_optimized(board: BitBoard, num_moves: int = None) -> float:
    """
    Оптимизированная оценка позиции.
    
    Автоматически выбирает лучшую доступную реализацию:
    1. Rust (если доступен) - самое быстрое
    2. Numba JIT (если доступен) - быстрое
    3. Python (fallback) - медленное, но работает
    
    Args:
        board: доска для оценки
        num_moves: количество доступных ходов (опционально, вычисляется если None)
    
    Returns:
        оценка позиции (меньше = лучше)
    """
    if num_moves is None:
        num_moves = len(board.get_moves())
    
    # Попытка использовать Rust версию
    if RUST_AVAILABLE and rust_evaluate_position:
        try:
            return rust_evaluate_position(board.pegs, num_moves)
        except Exception:
            pass  # Fallback на другие версии
    
    # Попытка использовать Numba версию
    if NUMBA_AVAILABLE and evaluate_position_fast:
        try:
            return evaluate_position_fast(board.pegs, num_moves)
        except Exception:
            pass  # Fallback на Python
    
    # Fallback на Python версию
    return _evaluate_position_python(board, num_moves)


def _evaluate_position_python(board: BitBoard, num_moves: int) -> float:
    """Python версия оценки позиции (fallback)."""
    score = board.peg_count() * 10
    
    # Расстояние до центра
    for pos in ENGLISH_VALID_POSITIONS:
        if board.has_peg(pos):
            r, c = pos // 7, pos % 7
            score += abs(r - 3) + abs(c - 3)
    
    # Мобильность
    score -= num_moves * 2
    
    # Изолированные колышки
    score += _count_isolated_python(board) * 15
    
    # Pagoda проверка
    from heuristics.pagoda import pagoda_value, PAGODA_WEIGHTS
    
    min_pagoda = min(PAGODA_WEIGHTS.values())
    current_pagoda = pagoda_value(board)
    target_pagoda = PAGODA_WEIGHTS[CENTER_POS]
    
    if board.peg_count() > 15:
        if current_pagoda < target_pagoda:
            score += 1000
    else:
        if current_pagoda < min_pagoda:
            score += 1000
    
    return score


def _count_isolated_python(board: BitBoard) -> int:
    """Подсчёт изолированных колышков (Python версия, оптимизированная)."""
    count = 0
    pegs = board.pegs
    
    for pos in ENGLISH_VALID_POSITIONS:
        if not (pegs & (1 << pos)):
            continue
        
        r, c = pos // 7, pos % 7
        # Проверяем соседей битовыми операциями
        has_neighbor = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            neighbor_pos = nr * 7 + nc
            if neighbor_pos in ENGLISH_VALID_POSITIONS and (pegs & (1 << neighbor_pos)):
                has_neighbor = True
                break
        
        if not has_neighbor:
            count += 1
    
    return count


def get_optimization_info() -> str:
    """Возвращает информацию о доступных оптимизациях."""
    parts = []
    if RUST_AVAILABLE:
        parts.append("Rust")
    if NUMBA_AVAILABLE:
        parts.append("Numba")
    if not parts:
        return "Python only (fallback)"
    return " + ".join(parts)
