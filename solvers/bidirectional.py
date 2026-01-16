"""
solvers/bidirectional.py

Bidirectional Search — двунаправленный поиск.
"""

from typing import List, Tuple, Optional, Dict
from collections import deque

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, ENGLISH_GOAL, ENGLISH_VALID_POSITIONS
from core.utils import DIRECTIONS


class BidirectionalSolver(BaseSolver):
    """
    Двунаправленный поиск.
    
    Ищет одновременно:
    - От начальной позиции вперёд
    - От целевой позиции назад
    
    Встречаются посередине — O(b^(d/2)) вместо O(b^d).
    """
    
    def __init__(self, max_iterations: int = 100000, use_symmetry: bool = True,
                 verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.max_iterations = max_iterations
    
    def solve(self, board: BitBoard, 
              target: BitBoard = None) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        
        if target is None:
            target = BitBoard(ENGLISH_GOAL)
        
        self._log(f"Starting Bidirectional (start={board.peg_count()}, target={target.peg_count()})")
        
        # Прямой поиск
        forward_queue = deque([(board, [])])
        forward_visited: Dict[int, List] = {board.pegs: []}
        
        # Обратный поиск
        backward_queue = deque([(target, [])])
        backward_visited: Dict[int, List] = {target.pegs: []}
        
        iterations = 0
        
        while forward_queue or backward_queue:
            iterations += 1
            self.stats.nodes_visited = iterations
            
            if iterations > self.max_iterations:
                self._log(f"Max iterations reached. {self.stats}")
                return None
            
            # Шаг вперёд
            if forward_queue:
                result = self._forward_step(
                    forward_queue, forward_visited, backward_visited
                )
                if result:
                    self.stats.solution_length = len(result)
                    self._log(f"Met at iteration {iterations}! {self.stats}")
                    return result
            
            # Шаг назад
            if backward_queue:
                result = self._backward_step(
                    backward_queue, backward_visited, forward_visited
                )
                if result:
                    self.stats.solution_length = len(result)
                    self._log(f"Met at iteration {iterations}! {self.stats}")
                    return result
        
        self._log(f"No solution. {self.stats}")
        return None
    
    def _forward_step(self, queue, forward_visited, backward_visited):
        current, path = queue.popleft()
        
        for move in current.get_moves():
            new_board = current.apply_move(*move)
            new_path = path + [move]
            
            if new_board.pegs in backward_visited:
                backward_path = backward_visited[new_board.pegs]
                return new_path + list(reversed(backward_path))
            
            if new_board.pegs not in forward_visited:
                forward_visited[new_board.pegs] = new_path
                queue.append((new_board, new_path))
        
        return None
    
    def _backward_step(self, queue, backward_visited, forward_visited):
        current, path = queue.popleft()
        
        # Генерируем обратные ходы
        for pos in ENGLISH_VALID_POSITIONS:
            if not current.has_peg(pos):  # это hole
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_board = self._reverse_move(current, pos, dr, dc)
                    if new_board is None:
                        continue
                    
                    # Ход в прямом направлении
                    from_pos = pos + 2 * (dr * 7 + dc)
                    move = (from_pos, pos + dr * 7 + dc, pos)
                    new_path = path + [move]
                    
                    if new_board.pegs in forward_visited:
                        forward_path = forward_visited[new_board.pegs]
                        return forward_path + list(reversed(new_path))
                    
                    if new_board.pegs not in backward_visited:
                        backward_visited[new_board.pegs] = new_path
                        queue.append((new_board, new_path))
        
        return None
    
    def _reverse_move(self, board: BitBoard, r: int, dr: int, dc: int) -> Optional[BitBoard]:
        """Обратный ход: hole hole peg → peg peg hole."""
        pos1 = r + dr * 7 + dc
        pos2 = r + 2 * (dr * 7 + dc)
        
        if pos1 not in ENGLISH_VALID_POSITIONS or pos2 not in ENGLISH_VALID_POSITIONS:
            return None
        
        if board.has_peg(r) or board.has_peg(pos1) or not board.has_peg(pos2):
            return None
        
        new_pegs = board.pegs
        new_pegs |= (1 << r)
        new_pegs |= (1 << pos1)
        new_pegs ^= (1 << pos2)
        
        return BitBoard(new_pegs)
