"""
solvers/astar.py

A* и IDA* решатели.
"""

from typing import List, Tuple, Optional, Dict
from heapq import heappush, heappop

from .base import BaseSolver, SolverStats
from core.bitboard import (
    BitBoard, CENTER_POS,
    is_english_board, get_center_position
)
from heuristics import combined_heuristic, pagoda_value, PAGODA_WEIGHTS


class AStarSolver(BaseSolver):
    """
    A* решатель с эвристикой.
    
    f(n) = g(n) + h(n)
    - g(n) = количество сделанных ходов
    - h(n) = эвристическая оценка до цели
    """
    
    def __init__(self, use_symmetry: bool = True, aggressive: bool = False,
                 verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.aggressive = aggressive
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        
        self._log(f"Starting A* (pegs={board.peg_count()}, aggressive={self.aggressive})")
        
        # Pagoda check (только для английской доски)
        if is_english_board(board):
            if pagoda_value(board) < PAGODA_WEIGHTS[CENTER_POS]:
                self._log("Position unsolvable (Pagoda)")
                return None
        
        counter = 0
        heap = []
        visited: Dict[int, Tuple[int, int, Tuple]] = {}  # key -> (steps, parent_key, move)
        
        start_key = self._get_key(board)
        h = combined_heuristic(board, 0, self.aggressive)
        heappush(heap, (h, counter, 0, board))
        visited[start_key] = (0, None, None)
        
        while heap:
            _, _, steps, current = heappop(heap)
            self.stats.nodes_visited += 1
            self.stats.max_depth = max(self.stats.max_depth, steps)
            
            if current.peg_count() == 1:
                # Восстанавливаем путь
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
                h = combined_heuristic(new_board, new_steps, self.aggressive)
                counter += 1
                heappush(heap, (h, counter, new_steps, new_board))
        
        self._log(f"No solution. {self.stats}")
        return None
    
    def _reconstruct_path(self, visited: Dict, end: BitBoard, start_key: int) -> List:
        path = []
        key = self._get_key(end)
        while key != start_key:
            _, parent_key, move = visited[key]
            if move:
                path.append(move)
            key = parent_key
        return list(reversed(path))


class IDAStarSolver(BaseSolver):
    """
    IDA* (Iterative Deepening A*) решатель.
    
    Экономит память: не хранит все состояния.
    """
    
    def __init__(self, use_symmetry: bool = True, max_depth: int = 35,
                 verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.max_depth = max_depth
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        
        self._log(f"Starting IDA* (pegs={board.peg_count()})")
        
        # Целевая Pagoda только для английской доски
        target_pagoda = PAGODA_WEIGHTS[CENTER_POS] if is_english_board(board) else None
        bound = board.peg_count() - 1
        
        while bound <= self.max_depth:
            self._log(f"Bound: {bound}")
            visited = set()
            result, new_bound = self._search(board, 0, bound, [], visited, target_pagoda)
            
            if result is not None:
                self.stats.solution_length = len(result)
                self._log(f"Found! {self.stats}")
                return result
            
            if new_bound == float('inf'):
                break
            bound = new_bound
        
        self._log(f"No solution. {self.stats}")
        return None
    
    def _search(self, board: BitBoard, g: int, bound: float, path: List,
                visited: set, target_pagoda: int) -> Tuple[Optional[List], float]:
        self.stats.nodes_visited += 1
        
        f = g + (board.peg_count() - 1)
        if f > bound:
            return None, f
        
        if board.peg_count() == 1:
            return path, f
        
        # Pagoda pruning (только для английской доски)
        if target_pagoda is not None and pagoda_value(board) < target_pagoda:
            self.stats.nodes_pruned += 1
            return None, float('inf')
        
        key = self._get_key(board)
        if key in visited:
            return None, float('inf')
        visited.add(key)
        
        moves = board.get_moves()
        if not moves:
            return None, float('inf')
        
        # Сортировка по расстоянию до центра
        center_pos = get_center_position(board)
        if center_pos is not None:
            center_r, center_c = center_pos // 7, center_pos % 7
            moves.sort(key=lambda m: abs(m[2] // 7 - center_r) + abs(m[2] % 7 - center_c))
        else:
            # Fallback: расстояние до центра доски (3, 3)
            moves.sort(key=lambda m: abs(m[2] // 7 - 3) + abs(m[2] % 7 - 3))
        
        min_threshold = float('inf')
        for move in moves:
            new_board = board.apply_move(*move)
            result, threshold = self._search(
                new_board, g + 1, bound, path + [move], visited, target_pagoda
            )
            if result is not None:
                return result, threshold
            min_threshold = min(min_threshold, threshold)
        
        return None, min_threshold
