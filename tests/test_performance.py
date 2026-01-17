"""
tests/test_performance.py

Тесты производительности для сравнения различных реализаций.
"""

import time
import statistics
import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bitboard import BitBoard
from heuristics import pagoda_value
from heuristics.evaluation import evaluate_position
from heuristics.fast_pagoda import pagoda_value_fast, NUMBA_AVAILABLE
from core.fast import USING_CYTHON
from core.rust_fast import USING_RUST, rust_pagoda_value, rust_evaluate_position


def benchmark_function(func, args, iterations=100000, warmup=1000):
    """Тестирует производительность функции."""
    # Прогреваем
    for _ in range(warmup):
        func(*args)
    
    # Замеряем время
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # в миллисекундах
    
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    ops_per_sec = 1000 / avg_time if avg_time > 0 else 0
    
    return {
        'avg_ms': avg_time,
        'min_ms': min_time,
        'max_ms': max_time,
        'ops_per_sec': ops_per_sec,
        'result': result
    }


def test_pagoda_performance():
    """Сравнение производительности pagoda_value."""
    print("\n" + "="*60)
    print("📊 Тест производительности: pagoda_value")
    print("="*60)
    
    board = BitBoard.english_start()
    iterations = 100000
    
    results = {}
    
    # Python версия (оригинальная)
    try:
        from heuristics.pagoda import pagoda_value as pagoda_py
        # Временно отключаем оптимизацию для чистого теста
        import heuristics.pagoda
        original_pagoda = heuristics.pagoda.pagoda_value
        def pagoda_py_original(board):
            total = 0
            from heuristics.pagoda import PAGODA_WEIGHTS
            for pos, weight in PAGODA_WEIGHTS.items():
                if board.has_peg(pos):
                    total += weight
            return total
        
        result = benchmark_function(pagoda_py_original, (board,), iterations)
        results['Python (original)'] = result
        print(f"  Python (original): {result['ops_per_sec']:,.0f} ops/s")
    except Exception as e:
        print(f"  Python (original): Error - {e}")
    
    # Numba версия
    if NUMBA_AVAILABLE:
        try:
            result = benchmark_function(pagoda_value_fast, (board.pegs,), iterations)
            results['Numba JIT'] = result
            print(f"  Numba JIT:        {result['ops_per_sec']:,.0f} ops/s")
        except Exception as e:
            print(f"  Numba JIT:        Error - {e}")
    
    # Rust версия
    if USING_RUST:
        try:
            result = benchmark_function(rust_pagoda_value, (board.pegs,), iterations)
            results['Rust'] = result
            print(f"  Rust:             {result['ops_per_sec']:,.0f} ops/s")
        except Exception as e:
            print(f"  Rust:             Error - {e}")
    
    # Автоматическая версия (с fallback)
    try:
        result = benchmark_function(pagoda_value, (board,), iterations)
        results['Auto (fallback)'] = result
        print(f"  Auto (fallback):  {result['ops_per_sec']:,.0f} ops/s")
    except Exception as e:
        print(f"  Auto (fallback):  Error - {e}")
    
    # Сравнение
    if len(results) > 1:
        baseline = results.get('Python (original)', {}).get('ops_per_sec', 1)
        print("\n  Ускорение относительно Python:")
        for name, result in results.items():
            if name != 'Python (original)':
                speedup = result['ops_per_sec'] / baseline if baseline > 0 else 0
                print(f"    {name:20s}: {speedup:.2f}x")


def test_evaluate_performance():
    """Сравнение производительности evaluate_position."""
    print("\n" + "="*60)
    print("📊 Тест производительности: evaluate_position")
    print("="*60)
    
    board = BitBoard.english_start()
    num_moves = len(board.get_moves())
    iterations = 50000
    
    results = {}
    
    # Python версия (оригинальная)
    def evaluate_py_original(board, num_moves):
        from core.bitboard import ENGLISH_VALID_POSITIONS, CENTER_POS
        from heuristics.pagoda import PAGODA_WEIGHTS, pagoda_value
        
        score = board.peg_count() * 10.0
        center_row, center_col = 3, 3
        
        for pos in ENGLISH_VALID_POSITIONS:
            if board.has_peg(pos):
                r, c = pos // 7, pos % 7
                score += abs(r - center_row) + abs(c - center_col)
        
        score -= num_moves * 2.0
        
        current_pagoda = pagoda_value(board)
        target_pagoda = PAGODA_WEIGHTS.get(CENTER_POS, 0)
        
        if board.peg_count() > 15:
            if current_pagoda < target_pagoda:
                score += 1000.0
        
        return score
    
    try:
        result = benchmark_function(evaluate_py_original, (board, num_moves), iterations)
        results['Python (original)'] = result
        print(f"  Python (original): {result['ops_per_sec']:,.0f} ops/s")
    except Exception as e:
        print(f"  Python (original): Error - {e}")
    
    # Numba версия
    if NUMBA_AVAILABLE:
        try:
            from heuristics.fast_pagoda import evaluate_position_fast
            result = benchmark_function(evaluate_position_fast, (board.pegs, num_moves), iterations)
            results['Numba JIT'] = result
            print(f"  Numba JIT:        {result['ops_per_sec']:,.0f} ops/s")
        except Exception as e:
            print(f"  Numba JIT:        Error - {e}")
    
    # Rust версия
    if USING_RUST:
        try:
            result = benchmark_function(rust_evaluate_position, (board.pegs, num_moves), iterations)
            results['Rust'] = result
            print(f"  Rust:             {result['ops_per_sec']:,.0f} ops/s")
        except Exception as e:
            print(f"  Rust:             Error - {e}")
    
    # Автоматическая версия (с fallback)
    try:
        result = benchmark_function(evaluate_position, (board, num_moves), iterations)
        results['Auto (fallback)'] = result
        print(f"  Auto (fallback):  {result['ops_per_sec']:,.0f} ops/s")
    except Exception as e:
        print(f"  Auto (fallback):  Error - {e}")
    
    # Сравнение
    if len(results) > 1:
        baseline = results.get('Python (original)', {}).get('ops_per_sec', 1)
        print("\n  Ускорение относительно Python:")
        for name, result in results.items():
            if name != 'Python (original)':
                speedup = result['ops_per_sec'] / baseline if baseline > 0 else 0
                print(f"    {name:20s}: {speedup:.2f}x")


def test_implementation_info():
    """Показывает информацию о доступных реализациях."""
    print("\n" + "="*60)
    print("📋 Информация о реализациях")
    print("="*60)
    
    print(f"  Cython:  {'✅' if USING_CYTHON else '❌'}")
    print(f"  Numba:   {'✅' if NUMBA_AVAILABLE else '❌'}")
    print(f"  Rust:    {'✅' if USING_RUST else '❌'}")
    
    if USING_RUST:
        from core.rust_fast import get_implementation_info
        print(f"\n  Текущая реализация: {get_implementation_info()}")


if __name__ == '__main__':
    print("\n🚀 Запуск тестов производительности Peg Solitaire Solver")
    
    test_implementation_info()
    test_pagoda_performance()
    test_evaluate_performance()
    
    print("\n" + "="*60)
    print("✅ Тесты завершены")
    print("="*60 + "\n")
