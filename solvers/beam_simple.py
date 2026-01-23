"""
solvers/beam_simple.py

Beam Search решатель - Фаза 2.3.
Быстрый неполный решатель для позиций где полное решение не требуется.
"""

from typing import List, Tuple, Optional

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, get_center_position
from core.optimized_bitboard import (
    optimized_get_moves, optimized_apply_move, optimized_peg_count, optimized_is_dead
)
from heuristics.basic import heuristic_peg_count, heuristic_distance_to_center
from heuristics.arbitrary import heuristic_mobility_arbitrary
from solvers.optimized_utils import evaluate_position_optimized


class BeamSimpleSolver(BaseSolver):
    """
    Beam Search решатель.
    
    Особенности:
    - Хранит только top-K лучших состояний на каждом уровне
    - Быстрый, но не гарантирует нахождение решения
    - Полезен для быстрой оценки позиций
    
    Алгоритм:
    1. Начинаем с начального состояния
    2. На каждом шаге расширяем все состояния из beam
    3. Оцениваем все новые состояния
    4. Оставляем только top-K лучших
    5. Повторяем пока не найдём решение или не исчерпаем beam
    """
    
    def __init__(self, beam_width: int = 100, max_depth: int = 50,
                 use_symmetry: bool = True, verbose: bool = False):
        """
        Args:
            beam_width: ширина луча (количество состояний на уровне)
            max_depth: максимальная глубина поиска
            use_symmetry: использовать канонические формы
            verbose: выводить отладочную информацию
        """
        super().__init__(use_symmetry=use_symmetry, verbose=verbose)
        self.beam_width = beam_width
        self.max_depth = max_depth
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку алгоритмом Beam Search.
        
        Args:
            board: начальная позиция
            
        Returns:
            Список ходов (from, jumped, to) или None если решение не найдено
        """
        self.stats = SolverStats()
        
        self._log(f"Starting Beam Search (pegs={board.peg_count()}, beam_width={self.beam_width}, max_depth={self.max_depth})")
        
        # Beam: список (score, steps, board, path)
        beam = [(self._evaluate(board), 0, board, [])]
        visited = set()
        
        for depth in range(self.max_depth):
            if not beam:
                break
            
            self.stats.max_depth = depth
            new_beam = []
            
            for score, steps, current, path in beam:
                self.stats.nodes_visited += 1
                self.stats.max_depth = max(self.stats.max_depth, steps)
                
                # Проверка победы (используем оптимизированную версию)
                if optimized_peg_count(current) == 1:
                    self.stats.solution_length = len(path)
                    self._log(f"Solution found: {len(path)} moves")
                    self._log(f"Stats: {self.stats}")
                    return path
                
                # Проверка тупика (используем оптимизированную версию)
                if optimized_is_dead(current):
                    self.stats.nodes_pruned += 1
                    continue
                
                # Получаем все возможные ходы (используем оптимизированную версию)
                moves = optimized_get_moves(current)
                if not moves:
                    continue
                
                # Расширяем состояние (используем оптимизированную версию)
                for move in moves:
                    new_board = optimized_apply_move(current, *move)
                    new_key = self._get_key(new_board)
                    
                    # Пропускаем уже посещённые
                    if new_key in visited:
                        continue
                    
                    visited.add(new_key)
                    new_path = path + [move]
                    # Используем оптимизированную оценку если доступна
                    try:
                        num_moves = len(new_board.get_moves())
                        new_score = evaluate_position_optimized(new_board, num_moves)
                    except Exception:
                        # Fallback на простую оценку
                        new_score = self._evaluate(new_board)
                    new_steps = steps + 1
                    
                    new_beam.append((new_score, new_steps, new_board, new_path))
            
            # Оставляем только top-K лучших
            new_beam.sort(key=lambda x: x[0])  # Сортируем по score (меньше = лучше)
            beam = new_beam[:self.beam_width]
            
            if depth % 5 == 0:
                self._log(f"Depth {depth}, beam: {len(beam)}")
        
        self._log("No solution found (beam exhausted)")
        self._log(f"Stats: {self.stats}")
        return None
    
    def _evaluate(self, board: BitBoard) -> float:
        """
        Оценивает позицию (меньше = лучше).
        
        Args:
            board: состояние доски
            
        Returns:
            Оценка позиции
        """
        # Базовая эвристика: количество колышков
        score = heuristic_peg_count(board)
        
        # Дополнительно: расстояние до центра
        center_pos = get_center_position(board)
        if center_pos is not None:
            dist = heuristic_distance_to_center(board,
                center=(center_pos // 7, center_pos % 7))
            score += dist * 0.1
        
        # Мобильность (больше ходов = лучше, поэтому вычитаем)
        mobility = heuristic_mobility_arbitrary(board)
        score -= mobility * 0.5
        
        return score
