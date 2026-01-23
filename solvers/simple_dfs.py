"""
solvers/simple_dfs.py

Простой DFS решатель без оптимизаций - минимальный рабочий прототип.
Используется для Фазы 1 разработки.
"""

from typing import List, Tuple, Optional

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard
from core.optimized_bitboard import (
    optimized_get_moves, optimized_apply_move, optimized_peg_count
)


class SimpleDFSSolver(BaseSolver):
    """
    Простой DFS решатель без оптимизаций.
    
    Особенности:
    - Базовый рекурсивный поиск
    - Без мемоизации
    - Без эвристик
    - Без симметрий
    - Только для проверки работоспособности
    """
    
    def __init__(self, verbose: bool = False):
        super().__init__(use_symmetry=False, verbose=verbose)
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку простым DFS.
        
        Args:
            board: начальная позиция
            
        Returns:
            Список ходов (from, jumped, to) или None если решение не найдено
        """
        self.stats = SolverStats()
        
        self._log(f"Starting Simple DFS (pegs={board.peg_count()})")
        result = self._dfs(board, [])
        
        if result:
            self.stats.solution_length = len(result)
            self._log(f"Solution found: {len(result)} moves")
        else:
            self._log("No solution found")
        
        self._log(f"Stats: {self.stats}")
        return result
    
    def _dfs(self, board: BitBoard, path: List[Tuple[int, int, int]]) -> Optional[List[Tuple[int, int, int]]]:
        """
        Рекурсивный DFS поиск.
        
        Args:
            board: текущее состояние доски
            path: путь ходов до текущего состояния
            
        Returns:
            Список ходов или None
        """
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Проверка победы: остался один колышек (используем оптимизированную версию)
        if optimized_peg_count(board) == 1:
            return path
        
        # Получаем все возможные ходы (используем оптимизированную версию)
        moves = optimized_get_moves(board)
        
        # Если нет ходов - тупик
        if not moves:
            return None
        
        # Пробуем каждый ход (используем оптимизированную версию)
        for move in moves:
            new_board = optimized_apply_move(board, *move)
            result = self._dfs(new_board, path + [move])
            if result is not None:
                return result
        
        # Решение не найдено
        return None
