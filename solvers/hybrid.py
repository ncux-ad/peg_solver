"""
solvers/hybrid.py

Гибридный решатель — комбинирует несколько стратегий.
"""

from typing import List, Tuple, Optional
import time

from .base import BaseSolver, SolverStats
from .dfs import DFSSolver
from .astar import AStarSolver, IDAStarSolver
from .beam import BeamSolver
from core.bitboard import (
    BitBoard, CENTER_POS,
    is_english_board
)
from heuristics import pagoda_value, PAGODA_WEIGHTS


class HybridSolver(BaseSolver):
    """
    Гибридный решатель.
    
    Пробует несколько стратегий по очереди:
    1. Beam Search (быстрый, но неполный)
    2. DFS с мемоизацией
    3. A* агрессивный
    4. IDA* (если много памяти)
    """
    
    def __init__(self, timeout: float = 60.0, verbose: bool = True):
        super().__init__(use_symmetry=True, verbose=verbose)
        self.timeout = timeout
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        start_time = time.time()
        
        peg_count = board.peg_count()
        self._log(f"Starting Hybrid Solver (pegs={peg_count}, timeout={self.timeout}s)")
        
        # Мягкая проверка Pagoda (только для английской доски)
        if is_english_board(board):
            min_pagoda = min(PAGODA_WEIGHTS.values())
            current_pagoda = pagoda_value(board)
            
            # Более мягкая проверка - не блокируем сразу
            if current_pagoda < min_pagoda:
                self._log(f"Warning: Low Pagoda value ({current_pagoda} < {min_pagoda}), but continuing...")
        
        # Новая стратегия: Beam для небольших досок, DFS для остальных
        # Beam показал лучшие результаты для небольших досок, DFS для остальных
        if peg_count < 10:
            # Небольшие доски: Beam Search (быстрый)
            strategies = [
                ("Beam Search", lambda: BeamSolver(beam_width=500, max_depth=50, verbose=False).solve(board)),
                ("DFS", lambda: DFSSolver(verbose=False, use_pagoda=False).solve(board)),
            ]
        else:
            # Большие доски: DFS (надёжный)
            strategies = [
                ("DFS", lambda: DFSSolver(verbose=False, use_pagoda=False).solve(board)),
                ("Beam Search", lambda: BeamSolver(beam_width=500, max_depth=50, verbose=False).solve(board)),
            ]
        
        for name, solver_fn in strategies:
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                self._log(f"Timeout ({self.timeout}s)")
                return None
            
            self._log(f"Trying {name}...")
            
            try:
                result = solver_fn()
                if result is not None:
                    # ВАЛИДАЦИЯ: проверяем, что решение корректное
                    if self._validate_solution(board, result):
                        self.stats.time_elapsed = time.time() - start_time
                        self.stats.solution_length = len(result)
                        self._log(f"✓ Found valid solution with {name}! ({len(result)} moves, {self.stats.time_elapsed:.2f}s)")
                        return result
                    else:
                        self._log(f"✗ {name} вернул невалидное решение, продолжаем...")
            except Exception as e:
                self._log(f"✗ {name} failed: {e}")
        
        self.stats.time_elapsed = time.time() - start_time
        self._log(f"No solution found ({self.stats.time_elapsed:.2f}s)")
        return None
    
    def _validate_solution(self, initial_board: BitBoard, solution: List[Tuple[int, int, int]]) -> bool:
        """Проверяет, что решение валидное (приводит к победному состоянию - 1 колышек)."""
        try:
            current_board = initial_board
            for move in solution:
                current_board = current_board.apply_move(*move)
            
            # Проверяем, что остался ровно 1 колышек (победное состояние)
            return current_board.peg_count() == 1
        except Exception as e:
            self._log(f"Ошибка валидации решения: {e}")
            return False