"""
solvers/ida_simple.py

IDA* (Iterative Deepening A*) решатель - Фаза 3.1.
Экономит память: не хранит все состояния, использует итеративное углубление.
"""

from typing import List, Tuple, Optional, Set

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, is_english_board, get_center_position
from heuristics.basic import heuristic_peg_count, heuristic_distance_to_center


class IDASimpleSolver(BaseSolver):
    """
    IDA* (Iterative Deepening A*) решатель.
    
    Особенности:
    - Экономия памяти: не хранит все состояния в памяти
    - Итеративное углубление: увеличивает bound до нахождения решения
    - Использует простые эвристики
    - Подходит для больших пространств поиска
    
    Алгоритм:
    1. Начинаем с начального bound = h(start)
    2. Выполняем DFS с ограничением f(n) <= bound
    3. Если решение не найдено, увеличиваем bound до минимального превышения
    4. Повторяем пока не найдём решение
    """
    
    def __init__(self, use_symmetry: bool = True, max_depth: int = 50,
                 verbose: bool = False):
        """
        Args:
            use_symmetry: использовать канонические формы
            max_depth: максимальная глубина поиска
            verbose: выводить отладочную информацию
        """
        super().__init__(use_symmetry=use_symmetry, verbose=verbose)
        self.max_depth = max_depth
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку алгоритмом IDA*.
        
        Args:
            board: начальная позиция
            
        Returns:
            Список ходов (from, jumped, to) или None если решение не найдено
        """
        self.stats = SolverStats()
        
        self._log(f"Starting IDA* (pegs={board.peg_count()}, max_depth={self.max_depth})")
        
        # Начальный bound = эвристика начальной позиции
        bound = self._heuristic(board)
        
        while bound <= self.max_depth:
            self._log(f"Trying bound: {bound}")
            
            visited: Set[int] = set()
            result, new_bound = self._search(board, 0, bound, [], visited)
            
            if result is not None:
                self.stats.solution_length = len(result)
                self._log(f"Solution found: {len(result)} moves")
                self._log(f"Stats: {self.stats}")
                return result
            
            if new_bound == float('inf'):
                # Нет решения в пределах max_depth
                break
            
            # Увеличиваем bound до минимального превышения
            bound = new_bound
        
        self._log("No solution found")
        self._log(f"Stats: {self.stats}")
        return None
    
    def _search(self, board: BitBoard, g_score: int, bound: float,
                path: List[Tuple[int, int, int]], visited: Set[int]) -> Tuple[Optional[List[Tuple[int, int, int]]], float]:
        """
        Рекурсивный поиск с ограничением bound.
        
        Args:
            board: текущее состояние доски
            g_score: стоимость пути до текущего состояния
            bound: максимальное значение f(n) для исследования
            path: путь ходов до текущего состояния
            visited: множество посещённых состояний на текущей итерации
            
        Returns:
            (решение или None, новый bound если решение не найдено)
        """
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Вычисляем f(n) = g(n) + h(n)
        h_score = self._heuristic(board)
        f_score = g_score + h_score
        
        # Если превысили bound, возвращаем новый bound
        if f_score > bound:
            return None, f_score
        
        # Проверка победы
        if board.peg_count() == 1:
            return path, f_score
        
        # Проверка на циклы (в рамках текущей итерации)
        key = self._get_key(board)
        if key in visited:
            return None, float('inf')
        visited.add(key)
        
        # Получаем все возможные ходы
        moves = board.get_moves()
        if not moves:
            return None, float('inf')
        
        # Сортируем ходы по эвристике (ближе к центру = лучше)
        moves = self._sort_moves(board, moves)
        
        # Ищем решение с минимальным превышением bound
        min_threshold = float('inf')
        
        for move in moves:
            new_board = board.apply_move(*move)
            result, threshold = self._search(
                new_board, g_score + 1, bound, path + [move], visited
            )
            
            if result is not None:
                return result, threshold
            
            min_threshold = min(min_threshold, threshold)
        
        return None, min_threshold
    
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
            h += dist * 0.1
        
        return h
    
    def _sort_moves(self, board: BitBoard, moves: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Сортирует ходы по эвристике: ближе к центру = лучше.
        
        Args:
            board: текущее состояние доски
            moves: список ходов для сортировки
            
        Returns:
            Отсортированный список ходов
        """
        center_pos = get_center_position(board)
        
        def priority(move: Tuple[int, int, int]) -> float:
            _, _, to_pos = move
            to_r, to_c = to_pos // 7, to_pos % 7
            
            if center_pos is not None:
                center_r, center_c = center_pos // 7, center_pos % 7
                center_dist = abs(to_r - center_r) + abs(to_c - center_c)
            else:
                center_dist = abs(to_r - 3) + abs(to_c - 3)
            
            return center_dist
        
        return sorted(moves, key=priority)
