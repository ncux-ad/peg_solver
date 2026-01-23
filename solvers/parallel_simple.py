"""
solvers/parallel_simple.py

Parallel DFS решатель - Фаза 3.4.
Многопоточный поиск для ускорения решения.
"""

from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard
from .simple_dfs import SimpleDFSSolver


class ParallelSimpleSolver(BaseSolver):
    """
    Параллельный DFS решатель.
    
    Особенности:
    - Распределяет первые ходы между потоками
    - Каждый поток ищет решение независимо
    - Первое найденное решение возвращается
    - Ускоряет поиск на многоядерных системах
    
    Алгоритм:
    1. Генерируем все возможные первые ходы
    2. Каждый ход запускается в отдельном потоке
    3. Первый поток, нашедший решение, возвращает его
    4. Остальные потоки отменяются
    """
    
    def __init__(self, num_workers: int = 4, use_symmetry: bool = True,
                 verbose: bool = False):
        """
        Args:
            num_workers: количество рабочих потоков
            use_symmetry: использовать канонические формы
            verbose: выводить отладочную информацию
        """
        super().__init__(use_symmetry=use_symmetry, verbose=verbose)
        self.num_workers = num_workers
        self._solution_found = threading.Event()
        self._result_lock = threading.Lock()
        self._result: Optional[List[Tuple[int, int, int]]] = None
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку параллельным DFS.
        
        Args:
            board: начальная позиция
            
        Returns:
            Список ходов (from, jumped, to) или None если решение не найдено
        """
        self.stats = SolverStats()
        self._solution_found.clear()
        self._result = None
        
        # Получаем все возможные первые ходы
        moves = board.get_moves()
        if not moves:
            return None
        
        self._log(f"Starting Parallel DFS (workers={self.num_workers}, first_moves={len(moves)})")
        
        # Запускаем поиск в параллельных потоках
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {}
            
            for move in moves:
                if self._solution_found.is_set():
                    break
                
                future = executor.submit(self._solve_subtree, board, move)
                futures[future] = move
            
            # Ждём первое решение
            for future in as_completed(futures):
                if self._solution_found.is_set():
                    break
                
                try:
                    result = future.result(timeout=None)
                    if result is not None:
                        with self._result_lock:
                            if self._result is None:
                                self._result = result
                                self._solution_found.set()
                                self.stats.solution_length = len(result)
                                self._log(f"Solution found: {len(result)} moves")
                                self._log(f"Stats: {self.stats}")
                                return result
                except Exception as e:
                    self._log(f"Error in worker: {e}")
        
        if self._result is not None:
            return self._result
        
        self._log("No solution found")
        self._log(f"Stats: {self.stats}")
        return None
    
    def _solve_subtree(self, board: BitBoard, first_move: Tuple[int, int, int]) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает поддерево, начиная с первого хода.
        
        Args:
            board: начальная позиция
            first_move: первый ход для исследования
            
        Returns:
            Решение или None
        """
        # Проверяем, не найдено ли уже решение
        if self._solution_found.is_set():
            return None
        
        # Применяем первый ход
        new_board = board.apply_move(*first_move)
        self.stats.nodes_visited += 1
        
        # Используем SimpleDFS для поиска в поддереве
        solver = SimpleDFSSolver(verbose=False)
        result = solver.solve(new_board)
        
        # Обновляем статистику
        self.stats.nodes_visited += solver.stats.nodes_visited
        self.stats.max_depth = max(self.stats.max_depth, solver.stats.max_depth + 1)
        
        if result is not None:
            return [first_move] + result
        
        return None
