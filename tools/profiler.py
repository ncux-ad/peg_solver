"""
tools/profiler.py

Инструменты профилирования для анализа производительности - Фаза 6.4.
"""

import time
import cProfile
import pstats
import io
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from functools import wraps

from core.bitboard import BitBoard
from solvers.base import BaseSolver


class PerformanceProfiler:
    """Профилировщик производительности решателей."""
    
    def __init__(self):
        self.profiles: Dict[str, cProfile.Profile] = {}
        self.stats: Dict[str, Dict[str, Any]] = {}
    
    @contextmanager
    def profile(self, name: str):
        """
        Контекстный менеджер для профилирования.
        
        Usage:
            with profiler.profile('my_function'):
                # код для профилирования
        """
        profiler = cProfile.Profile()
        profiler.enable()
        start_time = time.time()
        
        try:
            yield
        finally:
            profiler.disable()
            elapsed = time.time() - start_time
            
            self.profiles[name] = profiler
            self.stats[name] = {
                'elapsed_time': elapsed,
                'profile': profiler
            }
    
    def get_stats(self, name: str, sort_by: str = 'cumulative', 
                  limit: int = 20) -> str:
        """
        Возвращает статистику профилирования в виде строки.
        
        Args:
            name: имя профиля
            sort_by: сортировка ('cumulative', 'time', 'calls')
            limit: количество строк
            
        Returns:
            Строка со статистикой
        """
        if name not in self.profiles:
            return f"No profile found for '{name}'"
        
        profiler = self.profiles[name]
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats(sort_by)
        stats.print_stats(limit)
        
        return stream.getvalue()
    
    def compare_solvers(self, board: BitBoard, 
                       solvers: List[BaseSolver]) -> Dict[str, Dict[str, Any]]:
        """
        Сравнивает производительность нескольких решателей.
        
        Args:
            board: тестовая позиция
            solvers: список решателей для сравнения
            
        Returns:
            Словарь с результатами сравнения
        """
        results = {}
        
        for solver in solvers:
            solver_name = solver.__class__.__name__
            
            with self.profile(solver_name):
                start = time.time()
                solution = solver.solve(board)
                elapsed = time.time() - start
            
            results[solver_name] = {
                'solution_found': solution is not None,
                'solution_length': len(solution) if solution else 0,
                'time_elapsed': elapsed,
                'nodes_visited': solver.stats.nodes_visited,
                'nodes_pruned': solver.stats.nodes_pruned,
                'max_depth': solver.stats.max_depth
            }
        
        return results
    
    def print_comparison(self, board: BitBoard, solvers: List[BaseSolver]):
        """Выводит сравнение решателей в консоль."""
        results = self.compare_solvers(board, solvers)
        
        print("\n" + "=" * 80)
        print("Сравнение производительности решателей")
        print("=" * 80)
        print(f"{'Решатель':<30} {'Время':<12} {'Узлов':<12} {'Глубина':<10} {'Решение':<10}")
        print("-" * 80)
        
        for name, stats in results.items():
            solution_status = "✅" if stats['solution_found'] else "❌"
            print(f"{name:<30} {stats['time_elapsed']:>10.3f}s "
                  f"{stats['nodes_visited']:>12} {stats['max_depth']:>10} "
                  f"{solution_status:>10}")
        
        print("=" * 80)


def profile_solver(solver_name: str = None):
    """
    Декоратор для профилирования функций решателей.
    
    Usage:
        @profile_solver('my_solver')
        def solve(self, board):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = solver_name or f"{func.__module__}.{func.__name__}"
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                
                # Сохраняем профиль
                stats = pstats.Stats(profiler)
                stats.sort_stats('cumulative')
                stats.print_stats(10)  # Топ-10 функций
            
            return result
        return wrapper
    return decorator


def benchmark_solver(solver: BaseSolver, board: BitBoard, 
                    iterations: int = 1) -> Dict[str, Any]:
    """
    Бенчмарк решателя на заданной позиции.
    
    Args:
        solver: решатель для тестирования
        board: тестовая позиция
        iterations: количество итераций
        
    Returns:
        Словарь с результатами бенчмарка
    """
    times = []
    solutions = []
    
    for _ in range(iterations):
        start = time.time()
        solution = solver.solve(board)
        elapsed = time.time() - start
        
        times.append(elapsed)
        solutions.append(solution)
    
    return {
        'solver': solver.__class__.__name__,
        'iterations': iterations,
        'avg_time': sum(times) / len(times),
        'min_time': min(times),
        'max_time': max(times),
        'solutions_found': sum(1 for s in solutions if s is not None),
        'avg_solution_length': sum(len(s) for s in solutions if s) / max(1, sum(1 for s in solutions if s)),
        'stats': solver.stats.__dict__ if hasattr(solver, 'stats') else {}
    }
