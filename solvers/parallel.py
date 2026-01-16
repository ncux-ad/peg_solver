"""
solvers/parallel.py

Parallel DFS — многопоточный поиск.
"""

from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard


def _solve_subtree(args: Tuple[int, Tuple[int, int, int]]) -> Optional[List]:
    """Решает поддерево (для параллельного запуска)."""
    board_pegs, first_move = args
    board = BitBoard(board_pegs)
    new_board = board.apply_move(*first_move)
    
    # Импортируем здесь для избежания проблем с pickle
    from solvers.dfs import DFSSolver
    
    solver = DFSSolver(use_symmetry=True, verbose=False)
    result = solver.solve(new_board)
    
    if result is not None:
        return [first_move] + result
    return None


class ParallelSolver(BaseSolver):
    """
    Параллельный DFS решатель.
    
    Распределяет первые ходы между процессами.
    """
    
    def __init__(self, num_workers: int = None, use_symmetry: bool = True,
                 verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.num_workers = num_workers or multiprocessing.cpu_count()
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        
        moves = board.get_moves()
        if not moves:
            return None
        
        self._log(f"Starting Parallel DFS (workers={self.num_workers}, moves={len(moves)})")
        
        # Подготавливаем задачи
        tasks = [(board.pegs, move) for move in moves]
        
        try:
            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                futures = {executor.submit(_solve_subtree, task): task for task in tasks}
                
                for future in as_completed(futures):
                    self.stats.nodes_visited += 1
                    result = future.result()
                    
                    if result is not None:
                        self.stats.solution_length = len(result)
                        self._log(f"Found! {self.stats}")
                        
                        # Отменяем остальные
                        for f in futures:
                            f.cancel()
                        return result
        except Exception as e:
            self._log(f"Error: {e}")
            return None
        
        self._log(f"No solution. {self.stats}")
        return None
