"""
heuristics/evaluation.py

Оптимизированные функции оценки позиций.
Автоматически использует Numba JIT или Rust если доступны.
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.bitboard import BitBoard

def evaluate_position(board: 'BitBoard', num_moves: int = None) -> float:
    """
    Быстрая оценка позиции (меньше = лучше).
    
    Автоматически использует оптимизированную версию (Numba/Rust) если доступна.
    
    Args:
        board: BitBoard для оценки
        num_moves: количество доступных ходов (если None, вычисляется автоматически)
    
    Returns:
        оценка позиции (меньше = лучше)
    """
    if num_moves is None:
        num_moves = len(board.get_moves())
    
    # Пробуем использовать Rust версию
    try:
        from core.rust_fast import rust_evaluate_position
        return rust_evaluate_position(board.pegs, num_moves)
    except (ImportError, AttributeError):
        pass
    
    # Пробуем использовать Numba версию
    try:
        from .fast_pagoda import evaluate_position_fast
        return evaluate_position_fast(board.pegs, num_moves)
    except ImportError:
        pass
    
    # Fallback на оригинальную версию
    from core.bitboard import ENGLISH_VALID_POSITIONS, CENTER_POS
    from .pagoda import PAGODA_WEIGHTS
    
    score = board.peg_count() * 10.0
    
    # Расстояние до центра
    center_row, center_col = 3, 3
    for pos in ENGLISH_VALID_POSITIONS:
        if board.has_peg(pos):
            r, c = pos // 7, pos % 7
            score += abs(r - center_row) + abs(c - center_col)
    
    # Мобильность
    score -= num_moves * 2.0
    
    # Pagoda проверка
    from .pagoda import pagoda_value
    current_pagoda = pagoda_value(board)
    target_pagoda = PAGODA_WEIGHTS.get(CENTER_POS, 0)
    
    if board.peg_count() > 15:
        if current_pagoda < target_pagoda:
            score += 1000.0
    
    return score
