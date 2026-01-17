"""
solvers/pattern_astar.py

A* решатель с Pattern Database эвристикой.
"""

from typing import List, Tuple, Optional, Dict
from heapq import heappush, heappop

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, CENTER_POS
from heuristics import pattern_heuristic, pagoda_value, PAGODA_WEIGHTS


class PatternAStarSolver(BaseSolver):
    """
    A* с Pattern Database эвристикой.
    
    Использует предвычисленные эвристики для регионов доски.
    Даёт более точную нижнюю границу → меньше раскрытых узлов.
    """
    
    def __init__(self, use_symmetry: bool = True, verbose: bool = False):
        super().__init__(use_symmetry, verbose)
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        
        self._log(f"Starting Pattern A* (pegs={board.peg_count()})")
        
        # Загружаем Pattern DB
        from heuristics import get_pattern_db
        db = get_pattern_db()
        
        # Pagoda check
        if pagoda_value(board) < PAGODA_WEIGHTS[CENTER_POS]:
            self._log("Position unsolvable (Pagoda)")
            return None
        
        counter = 0
        heap = []
        visited: Dict[int, Tuple[int, int, Tuple]] = {}
        
        start_key = self._get_key(board)
        h = self._heuristic(board.pegs, db)
        heappush(heap, (h, counter, 0, board))
        visited[start_key] = (0, None, None)
        
        while heap:
            f, _, steps, current = heappop(heap)
            self.stats.nodes_visited += 1
            self.stats.max_depth = max(self.stats.max_depth, steps)
            
            if current.peg_count() == 1:
                path = self._reconstruct_path(visited, current, start_key)
                self.stats.solution_length = len(path)
                self._log(f"Found! {self.stats}")
                return path
            
            if current.is_dead():
                self.stats.nodes_pruned += 1
                continue
            
            current_key = self._get_key(current)
            
            for move in current.get_moves():
                new_board = current.apply_move(*move)
                new_key = self._get_key(new_board)
                new_steps = steps + 1
                
                if new_key in visited and visited[new_key][0] <= new_steps:
                    continue
                
                visited[new_key] = (new_steps, current_key, move)
                h = self._heuristic(new_board.pegs, get_pattern_db())
                f = new_steps + h
                counter += 1
                heappush(heap, (f, counter, new_steps, new_board))
        
        self._log(f"No solution. {self.stats}")
        return None
    
    def _heuristic(self, pegs: int, db) -> int:
        """Комбинированная эвристика."""
        # Используем быстрый popcount
        import sys
        if sys.version_info >= (3, 10):
            peg_count = pegs.bit_count()
        else:
            x = pegs
            x = x - ((x >> 1) & 0x5555555555555555)
            x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
            x = (x + (x >> 4)) & 0x0F0F0F0F0F0F0F0F
            peg_count = ((x * 0x0101010101010101) >> 56) & 0xFF
        
        base_h = peg_count - 1
        pattern_h = db.get_heuristic(pegs)
        return max(base_h, pattern_h)
    
    def _reconstruct_path(self, visited: Dict, end: BitBoard, start_key: int) -> List:
        path = []
        key = self._get_key(end)
        while key != start_key:
            _, parent_key, move = visited[key]
            if move:
                path.append(move)
            key = parent_key
        return list(reversed(path))
