"""
solvers/parallel_beam.py

Параллельный Beam Search - распараллеливает обработку каждого уровня.
"""

from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import threading

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, ENGLISH_VALID_POSITIONS, CENTER_POS
from heuristics import pagoda_value, PAGODA_WEIGHTS


class ParallelBeamSolver(BaseSolver):
    """
    Параллельный Beam Search - обрабатывает каждый уровень параллельно.
    
    Особенности:
    - Распараллеливает генерацию и оценку ходов
    - Использует ThreadPoolExecutor для параллелизма
    - Ускоряет поиск в ~N раз (где N = количество ядер)
    """
    
    def __init__(self, beam_width: int = 500, max_depth: int = 35,
                 num_workers: int = None, use_symmetry: bool = True,
                 verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.beam_width = beam_width
        self.max_depth = max_depth
        self.num_workers = num_workers or min(multiprocessing.cpu_count(), 8)
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        
        self._log(f"Starting Parallel Beam Search (width={self.beam_width}, workers={self.num_workers})")
        
        beam = [(board, [])]
        visited = {self._get_key(board)}
        
        for depth in range(self.max_depth):
            if not beam:
                break
            
            self.stats.max_depth = depth
            
            # Параллельная генерация и оценка кандидатов
            candidates = self._parallel_expand(beam, visited)
            
            if not candidates:
                break
            
            # Сортировка и выбор лучших
            candidates.sort(key=lambda x: x[0])
            beam = [(b, p) for _, b, p in candidates[:self.beam_width]]
            
            # Проверяем решение в лучших кандидатах
            for current, path in beam[:10]:  # Проверяем топ-10
                self.stats.nodes_visited += 1
                
                if current.peg_count() == 1:
                    self.stats.solution_length = len(path)
                    self._log(f"Found at depth {depth}! {self.stats}")
                    return path
            
            if depth % 5 == 0:
                self._log(f"Depth {depth}, beam: {len(beam)}")
        
        self._log(f"No solution. {self.stats}")
        return None
    
    def _parallel_expand(self, beam: List[Tuple[BitBoard, List]], 
                        visited: set) -> List[Tuple[float, BitBoard, List]]:
        """
        Параллельно расширяет лучшие состояния.
        Использует ThreadPoolExecutor для параллелизма.
        """
        candidates = []
        candidates_lock = threading.Lock()
        
        def expand_state(state_path: Tuple[BitBoard, List]):
            """Расширяет одно состояние и возвращает кандидатов."""
            current, path = state_path
            local_candidates = []
            
            for move in current.get_moves():
                new_board = current.apply_move(*move)
                key = self._get_key(new_board)
                
                # Проверка посещённости (с блокировкой)
                with candidates_lock:
                    if key in visited:
                        continue
                    visited.add(key)
                
                score = self._evaluate(new_board)
                local_candidates.append((score, new_board, path + [move]))
            
            return local_candidates
        
        # Параллельная обработка состояний в beam
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(expand_state, state_path): state_path 
                      for state_path in beam}
            
            for future in as_completed(futures):
                try:
                    local_candidates = future.result()
                    candidates.extend(local_candidates)
                except Exception as e:
                    self._log(f"Error in parallel expansion: {e}")
        
        return candidates
    
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
        
        # Pagoda (мягкий)
        min_pagoda = min(PAGODA_WEIGHTS.values())
        current_pagoda = pagoda_value(board)
        
        if board.peg_count() > 15:
            if current_pagoda < PAGODA_WEIGHTS[CENTER_POS]:
                score += 1000
        else:
            if current_pagoda < min_pagoda:
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
