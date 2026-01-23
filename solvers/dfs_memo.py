"""
solvers/dfs_memo.py

DFS с мемоизацией - Фаза 2.1.
Улучшенная версия SimpleDFS с запоминанием неудачных состояний.
"""

from typing import List, Tuple, Optional, Set

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard, is_english_board, get_center_position, CENTER_POS
from heuristics.pagoda import pagoda_value, PAGODA_WEIGHTS


class DFSMemoSolver(BaseSolver):
    """
    DFS решатель с мемоизацией неудачных состояний.
    
    Особенности:
    - Запоминает состояния без решения (Dynamic Programming)
    - Опциональная сортировка ходов по эвристике
    - Опциональное использование симметрий
    - Без сложных оптимизаций (Pagoda, etc.) - это для следующих фаз
    
    Улучшения по сравнению с SimpleDFS:
    - Мемоизация предотвращает повторное исследование тупиков
    - Значительно ускоряет поиск на сложных позициях
    """
    
    def __init__(self, use_symmetry: bool = True, sort_moves: bool = True,
                 use_pagoda: bool = True, verbose: bool = False):
        """
        Args:
            use_symmetry: использовать канонические формы для мемоизации
            sort_moves: сортировать ходы по эвристике (ближе к центру = лучше)
            use_pagoda: использовать Pagoda pruning (только для английской доски)
            verbose: выводить отладочную информацию
        """
        super().__init__(use_symmetry=use_symmetry, verbose=verbose)
        self.sort_moves = sort_moves
        self.use_pagoda = use_pagoda
        self.memo: Set[int] = set()
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку DFS с мемоизацией.
        
        Args:
            board: начальная позиция
            
        Returns:
            Список ходов (from, jumped, to) или None если решение не найдено
        """
        self.stats = SolverStats()
        self.memo.clear()
        
        self._log(f"Starting DFS with memoization (pegs={board.peg_count()})")
        result = self._dfs(board, [])
        
        if result:
            self.stats.solution_length = len(result)
            self._log(f"Solution found: {len(result)} moves")
        else:
            self._log("No solution found")
        
        self._log(f"Stats: {self.stats}")
        return result
    
    def _dfs(self, board: BitBoard, path: List[Tuple[int, int, int]]) -> Optional[List[Tuple[int, int, int]]]:
        """
        Рекурсивный DFS поиск с мемоизацией.
        
        Args:
            board: текущее состояние доски
            path: путь ходов до текущего состояния
            
        Returns:
            Список ходов или None
        """
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Проверка победы: остался один колышек
        if board.peg_count() == 1:
            return path
        
        # Проверяем мемо: уже исследовали это состояние?
        key = self._get_key(board)
        if key in self.memo:
            self.stats.nodes_pruned += 1
            return None
        
        # Pagoda pruning (только для английской доски)
        if self.use_pagoda and is_english_board(board):
            try:
                current_pagoda = pagoda_value(board)
                min_pagoda = min(PAGODA_WEIGHTS.values())
                
                # Мягкая проверка: если pagoda слишком низкая, вероятно тупик
                if board.peg_count() > 15:
                    # В начале: строгая проверка (финал в центре - английская доска)
                    if current_pagoda < PAGODA_WEIGHTS.get(CENTER_POS, min_pagoda):
                        self.memo.add(key)
                        self.stats.nodes_pruned += 1
                        return None
                else:
                    # Ближе к концу: мягкая проверка (финал может быть где угодно)
                    if current_pagoda < min_pagoda:
                        self.memo.add(key)
                        self.stats.nodes_pruned += 1
                        return None
            except Exception:
                # Если Pagoda не работает, продолжаем без неё
                pass
        
        # Получаем все возможные ходы
        moves = board.get_moves()
        
        # Если нет ходов - тупик, запоминаем и возвращаем None
        if not moves:
            self.memo.add(key)
            return None
        
        # Опциональная сортировка ходов по эвристике
        if self.sort_moves:
            moves = self._sort_moves(board, moves)
        
        # Пробуем каждый ход
        for move in moves:
            new_board = board.apply_move(*move)
            result = self._dfs(new_board, path + [move])
            if result is not None:
                return result
        
        # Все ходы привели в тупик - запоминаем это состояние
        self.memo.add(key)
        return None
    
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
            """Вычисляет приоритет хода (меньше = лучше)."""
            _, jumped, to_pos = move
            to_r, to_c = to_pos // 7, to_pos % 7
            
            # Расстояние до центра
            if center_pos is not None:
                center_r, center_c = center_pos // 7, center_pos % 7
                center_dist = abs(to_r - center_r) + abs(to_c - center_c)
            else:
                # Если нет центра, используем расстояние до центра доски (3, 3)
                center_dist = abs(to_r - 3) + abs(to_c - 3)
            
            return center_dist
        
        return sorted(moves, key=priority)
