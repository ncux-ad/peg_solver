"""
solvers/parallel_beam.py

Параллельный Beam Search - распараллеливает обработку каждого уровня.
"""

from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, ENGLISH_VALID_POSITIONS, CENTER_POS
from heuristics import pagoda_value, PAGODA_WEIGHTS
from .optimized_utils import evaluate_position_optimized


def _evaluate_board(state_data: Tuple[int, List]) -> Tuple[float, int, List]:
    """Оценивает состояние доски (для multiprocessing).
    
    Использует оптимизированные функции если доступны.
    """
    from core.bitboard import BitBoard
    from heuristics.evaluation import evaluate_position
    
    pegs, path = state_data
    board = BitBoard(pegs)
    
    # Используем оптимизированную версию оценки
    try:
        score = evaluate_position(board)
    except ImportError:
        # Fallback на оригинальную версию
        from core.bitboard import ENGLISH_VALID_POSITIONS, CENTER_POS
        from heuristics import pagoda_value, PAGODA_WEIGHTS
        
        num_moves = len(board.get_moves())
        score = board.peg_count() * 10.0
        
        center_row, center_col = 3, 3
        for pos in ENGLISH_VALID_POSITIONS:
            if board.has_peg(pos):
                r, c = pos // 7, pos % 7
                score += abs(r - center_row) + abs(c - center_col)
        
        score -= num_moves * 2.0
        
        current_pagoda = pagoda_value(board)
        target_pagoda = PAGODA_WEIGHTS.get(CENTER_POS, 0)
        
        if board.peg_count() > 15:
            if current_pagoda < target_pagoda:
                score += 1000.0
    
    return (score, pegs, path)


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
        Использует ProcessPoolExecutor для настоящего параллелизма.
        """
        candidates = []
        
        # Подготавливаем задачи (сериализуем в int для multiprocessing)
        tasks = []
        for current, path in beam:
            for move in current.get_moves():
                new_board = current.apply_move(*move)
                key = self._get_key(new_board)
                
                # Проверка посещённости
                if key in visited:
                    continue
                visited.add(key)
                
                tasks.append((new_board.pegs, path + [move]))
        
        if not tasks:
            return candidates
        
        # Параллельная оценка (только CPU-bound операция)
        # Используем ProcessPoolExecutor для настоящего параллелизма
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(_evaluate_board, task): task for task in tasks}
            
            for future in as_completed(futures):
                try:
                    score, pegs, path = future.result()
                    board = BitBoard(pegs)
                    candidates.append((score, board, path))
                except Exception as e:
                    self._log(f"Error in parallel evaluation: {e}")
        
        return candidates
    
    def _evaluate(self, board: BitBoard) -> float:
        """Оценка позиции (меньше = лучше). Использует оптимизированную версию."""
        num_moves = len(board.get_moves())
        return evaluate_position_optimized(board, num_moves)
    
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
