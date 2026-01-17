"""
core/rust_fast.py

Автоматический выбор Rust реализации критических операций.
Если Rust модуль скомпилирован — использует его.
Иначе — fallback на Cython/Python.
"""

try:
    # Пробуем импортировать Rust версию
    from rust_peg_solver import (
        rust_peg_count,
        rust_has_peg,
        rust_apply_move,
        rust_get_moves,
        rust_is_dead,
        rust_pagoda_value,
        rust_evaluate_position,
        rust_evaluate_batch
    )
    USING_RUST = True
except ImportError:
    # Fallback на Cython/Python
    from .fast import (
        fast_peg_count as rust_peg_count,
        fast_has_peg as rust_has_peg,
        fast_apply_move as rust_apply_move,
        fast_get_moves as rust_get_moves,
        fast_is_dead as rust_is_dead,
    )
    from heuristics.fast_pagoda import pagoda_value_fast as rust_pagoda_value
    USING_RUST = False
    
    # Заглушки для функций, которых нет в Cython
    def rust_evaluate_position(pegs: int, num_moves: int) -> float:
        from heuristics.fast_pagoda import evaluate_position_fast
        return evaluate_position_fast(pegs, num_moves)
    
    def rust_evaluate_batch(pegs_list, moves_list):
        return [rust_evaluate_position(p, m) for p, m in zip(pegs_list, moves_list)]


def get_implementation_info() -> str:
    """Возвращает информацию о текущей реализации."""
    if USING_RUST:
        return "Rust (compiled, fastest - 2-10x faster than Cython)"
    else:
        from .fast import USING_CYTHON, get_implementation_info as get_cython_info
        if USING_CYTHON:
            return "Cython (compiled, 26x faster than Python)"
        else:
            return "Pure Python (fallback, slowest)"


__all__ = [
    'rust_peg_count',
    'rust_has_peg',
    'rust_apply_move',
    'rust_get_moves',
    'rust_is_dead',
    'rust_pagoda_value',
    'rust_evaluate_position',
    'rust_evaluate_batch',
    'USING_RUST',
    'get_implementation_info'
]
