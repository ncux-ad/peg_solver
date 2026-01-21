"""
solvers/exhaustive.py

Exhaustive Search с оценкой промежуточных состояний.
Агрессивный поиск для сложных позиций.
"""

from typing import List, Tuple, Optional, Set, Dict
import time

from .base import BaseSolver, SolverStats
from core.bitboard import (
    BitBoard, CENTER_POS,
    is_english_board
)
from heuristics import pagoda_value, PAGODA_WEIGHTS
from heuristics.evaluation import evaluate_position


class ExhaustiveSolver(BaseSolver):
    """
    Exhaustive решатель с оценкой промежуточных состояний.
    
    Особенности:
    - Полный перебор всех возможных путей
    - Оценка каждого промежуточного состояния
    - Приоритизация путей с лучшей оценкой
    - Мягкий Pagoda pruning
    - Мемоизация для ускорения
    """
    
    def __init__(self, use_symmetry: bool = True, 
                 use_pagoda: bool = False,  # По умолчанию отключаем для сложных позиций
                 verbose: bool = False,
                 timeout: float = 600.0,
                 max_depth: int = 50):
        super().__init__(use_symmetry, verbose)
        self.use_pagoda = use_pagoda
        self.timeout = timeout
        self.max_depth = max_depth
        self.start_time = None
        self.memo: Dict[int, Optional[List]] = {}  # Кэш результатов
        self.best_paths: List[Tuple[float, List]] = []  # Лучшие пути с оценками
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """Запускает exhaustive search с оценкой."""
        self.stats = SolverStats()
        self.memo.clear()
        self.best_paths.clear()
        self.start_time = time.time()
        
        peg_count = board.peg_count()
        self._log(f"Starting Exhaustive Search (pegs={peg_count}, timeout={self.timeout}s, max_depth={self.max_depth})")
        
        # Мягкая проверка Pagoda (только для английской доски)
        if self.use_pagoda and is_english_board(board):
            min_pagoda = min(PAGODA_WEIGHTS.values())
            current_pagoda = pagoda_value(board)
            
            if current_pagoda < min_pagoda:
                self._log(f"Warning: Low Pagoda ({current_pagoda} < {min_pagoda}), but continuing...")
        
        result = self._exhaustive_search(board, [])
        
        elapsed = time.time() - self.start_time
        self.stats.time_elapsed = elapsed
        
        if result:
            self.stats.solution_length = len(result)
            self._log(f"✓ Solution found! ({len(result)} moves, {elapsed:.2f}s, {self.stats.nodes_visited} nodes)")
        else:
            self._log(f"✗ No solution found ({elapsed:.2f}s, {self.stats.nodes_visited} nodes, {self.stats.nodes_pruned} pruned)")
        
        return result
    
    def _exhaustive_search(self, board: BitBoard, path: List[Tuple[int, int, int]]) -> Optional[List]:
        """Рекурсивный exhaustive search с оценкой."""
        # Проверка timeout
        if time.time() - self.start_time > self.timeout:
            return None
        
        # Проверка глубины
        if len(path) >= self.max_depth:
            return None
        
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Победа
        if board.peg_count() == 1:
            self.stats.solution_length = len(path)
            return path
        
        # Проверяем мемо
        key = self._get_key(board)
        if key in self.memo:
            result = self.memo[key]
            if result is None:
                self.stats.nodes_pruned += 1
            return result
        
        # Мягкий Pagoda pruning (только для английской доски)
        if self.use_pagoda and is_english_board(board):
            min_pagoda = min(PAGODA_WEIGHTS.values())
            current_pagoda = pagoda_value(board)
            
            # Очень мягкая проверка - только если очень далеко от минимума
            if current_pagoda < min_pagoda - 10:  # Допускаем значительное отклонение для сложных позиций
                self.memo[key] = None
                self.stats.nodes_pruned += 1
                return None
        
        # Получаем ходы
        moves = board.get_moves()
        if not moves:
            self.memo[key] = None
            return None
        
        # Оцениваем каждый ход и сортируем по приоритету
        move_scores = []
        for move in moves:
            # Применяем ход для оценки
            from_pos, jumped, to_pos = move
            new_board = board.apply_move(from_pos, jumped, to_pos)
            
            # Оценка позиции после хода
            peg_count = new_board.peg_count()
            num_moves = len(new_board.get_moves())
            score = evaluate_position(new_board, num_moves)
            
            # Приоритет: меньше оценка = лучше (evaluate_position возвращает меньше = лучше)
            # Также учитываем количество колышков (меньше = ближе к цели)
            priority = -score - (peg_count * 0.1)  # Инвертируем, т.к. меньше = лучше
            
            move_scores.append((priority, move, new_board))
        
        # Сортируем по приоритету (лучшие первыми)
        move_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Пробуем ходы в порядке приоритета
        for priority, move, new_board in move_scores:
            new_path = path + [move]
            
            # Рекурсивный поиск
            result = self._exhaustive_search(new_board, new_path)
            
            if result is not None:
                self.memo[key] = result
                return result
        
        # Все пути не привели к решению
        self.memo[key] = None
        return None
    
    def _get_key(self, board: BitBoard) -> int:
        """Получает ключ для мемоизации."""
        if self.use_symmetry:
            return board.canonical().pegs
        return board.pegs
