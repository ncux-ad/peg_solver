"""
solvers/astar_simple.py

A* решатель - Фаза 2.2.
Упрощённая версия A* с базовыми эвристиками.
"""

from typing import List, Tuple, Optional, Dict
from heapq import heappush, heappop

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, is_english_board, get_center_position
from core.optimized_bitboard import (
    optimized_get_moves, optimized_apply_move, optimized_peg_count, optimized_is_dead
)
from heuristics.basic import heuristic_peg_count, heuristic_distance_to_center


class AStarSimpleSolver(BaseSolver):
    """
    A* решатель с простыми эвристиками.
    
    f(n) = g(n) + h(n)
    - g(n) = количество сделанных ходов (стоимость пути)
    - h(n) = эвристическая оценка до цели
    
    Эвристики:
    - Количество колышков - 1 (минимум ходов)
    - Расстояние до центра (манхэттенское)
    
    Особенности:
    - Использует приоритетную очередь (heap)
    - Отслеживает посещённые состояния
    - Восстанавливает путь от цели к началу
    """
    
    def __init__(self, use_symmetry: bool = True, verbose: bool = False):
        """
        Args:
            use_symmetry: использовать канонические формы для visited set
            verbose: выводить отладочную информацию
        """
        super().__init__(use_symmetry=use_symmetry, verbose=verbose)
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку алгоритмом A*.
        
        Args:
            board: начальная позиция
            
        Returns:
            Список ходов (from, jumped, to) или None если решение не найдено
        """
        self.stats = SolverStats()
        
        self._log(f"Starting A* (pegs={board.peg_count()})")
        
        # Приоритетная очередь: (f_score, counter, steps, board)
        # counter нужен для разрешения равенств в heap
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
                # Восстанавливаем путь
                path = self._reconstruct_path(visited, current, start_key)
                self.stats.solution_length = len(path)
                self._log(f"Solution found: {len(path)} moves")
                self._log(f"Stats: {self.stats}")
                return path
            
            # Проверка тупика (используем оптимизированную версию)
            if optimized_is_dead(current):
                self.stats.nodes_pruned += 1
                continue
            
            current_key = self._get_key(current)
            
            # Проверяем, не посещали ли мы это состояние с лучшим g_score
            # (но это уже проверено при добавлении в heap, так что пропускаем)
            
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
        
        Args:
            board: состояние доски
            
        Returns:
            Эвристическая оценка (меньше = лучше)
        """
        # Базовая эвристика: количество колышков - 1
        h = heuristic_peg_count(board)
        
        # Дополнительно: расстояние до центра
        center_pos = get_center_position(board)
        if center_pos is not None:
            dist = heuristic_distance_to_center(board, 
                center=(center_pos // 7, center_pos % 7))
            h += dist * 0.1  # Небольшой вес для расстояния
        
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
