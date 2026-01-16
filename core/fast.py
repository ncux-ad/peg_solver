"""
core/fast.py

Автоматический выбор быстрой реализации.

Если Cython скомпилирован — использует его.
Иначе — fallback на чистый Python.
"""

try:
    # Пробуем импортировать Cython версию
    from .fast_bitboard import (
        fast_peg_count,
        fast_has_peg,
        fast_apply_move,
        fast_get_moves,
        fast_is_dead,
        fast_zobrist_hash,
        fast_update_zobrist,
        FastBitBoard
    )
    USING_CYTHON = True
except ImportError:
    # Fallback на чистый Python
    from .fast_bitboard_py import (
        fast_peg_count,
        fast_has_peg,
        fast_apply_move,
        fast_get_moves,
        fast_is_dead,
        fast_zobrist_hash,
        fast_update_zobrist,
        FastBitBoard
    )
    USING_CYTHON = False


def get_implementation_info() -> str:
    """Возвращает информацию о текущей реализации."""
    if USING_CYTHON:
        return "Cython (compiled, 50-100x faster)"
    else:
        return "Pure Python (fallback)"


__all__ = [
    'fast_peg_count',
    'fast_has_peg',
    'fast_apply_move',
    'fast_get_moves',
    'fast_is_dead',
    'fast_zobrist_hash',
    'fast_update_zobrist',
    'FastBitBoard',
    'USING_CYTHON',
    'get_implementation_info'
]
