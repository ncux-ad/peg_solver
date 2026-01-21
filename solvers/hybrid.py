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
        
        self._log(f"Starting Hybrid Solver (pegs={board.peg_count()}, timeout={self.timeout}s)")
        
        # Мягкая проверка Pagoda (только для английской доски)
        if is_english_board(board):
            min_pagoda = min(PAGODA_WEIGHTS.values())
            current_pagoda = pagoda_value(board)
            
            # Более мягкая проверка - не блокируем сразу
            if current_pagoda < min_pagoda:
                self._log(f"Warning: Low Pagoda value ({current_pagoda} < {min_pagoda}), but continuing...")
        
        strategies = [
            ("Beam Search", lambda: BeamSolver(beam_width=200, verbose=False).solve(board)),
            ("DFS + Memo", lambda: DFSSolver(verbose=False).solve(board)),
            ("A* Aggressive", lambda: AStarSolver(aggressive=True, verbose=False).solve(board)),
            ("IDA*", lambda: IDAStarSolver(verbose=False).solve(board)),
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
                    self.stats.time_elapsed = time.time() - start_time
                    self.stats.solution_length = len(result)
                    self._log(f"✓ Found with {name}! ({len(result)} moves, {self.stats.time_elapsed:.2f}s)")
                    return result
            except Exception as e:
                self._log(f"✗ {name} failed: {e}")
        
        self.stats.time_elapsed = time.time() - start_time
        self._log(f"No solution found ({self.stats.time_elapsed:.2f}s)")
        return None
