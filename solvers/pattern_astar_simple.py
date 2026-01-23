"""
solvers/pattern_astar_simple.py

A* с Pattern Database эвристикой - Фаза 3.3.
Использует предвычисленные эвристики для более точной оценки.
"""

from typing import List, Tuple, Optional, Dict
from heapq import heappush, heappop

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, is_english_board, get_center_position
from core.optimized_bitboard import (
    optimized_get_moves, optimized_apply_move, optimized_peg_count
)
from heuristics.pattern_db import PatternDatabase, get_pattern_db


class PatternAStarSimpleSolver(BaseSolver):
    """
    A* решатель с Pattern Database эвристикой.
    
    Особенности:
    - Использует предвычисленные эвристики (Pattern Database)
    - Более точная оценка позиций
    - Admissible эвристика (не переоценивает)
    - Эффективен для английской доски
    
    Pattern Database:
    - Разбивает доску на регионы
    - Предвычисляет минимальное количество ходов для очистки каждого региона
    - Сумма по регионам = нижняя граница для полного решения
    """
    
    def __init__(self, use_symmetry: bool = True, use_pattern_db: bool = True,
                 verbose: bool = False):
        """
        Args:
            use_symmetry: использовать канонические формы
            use_pattern_db: использовать Pattern Database (только для английской доски)
            verbose: выводить отладочную информацию
        """
        super().__init__(use_symmetry=use_symmetry, verbose=verbose)
        self.use_pattern_db = use_pattern_db
        self.pattern_db: Optional[PatternDatabase] = None
        
        if use_pattern_db:
            try:
                self.pattern_db = get_pattern_db()
                self._log("Pattern Database loaded")
            except Exception as e:
                self._log(f"Failed to load Pattern Database: {e}")
                self.pattern_db = None
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку алгоритмом A* с Pattern Database эвристикой.
        
        Args:
            board: начальная позиция
            
        Returns:
            Список ходов (from, jumped, to) или None если решение не найдено
        """
        self.stats = SolverStats()
        
        # Проверяем, можем ли использовать Pattern Database
        if self.use_pattern_db and not is_english_board(board):
            self._log("Pattern Database only works for English board, falling back to simple heuristic")
            self.pattern_db = None
        
        self._log(f"Starting Pattern A* (pegs={optimized_peg_count(board)}, pattern_db={self.pattern_db is not None})")
        
        # Приоритетная очередь: (f_score, counter, steps, board)
        heap = []
        counter = 0
        
        # Отслеживание посещённых состояний: key -> (g_score, parent_key, move)
        visited: Dict[int, Tuple[int, Optional[int], Optional[Tuple[int, int, int]]]] = {}
        
        # Начальное состояние
        start_key = self._get_key(board)
        g_score = 0
        h_score = self._heuristic(board)
        f_score = g_score + h_score
        
        heappush(heap, (f_score, counter, g_score, board))
        visited[start_key] = (g_score, None, None)
        counter += 1
        
        while heap:
            f_score, _, g_score, current = heappop(heap)
            self.stats.nodes_visited += 1
            self.stats.max_depth = max(self.stats.max_depth, g_score)
            
            # Проверка победы (используем оптимизированную версию)
            if optimized_peg_count(current) == 1:
                path = self._reconstruct_path(visited, current, start_key)
                self.stats.solution_length = len(path)
                self._log(f"Solution found: {len(path)} moves")
                self._log(f"Stats: {self.stats}")
                return path
            
            # Проверка тупика (используем оптимизированную версию)
            from core.optimized_bitboard import optimized_is_dead
            if optimized_is_dead(current):
                self.stats.nodes_pruned += 1
                continue
            
            current_key = self._get_key(current)
            
            # Исследуем все возможные ходы (используем оптимизированную версию)
            for move in optimized_get_moves(current):
                new_board = optimized_apply_move(current, *move)
                new_key = self._get_key(new_board)
                new_g_score = g_score + 1
                
                # Если уже посещали с лучшим или равным g_score, пропускаем
                if new_key in visited:
                    stored_g_score, _, _ = visited[new_key]
                    if new_g_score >= stored_g_score:
                        continue
                
                # Вычисляем эвристику и f_score
                new_h_score = self._heuristic(new_board)
                new_f_score = new_g_score + new_h_score
                
                # Обновляем visited и добавляем в очередь
                visited[new_key] = (new_g_score, current_key, move)
                heappush(heap, (new_f_score, counter, new_g_score, new_board))
                counter += 1
        
        self._log("No solution found")
        self._log(f"Stats: {self.stats}")
        return None
    
    def _heuristic(self, board: BitBoard) -> float:
        """
        Вычисляет эвристическую оценку позиции.
        
        Использует Pattern Database если доступна, иначе простую эвристику.
        
        Args:
            board: состояние доски
            
        Returns:
            Эвристическая оценка (меньше = лучше)
        """
        # Используем Pattern Database если доступна
        if self.pattern_db is not None and is_english_board(board):
            try:
                from heuristics.pattern_db import pattern_heuristic
                return pattern_heuristic(board, self.pattern_db)
            except Exception as e:
                self._log(f"Pattern DB error: {e}, falling back to simple heuristic")
        
        # Fallback: простая эвристика
        from heuristics.basic import heuristic_peg_count, heuristic_distance_to_center
        
        h = heuristic_peg_count(board)
        
        center_pos = get_center_position(board)
        if center_pos is not None:
            dist = heuristic_distance_to_center(board,
                center=(center_pos // 7, center_pos % 7))
            h += dist * 0.1
        
        return h
    
    def _reconstruct_path(self, visited: Dict[int, Tuple[int, Optional[int], Optional[Tuple[int, int, int]]]], 
                          end: BitBoard, start_key: int) -> List[Tuple[int, int, int]]:
        """
        Восстанавливает путь от конечного состояния к начальному.
        
        Args:
            visited: словарь посещённых состояний
            end: конечное состояние
            start_key: ключ начального состояния
            
        Returns:
            Список ходов от начала к концу
        """
        path = []
        key = self._get_key(end)
        
        while key != start_key:
            _, parent_key, move = visited[key]
            if move is not None:
                path.append(move)
            if parent_key is None:
                break
            key = parent_key
        
        return list(reversed(path))
