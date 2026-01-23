"""
core/optimized_bitboard.py

Оптимизированные обёртки для BitBoard операций.
Автоматически использует Rust/Cython версии, если доступны.
"""

from typing import List, Tuple, Optional
from core.bitboard import BitBoard

# Попытка импортировать Rust версии
try:
    from core.rust_fast import (
        rust_peg_count,
        rust_has_peg,
        rust_apply_move,
        rust_get_moves,
        rust_is_dead,
        USING_RUST as RUST_AVAILABLE
    )
except ImportError:
    RUST_AVAILABLE = False
    rust_peg_count = None
    rust_has_peg = None
    rust_apply_move = None
    rust_get_moves = None
    rust_is_dead = None

# Попытка импортировать Cython версии
try:
    from core.fast import (
        fast_peg_count,
        fast_has_peg,
        fast_apply_move,
        fast_get_moves,
        fast_is_dead,
        USING_CYTHON
    )
except ImportError:
    USING_CYTHON = False
    fast_peg_count = None
    fast_has_peg = None
    fast_apply_move = None
    fast_get_moves = None
    fast_is_dead = None


def optimized_peg_count(board: BitBoard) -> int:
    """
    Оптимизированный подсчёт колышков.
    
    Автоматически выбирает лучшую доступную реализацию:
    1. Rust (если доступен) - самое быстрое
    2. Cython (если доступен) - быстрое
    3. Python (fallback) - медленное, но работает
    """
    if RUST_AVAILABLE and rust_peg_count:
        try:
            return rust_peg_count(board.pegs)
        except Exception:
            pass
    
    if USING_CYTHON and fast_peg_count:
        try:
            return fast_peg_count(board.pegs)
        except Exception:
            pass
    
    # Fallback на Python
    return board.peg_count()


def optimized_get_moves(board: BitBoard) -> List[Tuple[int, int, int]]:
    """
    Оптимизированная генерация ходов.
    
    Автоматически выбирает лучшую доступную реализацию.
    """
    if RUST_AVAILABLE and rust_get_moves:
        try:
            return rust_get_moves(board.pegs, board.valid_mask)
        except Exception:
            pass
    
    if USING_CYTHON and fast_get_moves:
        try:
            return fast_get_moves(board.pegs, board.valid_mask)
        except Exception:
            pass
    
    # Fallback на Python
    return board.get_moves()


def optimized_apply_move(board: BitBoard, from_pos: int, jumped_pos: int, to_pos: int) -> BitBoard:
    """
    Оптимизированное применение хода.
    
    Автоматически выбирает лучшую доступную реализацию.
    """
    if RUST_AVAILABLE and rust_apply_move:
        try:
            new_pegs = rust_apply_move(board.pegs, from_pos, jumped_pos, to_pos)
            return BitBoard(new_pegs, valid_mask=board.valid_mask)
        except Exception:
            pass
    
    if USING_CYTHON and fast_apply_move:
        try:
            new_pegs = fast_apply_move(board.pegs, from_pos, jumped_pos, to_pos)
            return BitBoard(new_pegs, valid_mask=board.valid_mask)
        except Exception:
            pass
    
    # Fallback на Python
    return board.apply_move(from_pos, jumped_pos, to_pos)


def optimized_is_dead(board: BitBoard) -> bool:
    """
    Оптимизированная проверка тупика.
    
    Автоматически выбирает лучшую доступную реализацию.
    """
    if RUST_AVAILABLE and rust_is_dead:
        try:
            return rust_is_dead(board.pegs, board.valid_mask)
        except Exception:
            pass
    
    if USING_CYTHON and fast_is_dead:
        try:
            return fast_is_dead(board.pegs, board.valid_mask)
        except Exception:
            pass
    
    # Fallback на Python
    return board.is_dead()


def optimized_has_peg(board: BitBoard, pos: int) -> bool:
    """
    Оптимизированная проверка наличия колышка.
    
    Автоматически выбирает лучшую доступную реализацию.
    """
    if RUST_AVAILABLE and rust_has_peg:
        try:
            return rust_has_peg(board.pegs, pos)
        except Exception:
            pass
    
    if USING_CYTHON and fast_has_peg:
        try:
            return fast_has_peg(board.pegs, pos)
        except Exception:
            pass
    
    # Fallback на Python
    return board.has_peg(pos)


def get_optimization_info() -> str:
    """Возвращает информацию о доступных оптимизациях для BitBoard операций."""
    parts = []
    if RUST_AVAILABLE:
        parts.append("Rust")
    if USING_CYTHON:
        parts.append("Cython")
    if not parts:
        return "Python only (fallback)"
    return " + ".join(parts)


__all__ = [
    'optimized_peg_count',
    'optimized_get_moves',
    'optimized_apply_move',
    'optimized_is_dead',
    'optimized_has_peg',
    'get_optimization_info',
    'RUST_AVAILABLE',
    'USING_CYTHON'
]
