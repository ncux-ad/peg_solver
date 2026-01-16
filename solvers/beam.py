"""
solvers/beam.py

Beam Search — ограниченный по ширине поиск.
"""

from typing import List, Tuple, Optional

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, ENGLISH_VALID_POSITIONS, CENTER_POS
from heuristics import pagoda_value, PAGODA_WEIGHTS


class BeamSolver(BaseSolver):
    """
    Beam Search решатель.
    
    Сохраняет только K лучших состояний на каждом уровне.
    
    Плюсы:
    - Контролируемый расход памяти
    - Быстрее чем полный BFS
    
    Минусы:
    - Может пропустить решение (неполный алгоритм)
    """
    
    def __init__(self, beam_width: int = 100, max_depth: int = 35,
                 use_symmetry: bool = True, verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.beam_width = beam_width
        self.max_depth = max_depth
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        
        self._log(f"Starting Beam Search (width={self.beam_width})")
        
        beam = [(board, [])]
        visited = {self._get_key(board)}
        
        for depth in range(self.max_depth):
            if not beam:
                break
            
            self.stats.max_depth = depth
            candidates = []
            
            for current, path in beam:
                self.stats.nodes_visited += 1
                
                if current.peg_count() == 1:
                    self.stats.solution_length = len(path)
                    self._log(f"Found at depth {depth}! {self.stats}")
                    return path
                
                for move in current.get_moves():
                    new_board = current.apply_move(*move)
                    key = self._get_key(new_board)
                    
                    if key in visited:
                        continue
                    visited.add(key)
                    
                    score = self._evaluate(new_board)
                    candidates.append((score, new_board, path + [move]))
            
            # Оставляем лучшие
            candidates.sort(key=lambda x: x[0])
            beam = [(b, p) for _, b, p in candidates[:self.beam_width]]
            
            if depth % 5 == 0:
                self._log(f"Depth {depth}, beam: {len(beam)}")
        
        self._log(f"No solution. {self.stats}")
        return None
    
    def _evaluate(self, board: BitBoard) -> float:
        """Оценка позиции (меньше = лучше)."""
        score = board.peg_count() * 10
        
        # Расстояние до центра
        for pos in ENGLISH_VALID_POSITIONS:
            if board.has_peg(pos):
                r, c = pos // 7, pos % 7
                score += abs(r - 3) + abs(c - 3)
        
        # Мобильность
        score -= len(board.get_moves()) * 2
        
        # Изолированные колышки
        score += self._count_isolated(board) * 15
        
        # Pagoda
        if pagoda_value(board) < PAGODA_WEIGHTS[CENTER_POS]:
            score += 1000
        
        return score
    
    def _count_isolated(self, board: BitBoard) -> int:
        """Количество изолированных колышков."""
        count = 0
        for pos in ENGLISH_VALID_POSITIONS:
            if not board.has_peg(pos):
                continue
            r, c = pos // 7, pos % 7
            has_neighbor = any(
                board.has_peg(nr * 7 + nc)
                for nr, nc in [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                if (nr * 7 + nc) in ENGLISH_VALID_POSITIONS
            )
            if not has_neighbor:
                count += 1
        return count
