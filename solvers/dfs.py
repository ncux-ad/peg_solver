"""
solvers/dfs.py

DFS (Depth-First Search) с мемоизацией.
Dynamic Programming подход.
"""

from typing import List, Tuple, Optional, Set

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, CENTER_POS
from heuristics import pagoda_value, PAGODA_WEIGHTS


class DFSSolver(BaseSolver):
    """
    DFS решатель с мемоизацией неудачных состояний.
    
    Особенности:
    - Запоминает состояния без решения (Dynamic Programming)
    - Сортирует ходы по эвристике
    - Использует Pagoda pruning
    - Учитывает симметрии
    """
    
    def __init__(self, use_symmetry: bool = True, sort_moves: bool = True,
                 use_pagoda: bool = True, verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.sort_moves = sort_moves
        self.use_pagoda = use_pagoda
        self.memo: Set[int] = set()
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """Запускает DFS с мемоизацией."""
        self.stats = SolverStats()
        self.memo.clear()
        
        self._log(f"Starting DFS (pegs={board.peg_count()})")
        result = self._dfs(board, [])
        
        self._log(f"Done: {self.stats}")
        return result
    
    def _dfs(self, board: BitBoard, path: List) -> Optional[List]:
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Победа
        if board.peg_count() == 1:
            self.stats.solution_length = len(path)
            return path
        
        # Проверяем мемо
        key = self._get_key(board)
        if key in self.memo:
            self.stats.nodes_pruned += 1
            return None
        
        # Pagoda pruning
        if self.use_pagoda:
            if pagoda_value(board) < PAGODA_WEIGHTS[CENTER_POS]:
                self.memo.add(key)
                self.stats.nodes_pruned += 1
                return None
        
        # Получаем ходы
        moves = board.get_moves()
        if not moves:
            self.memo.add(key)
            return None
        
        # Сортируем по эвристике
        if self.sort_moves:
            moves = self._sort_moves(board, moves)
        
        # Рекурсивный поиск
        for move in moves:
            new_board = board.apply_move(*move)
            result = self._dfs(new_board, path + [move])
            if result is not None:
                return result
        
        # Запоминаем неудачу
        self.memo.add(key)
        return None
    
    def _sort_moves(self, board: BitBoard, moves: List) -> List:
        """Сортирует ходы: ближе к центру = лучше."""
        def priority(move):
            _, jumped, to_pos = move
            to_r, to_c = to_pos // 7, to_pos % 7
            center_dist = abs(to_r - 3) + abs(to_c - 3)
            pagoda_bonus = -PAGODA_WEIGHTS.get(jumped, 0) * 0.1
            return center_dist + pagoda_bonus
        
        return sorted(moves, key=priority)
