"""
solvers/zobrist_dfs.py

DFS решатель с Zobrist хешированием.
Максимальная эффективность для backtracking поиска.
"""

from typing import List, Tuple, Optional, Set

from .base import BaseSolver, SolverStats
from core.zobrist import ZobristBitBoard
from core.bitboard import CENTER_POS
from heuristics.pagoda import pagoda_value, PAGODA_WEIGHTS


class ZobristDFSSolver(BaseSolver):
    """
    DFS с Zobrist хешированием.
    
    Преимущества над обычным DFS:
    - O(1) обновление хеша при ходе
    - Быстрое сравнение в visited set
    - Идеально для глубокого backtracking
    """
    
    def __init__(self, use_symmetry: bool = False, sort_moves: bool = True,
                 use_pagoda: bool = True, verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.sort_moves = sort_moves
        self.use_pagoda = use_pagoda
        self.visited: Set[int] = set()
    
    def solve(self, board) -> Optional[List[Tuple[int, int, int]]]:
        """Запускает DFS с Zobrist хешированием."""
        # Конвертируем в ZobristBitBoard если нужно
        if not isinstance(board, ZobristBitBoard):
            from core.bitboard import BitBoard
            if isinstance(board, BitBoard):
                zboard = ZobristBitBoard(board.pegs)
            else:
                raise TypeError("Expected BitBoard or ZobristBitBoard")
        else:
            zboard = board
        
        self.stats = SolverStats()
        self.visited.clear()
        
        self._log(f"Starting Zobrist DFS (pegs={zboard.peg_count()})")
        
        result = self._dfs(zboard, [])
        
        self._log(f"Done: {self.stats}")
        return result
    
    def _dfs(self, board: ZobristBitBoard, path: List) -> Optional[List]:
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Победа
        if board.peg_count() == 1:
            self.stats.solution_length = len(path)
            return path
        
        # Zobrist хеш — уже вычислен, просто берём
        h = board.zobrist_hash
        if h in self.visited:
            self.stats.nodes_pruned += 1
            return None
        self.visited.add(h)
        
        # Pagoda pruning (используем pegs напрямую)
        if self.use_pagoda:
            from core.bitboard import BitBoard
            temp_board = BitBoard(board.pegs)
            if pagoda_value(temp_board) < PAGODA_WEIGHTS[CENTER_POS]:
                self.stats.nodes_pruned += 1
                return None
        
        # Получаем ходы
        moves = board.get_moves()
        if not moves:
            return None
        
        # Сортируем по эвристике
        if self.sort_moves:
            moves = self._sort_moves(moves)
        
        # Рекурсивный поиск
        for move in moves:
            # apply_move возвращает новый ZobristBitBoard с уже вычисленным хешом!
            new_board = board.apply_move(*move)
            result = self._dfs(new_board, path + [move])
            if result is not None:
                return result
        
        return None
    
    def _sort_moves(self, moves: List) -> List:
        """Сортирует ходы: ближе к центру = лучше."""
        def priority(move):
            _, jumped, to_pos = move
            to_r, to_c = to_pos // 7, to_pos % 7
            return abs(to_r - 3) + abs(to_c - 3)
        
        return sorted(moves, key=priority)
