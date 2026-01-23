"""
solvers/backward_simple.py

Backward Search (Обратный поиск) решатель.
Начинает с целевого состояния и разворачивает ходы назад.
Эффективен для произвольных досок.
"""

from typing import List, Tuple, Optional, Dict, Set
from collections import deque

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, get_center_position
from core.optimized_bitboard import (
    optimized_get_moves, optimized_apply_move, optimized_peg_count
)


class BackwardSimpleSolver(BaseSolver):
    """
    Обратный поиск (Backward Search) решатель.
    
    Особенности:
    - Начинает с целевого состояния (1 колышек) и разворачивает ходы назад
    - Генерирует "обратные ходы": создаёт колышки вместо удаления
    - Меньше ветвление, чем при прямом поиске
    - Эффективен для произвольных досок
    
    Алгоритм:
    1. Начинаем с целевого состояния (1 колышек)
    2. Генерируем обратные ходы (создаём колышки)
    3. Ищем путь к начальному состоянию
    4. Инвертируем путь для получения решения
    
    Обратный ход:
    - Если прямой ход: (from, jumped, to) удаляет from и jumped, создаёт to
    - Обратный ход: (to, jumped, from) создаёт from и jumped, удаляет to
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
        Решает головоломку обратным поиском.
        
        Args:
            board: начальная позиция (целевое состояние для обратного поиска)
            target: целевая позиция (если None, используется состояние с 1 колышком)
            
        Returns:
            Список ходов (from, jumped, to) от начального к целевому состоянию
        """
        self.stats = SolverStats()
        
        # Определяем целевое состояние для обратного поиска
        if target is None:
            # Для обратного поиска: начинаем с состояния с 1 колышком
            center_pos = get_center_position(board)
            if center_pos is None:
                # Если нет центра, используем первую валидную позицию
                valid_positions = [pos for pos in range(49) if (board.valid_mask >> pos) & 1]
                if not valid_positions:
                    return None
                center_pos = valid_positions[0]
            target = BitBoard(1 << center_pos, valid_mask=board.valid_mask)
        
        # Начальное состояние для обратного поиска = целевое состояние прямой задачи
        start_state = target
        goal_state = board  # Цель обратного поиска = начальное состояние прямой задачи
        
        self._log(f"Starting Backward Search (goal_pegs={optimized_peg_count(goal_state)}, target_pegs={optimized_peg_count(start_state)})")
        
        # BFS от целевого состояния к начальному
        queue = deque([(start_state, [])])
        visited: Dict[int, List[Tuple[int, int, int]]] = {self._get_key(start_state): []}
        
        max_iterations = 10000000  # Защита от бесконечного цикла
        iteration = 0
        
        while queue:
            iteration += 1
            if iteration > max_iterations:
                self._log(f"Max iterations reached: {max_iterations}")
                break
            
            current, path = queue.popleft()
            self.stats.nodes_visited += 1
            self.stats.max_depth = max(self.stats.max_depth, len(path))
            
            # Проверка достижения цели (начального состояния прямой задачи)
            current_key = self._get_key(current)
            goal_key = self._get_key(goal_state)
            
            if current_key == goal_key:
                # Нашли путь! Инвертируем ходы для получения решения
                solution = self._invert_path(path)
                self.stats.solution_length = len(solution)
                self._log(f"Solution found: {len(solution)} moves (backward path: {len(path)})")
                self._log(f"Stats: {self.stats}")
                return solution
            
            # Генерируем обратные ходы
            reverse_moves = self._generate_reverse_moves(current)
            
            for reverse_move in reverse_moves:
                new_board = self._apply_reverse_move(current, reverse_move)
                new_key = self._get_key(new_board)
                
                # Пропускаем уже посещённые
                if new_key in visited:
                    continue
                
                # Проверяем, не превысили ли мы количество колышков в начальном состоянии
                if optimized_peg_count(new_board) > optimized_peg_count(goal_state):
                    continue
                
                visited[new_key] = path + [reverse_move]
                queue.append((new_board, path + [reverse_move]))
        
        self._log("No solution found")
        self._log(f"Stats: {self.stats}")
        return None
    
    def _generate_reverse_moves(self, board: BitBoard) -> List[Tuple[int, int, int]]:
        """
        Генерирует обратные ходы.
        
        Обратный ход: если прямой ход (from, jumped, to) удаляет from и jumped, создаёт to,
        то обратный ход создаёт from и jumped, удаляет to.
        
        Для обратного хода:
        - to_pos должна быть занята (колышек, который будет удалён)
        - jumped_pos должна быть свободна (будет создана)
        - from_pos должна быть свободна (будет создана)
        
        Args:
            board: текущее состояние доски
            
        Returns:
            Список обратных ходов (from, jumped, to)
        """
        reverse_moves = []
        pegs = board.pegs
        holes = board.valid_mask & ~pegs  # Свободные ячейки
        
        # Для каждой занятой ячейки (to) ищем возможные обратные ходы
        for to_pos in range(49):
            if not (pegs >> to_pos) & 1:
                continue  # Не занята
            if not (board.valid_mask >> to_pos) & 1:
                continue  # Не валидна
            
            r, c = divmod(to_pos, 7)
            
            # Проверяем все направления для обратных ходов
            directions = [
                ((-1, 0), (-2, 0)),  # Вверх
                ((1, 0), (2, 0)),     # Вниз
                ((0, -1), (0, -2)),   # Влево
                ((0, 1), (0, 2)),     # Вправо
            ]
            
            for (dr1, dc1), (dr2, dc2) in directions:
                jumped_r, jumped_c = r + dr1, c + dc1
                from_r, from_c = r + dr2, c + dc2
                
                if not (0 <= jumped_r < 7 and 0 <= jumped_c < 7):
                    continue
                if not (0 <= from_r < 7 and 0 <= from_c < 7):
                    continue
                
                jumped_pos = jumped_r * 7 + jumped_c
                from_pos = from_r * 7 + from_c
                
                # Проверяем валидность позиций
                if not (board.valid_mask >> jumped_pos) & 1:
                    continue
                if not (board.valid_mask >> from_pos) & 1:
                    continue
                
                # Обратный ход возможен, если:
                # - to_pos занята (уже проверили)
                # - jumped_pos свободна (будет создана)
                # - from_pos свободна (будет создана)
                if (holes >> jumped_pos) & 1 and (holes >> from_pos) & 1:
                    reverse_moves.append((from_pos, jumped_pos, to_pos))
        
        return reverse_moves
    
    def _apply_reverse_move(self, board: BitBoard, reverse_move: Tuple[int, int, int]) -> BitBoard:
        """
        Применяет обратный ход к доске.
        
        Обратный ход (from, jumped, to):
        - Создаёт колышки в from и jumped
        - Удаляет колышек из to
        
        Args:
            board: текущее состояние доски
            reverse_move: обратный ход (from, jumped, to)
            
        Returns:
            Новое состояние доски
        """
        from_pos, jumped_pos, to_pos = reverse_move
        
        # Создаём колышки в from и jumped, удаляем из to
        new_pegs = board.pegs
        new_pegs |= (1 << from_pos)
        new_pegs |= (1 << jumped_pos)
        new_pegs &= ~(1 << to_pos)
        
        return BitBoard(new_pegs, valid_mask=board.valid_mask)
    
    def _invert_path(self, reverse_path: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Инвертирует путь обратных ходов в прямой путь.
        
        Обратный ход (from, jumped, to) становится прямым ходом (from, jumped, to),
        но порядок ходов нужно развернуть.
        
        Args:
            reverse_path: путь обратных ходов
            
        Returns:
            Прямой путь ходов
        """
        # Обратные ходы уже в правильном формате (from, jumped, to)
        # Просто разворачиваем порядок
        return list(reversed(reverse_path))
