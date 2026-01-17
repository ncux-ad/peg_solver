"""
solvers/brute_force.py

Brute Force решатель - максимально агрессивный поиск без pruning.
Используется только для самых сложных позиций, когда все остальные методы не работают.
"""

from typing import List, Tuple, Optional, Dict
import time

from .base import BaseSolver, SolverStats
from core.bitboard import BitBoard
from heuristics.evaluation import evaluate_position


class BruteForceSolver(BaseSolver):
    """
    Brute Force решатель - полный перебор БЕЗ Pagoda pruning.
    
    Особенности:
    - Полный перебор всех возможных путей
    - Оценка каждого промежуточного состояния
    - Приоритизация путей с лучшей оценкой
    - БЕЗ Pagoda pruning (только проверка на тупики)
    - Мемоизация для ускорения
    - Может работать очень долго для сложных позиций
    """
    
    def __init__(self, use_symmetry: bool = True, 
                 verbose: bool = False,
                 timeout: float = 3600.0,  # 1 час по умолчанию
                 max_depth: int = 50,
                 use_prioritization: bool = True,  # Отключить приоритизацию для полного перебора
                 use_memoization: bool = True):  # Отключить мемоизацию для полного перебора
        super().__init__(use_symmetry, verbose)
        self.timeout = timeout
        self.max_depth = max_depth
        self.use_prioritization = use_prioritization
        self.use_memoization = use_memoization
        self.start_time = None
        self.memo: Dict[int, Optional[List]] = {}  # Кэш результатов
        self.last_progress_log = 0.0  # Время последнего логирования прогресса
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """Запускает brute force search."""
        self.stats = SolverStats()
        self.memo.clear()
        self.start_time = time.time()
        self.last_progress_log = 0.0
        
        peg_count = board.peg_count()
        # Всегда выводим важные сообщения
        print(f"[BruteForce] Starting (pegs={peg_count}, timeout={self.timeout}s, max_depth={self.max_depth})")
        self._log(f"Starting Brute Force Search (pegs={peg_count}, timeout={self.timeout}s, max_depth={self.max_depth})")
        self._log(f"⚠️  WARNING: No Pagoda pruning - this may take a VERY long time!")
        
        result = self._brute_force_search(board, [])
        
        elapsed = time.time() - self.start_time
        self.stats.time_elapsed = elapsed
        
        if result:
            self.stats.solution_length = len(result)
            print(f"[BruteForce] ✓ Solution found! ({len(result)} moves, {elapsed:.2f}s, {self.stats.nodes_visited} nodes)")
            self._log(f"✓ Solution found! ({len(result)} moves, {elapsed:.2f}s, {self.stats.nodes_visited} nodes)")
        else:
            print(f"[BruteForce] ✗ No solution ({elapsed:.2f}s/{self.timeout}s, nodes={self.stats.nodes_visited}, pruned={self.stats.nodes_pruned}, max_depth={self.stats.max_depth}, memo={len(self.memo)})")
            self._log(f"✗ No solution found ({elapsed:.2f}s из {self.timeout}s, {self.stats.nodes_visited} nodes, {self.stats.nodes_pruned} pruned, max_depth={self.stats.max_depth})")
            if elapsed < self.timeout:
                print(f"[BruteForce] ⚠️  Stopped early! Possible reasons: max_depth={self.max_depth} reached or all paths exhausted")
                self._log(f"⚠️  Brute Force прервался раньше timeout! Работал {elapsed:.2f}s из {self.timeout}s")
                self._log(f"   Возможные причины: достигнут max_depth={self.max_depth} или исчерпаны все пути")
        
        return result
    
    def _brute_force_search(self, board: BitBoard, path: List[Tuple[int, int, int]]) -> Optional[List]:
        """Рекурсивный brute force search БЕЗ Pagoda pruning."""
        # Проверка timeout
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout:
            if len(path) == 0:  # Логируем только на верхнем уровне, чтобы не спамить
                self._log(f"⏱️  Timeout reached: {elapsed:.2f}s >= {self.timeout}s")
            return None
        
        # Периодическое логирование прогресса (каждые 30 секунд)
        if len(path) == 0 and elapsed - self.last_progress_log >= 30.0:
            self.last_progress_log = elapsed
            msg = f"[BruteForce] ⏳ Progress: {elapsed:.1f}s/{self.timeout:.1f}s, nodes={self.stats.nodes_visited}, depth={self.stats.max_depth}, memo={len(self.memo)}"
            print(msg)
            self._log(f"⏳ Progress: {elapsed:.1f}s / {self.timeout:.1f}s, nodes={self.stats.nodes_visited}, depth={self.stats.max_depth}, memo={len(self.memo)}")
        
        # Проверка глубины
        if len(path) >= self.max_depth:
            if len(path) == self.max_depth:  # Логируем только когда достигли лимита
                print(f"[BruteForce] 📏 Max depth reached: {len(path)} >= {self.max_depth} (pegs={board.peg_count()}, remaining_moves={len(board.get_moves())})")
                self._log(f"📏 Max depth reached: {len(path)} >= {self.max_depth}")
            return None
        
        self.stats.nodes_visited += 1
        self.stats.max_depth = max(self.stats.max_depth, len(path))
        
        # Победа
        if board.peg_count() == 1:
            self.stats.solution_length = len(path)
            return path
        
        # Проверяем мемо (если включено)
        if self.use_memoization:
            key = self._get_key(board)
            if key in self.memo:
                result = self.memo[key]
                if result is None:
                    self.stats.nodes_pruned += 1
                    # Логируем только на верхнем уровне для статистики
                    if len(path) == 0:
                        print(f"[BruteForce] Memo hit (pruned): {self.stats.nodes_pruned} nodes pruned so far")
                return result
        
        # Получаем ходы
        moves = board.get_moves()
        if not moves:
            # Тупик - нет ходов
            if self.use_memoization:
                key = self._get_key(board)
                self.memo[key] = None
            return None
        
        # Оцениваем каждый ход и сортируем по приоритету (если включено)
        if self.use_prioritization:
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
                # Также учитываем:
                # - Количество колышков (меньше = ближе к цели)
                # - Количество доступных ходов (больше = лучше, больше вариантов)
                # - Расстояние до центра (ближе = лучше)
                priority = -score - (peg_count * 0.1) + (num_moves * 0.05)  # Больше ходов = лучше
                
                # Бонус за ходы, которые ведут к позициям с большим количеством ходов
                if num_moves > 0:
                    priority += 0.1
                
                move_scores.append((priority, move, new_board))
            
            # Сортируем по приоритету (лучшие первыми)
            move_scores.sort(key=lambda x: x[0], reverse=True)
            moves_to_try = [(None, move, board.apply_move(*move)) for _, move, _ in move_scores]
        else:
            # Без приоритизации - пробуем ходы в исходном порядке
            moves_to_try = [(None, move, board.apply_move(*move)) for move in moves]
        
        # Пробуем ходы
        for priority, move, new_board in moves_to_try:
            new_path = path + [move]
            
            # Рекурсивный поиск
            result = self._brute_force_search(new_board, new_path)
            
            if result is not None:
                if self.use_memoization:
                    self.memo[key] = result
                return result
        
        # Все пути не привели к решению
        if self.use_memoization:
            key = self._get_key(board)
            self.memo[key] = None
        
        # Логируем только на верхнем уровне, если исчерпаны все пути
        if len(path) == 0:
            elapsed = time.time() - self.start_time
            if elapsed < self.timeout:
                print(f"[BruteForce] 🔍 All paths exhausted: visited {self.stats.nodes_visited} nodes, max_depth={self.stats.max_depth}, memo_size={len(self.memo)}, pruned={self.stats.nodes_pruned}")
                self._log(f"🔍 All paths exhausted: visited {self.stats.nodes_visited} nodes, max_depth={self.stats.max_depth}, memo_size={len(self.memo)}")
        
        return None
    
    def _get_key(self, board: BitBoard) -> int:
        """Получает ключ для мемоизации."""
        if self.use_symmetry:
            return board.canonical().pegs
        return board.pegs
