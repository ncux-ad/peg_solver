"""
solvers/bidirectional_simple.py

Bidirectional Search решатель - Фаза 3.2.
Двунаправленный поиск: одновременно от начала и от конца.
"""

from typing import List, Tuple, Optional, Dict
from collections import deque

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, ENGLISH_GOAL, get_center_position


class BidirectionalSimpleSolver(BaseSolver):
    """
    Двунаправленный поиск (Bidirectional Search).
    
    Особенности:
    - Ищет одновременно от начальной позиции вперёд и от целевой назад
    - Встречаются посередине — O(b^(d/2)) вместо O(b^d)
    - Эффективен для задач где известна целевая позиция
    
    Алгоритм:
    1. Два BFS: один от start, другой от goal
    2. На каждом шаге расширяем оба фронта
    3. Когда состояния встречаются — объединяем пути
    """
    
    def __init__(self, use_symmetry: bool = True, verbose: bool = False):
        """
        Args:
            use_symmetry: использовать канонические формы
            verbose: выводить отладочную информацию
        """
        super().__init__(use_symmetry=use_symmetry, verbose=verbose)
    
    def solve(self, board: BitBoard, target: Optional[BitBoard] = None) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку двунаправленным поиском.
        
        Args:
            board: начальная позиция
            target: целевая позиция (если None, используется стандартная цель - 1 колышек в центре)
            
        Returns:
            Список ходов (from, jumped, to) или None если решение не найдено
        """
        self.stats = SolverStats()
        
        # Если target не указан, используем стандартную цель
        if target is None:
            # Для английской доски - центр, иначе любое состояние с 1 колышком
            if board.valid_mask == BitBoard.english_start().valid_mask:
                target = BitBoard.english_goal()
            else:
                # Для произвольной доски создаём цель с 1 колышком в центре доски
                center_pos = get_center_position(board)
                if center_pos is None:
                    # Если нет центра, используем первую валидную позицию
                    valid_positions = [pos for pos in range(49) if (board.valid_mask >> pos) & 1]
                    if not valid_positions:
                        return None
                    center_pos = valid_positions[0]
                target = BitBoard(1 << center_pos, valid_mask=board.valid_mask)
        
        self._log(f"Starting Bidirectional Search (start={board.peg_count()}, target={target.peg_count()})")
        
        # Прямой поиск: от start к target
        forward_queue = deque([(board, [])])
        forward_visited: Dict[int, List[Tuple[int, int, int]]] = {self._get_key(board): []}
        
        # Обратный поиск: от target к start
        backward_queue = deque([(target, [])])
        backward_visited: Dict[int, List[Tuple[int, int, int]]] = {self._get_key(target): []}
        
        iteration = 0
        max_iterations = 1000000  # Защита от бесконечного цикла
        
        while forward_queue or backward_queue:
            iteration += 1
            if iteration > max_iterations:
                self._log(f"Max iterations reached: {max_iterations}")
                break
            
            # Шаг вперёд
            if forward_queue:
                result = self._forward_step(forward_queue, forward_visited, backward_visited)
                if result is not None:
                    self.stats.solution_length = len(result)
                    self._log(f"Solution found: {len(result)} moves (met at iteration {iteration})")
                    self._log(f"Stats: {self.stats}")
                    return result
            
            # Шаг назад
            if backward_queue:
                result = self._backward_step(backward_queue, backward_visited, forward_visited)
                if result is not None:
                    self.stats.solution_length = len(result)
                    self._log(f"Solution found: {len(result)} moves (met at iteration {iteration})")
                    self._log(f"Stats: {self.stats}")
                    return result
        
        self._log("No solution found")
        self._log(f"Stats: {self.stats}")
        return None
    
    def _forward_step(self, queue: deque, visited: Dict[int, List[Tuple[int, int, int]]],
                     other_visited: Dict[int, List[Tuple[int, int, int]]]) -> Optional[List[Tuple[int, int, int]]]:
        """
        Один шаг прямого поиска.
        
        Args:
            queue: очередь состояний для расширения
            visited: словарь посещённых состояний (key -> path)
            other_visited: словарь состояний из обратного поиска
            
        Returns:
            Решение если встретились, иначе None
        """
        if not queue:
            return None
        
        current, path = queue.popleft()
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Проверяем, не встретились ли с обратным поиском
        current_key = self._get_key(current)
        if current_key in other_visited:
            # Встретились! Объединяем пути
            backward_path = other_visited[current_key]
            # Обратный путь нужно инвертировать
            reversed_backward = self._reverse_path(backward_path)
            return path + reversed_backward
        
        # Расширяем состояние
        for move in current.get_moves():
            new_board = current.apply_move(*move)
            new_key = self._get_key(new_board)
            
            # Пропускаем уже посещённые
            if new_key in visited:
                continue
            
            visited[new_key] = path + [move]
            queue.append((new_board, path + [move]))
        
        return None
    
    def _backward_step(self, queue: deque, visited: Dict[int, List[Tuple[int, int, int]]],
                      other_visited: Dict[int, List[Tuple[int, int, int]]]) -> Optional[List[Tuple[int, int, int]]]:
        """
        Один шаг обратного поиска.
        
        Args:
            queue: очередь состояний для расширения
            visited: словарь посещённых состояний (key -> path)
            other_visited: словарь состояний из прямого поиска
            
        Returns:
            Решение если встретились, иначе None
        """
        if not queue:
            return None
        
        current, path = queue.popleft()
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Проверяем, не встретились ли с прямым поиском
        current_key = self._get_key(current)
        if current_key in other_visited:
            # Встретились! Объединяем пути
            forward_path = other_visited[current_key]
            # Обратный путь нужно инвертировать
            reversed_path = self._reverse_path(path)
            return forward_path + reversed_path
        
        # Расширяем состояние (обратные ходы)
        for move in current.get_moves():
            new_board = current.apply_move(*move)
            new_key = self._get_key(new_board)
            
            # Пропускаем уже посещённые
            if new_key in visited:
                continue
            
            visited[new_key] = path + [move]
            queue.append((new_board, path + [move]))
        
        return None
    
    def _reverse_path(self, path: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Инвертирует путь (для обратного поиска).
        
        Ход (from, jumped, to) становится (to, jumped, from).
        
        Args:
            path: путь для инвертирования
            
        Returns:
            Инвертированный путь
        """
        reversed_path = []
        for from_pos, jumped, to_pos in reversed(path):
            # Инвертируем ход: (from, jumped, to) -> (to, jumped, from)
            reversed_path.append((to_pos, jumped, from_pos))
        return reversed_path
