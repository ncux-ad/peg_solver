"""
solvers/sequential.py

SequentialSolver — систематический перебор решателей от простых к сложным.
Пробует решатели в порядке увеличения сложности до получения легального решения.
"""

from typing import List, Tuple, Optional
import time

from .base import BaseSolver, SolverStats
from .lookup import LookupSolver
from .dfs import DFSSolver
from .zobrist_dfs import ZobristDFSSolver
from .beam import BeamSolver
from .astar import AStarSolver, IDAStarSolver
from .pattern_astar import PatternAStarSolver
from .bidirectional import BidirectionalSolver
from .parallel import ParallelSolver
from .parallel_beam import ParallelBeamSolver
from core.bitboard import (
    BitBoard, CENTER_POS,
    is_english_board
)
from heuristics import pagoda_value, PAGODA_WEIGHTS


class SequentialSolver(BaseSolver):
    """
    Sequential решатель — систематический перебор от простых к сложным.
    
    Порядок перебора (от простых к сложным):
    1. Lookup (база решений) - мгновенно для известных позиций
    2. DFS (полный) - для маленьких позиций (<10 колышков)
    3. Beam Search (быстрый) - для универсального использования
    4. Zobrist DFS (глубокий поиск) - для сложных позиций
    5. A* (эвристический) - для средних позиций
    6. Pattern A* (оптимизированный A*) - для сложных позиций
    7. IDA* (экономия памяти) - для очень сложных позиций
    8. Bidirectional (двунаправленный) - для ускоренного поиска
    9. Parallel DFS (многопоточный) - для глубоких позиций
    10. Parallel Beam (многопоточный) - для больших позиций
    
    Продолжает перебор до получения легального (победного) решения.
    """
    
    def __init__(self, timeout: float = 300.0, verbose: bool = True, 
                 max_depth_unlimited: int = None, max_iterations: int = 10000000):
        super().__init__(use_symmetry=True, verbose=verbose)
        self.timeout = timeout
        self.max_depth_unlimited = max_depth_unlimited or 1000
        self.max_iterations = max_iterations
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Систематический перебор решателей от простых к сложным.
        
        Возвращает первое найденное легальное решение.
        """
        self.stats = SolverStats()
        start_time = time.time()
        
        peg_count = board.peg_count()
        self._log(f"Starting Sequential Solver (pegs={peg_count}, timeout={self.timeout}s)")
        self._log("Перебор решателей от простых к сложным до получения решения...")
        
        # Мягкая проверка Pagoda (только для английской доски)
        if is_english_board(board):
            min_pagoda = min(PAGODA_WEIGHTS.values())
            current_pagoda = pagoda_value(board)
            
            if current_pagoda < min_pagoda:
                self._log(f"Warning: Low Pagoda value ({current_pagoda} < {min_pagoda}), but continuing...")
        
        # Новая стратегия на основе результатов: Beam для небольших досок, DFS для остальных
        # Определяем последовательность решателей от простых к сложным
        peg_count = board.peg_count()
        
        if peg_count < 10:
            # Небольшие доски: Lookup → Beam → DFS
            strategies = [
                # 1. Lookup (самый быстрый для известных позиций)
                ("Lookup", lambda: LookupSolver(use_fallback=False, verbose=False).solve(board)),
                
                # 2. Beam Search (показал лучшие результаты для небольших досок)
                ("Beam Search", lambda: BeamSolver(beam_width=500, max_depth=50, verbose=False).solve(board)),
                
                # 3. DFS (надёжный fallback)
                ("DFS", lambda: DFSSolver(verbose=False, use_pagoda=False).solve(board)),
            ]
        else:
            # Большие доски: Lookup → DFS → Beam
            strategies = [
                # 1. Lookup (самый быстрый для известных позиций)
                ("Lookup", lambda: LookupSolver(use_fallback=False, verbose=False).solve(board)),
                
                # 2. DFS (показал лучшие результаты для больших досок)
                ("DFS", lambda: DFSSolver(verbose=False, use_pagoda=False).solve(board)),
                
                # 3. Beam Search (быстрый fallback)
                ("Beam Search", lambda: BeamSolver(beam_width=500, max_depth=50, verbose=False).solve(board)),
            ]
        
        # Добавляем дополнительные решатели только если основные не сработали
        # Упрощённый список - убрали неэффективные решатели
        additional_strategies = [
            # 4. Zobrist DFS (оптимизированный DFS)
            ("Zobrist DFS", lambda: ZobristDFSSolver(verbose=False, use_pagoda=False).solve(board)),
            
            # 5. A* (эвристический, полный)
            ("A*", lambda: AStarSolver(verbose=False).solve(board)),
            
            # 6. IDA* (экономия памяти)
            ("IDA*", lambda: IDAStarSolver(max_depth=self.max_depth_unlimited, verbose=False).solve(board)),
        ]
        
        # Объединяем основные и дополнительные стратегии
        strategies = strategies + additional_strategies
        
        # Перебираем решатели последовательно
        for idx, (name, solver_fn) in enumerate(strategies, 1):
            # Проверяем timeout перед каждым решателем (кроме Brute Force - он всегда получает время)
            elapsed = time.time() - start_time
            if name != "Brute Force" and elapsed > self.timeout:
                self._log(f"Timeout ({self.timeout}s) достигнут, пропускаем {name}")
                continue  # Пропускаем этот решатель, но продолжаем для Brute Force
            
            # Для Brute Force всегда даём шанс, даже если timeout превышен
            if name == "Brute Force" and elapsed > self.timeout:
                self._log(f"Timeout ({self.timeout}s) достигнут, но даём Brute Force шанс (минимум 1 час)")
            
            self._log(f"[{idx}/{len(strategies)}] Пробуем {name}...")
            
            try:
                solver_start = time.time()
                result = solver_fn()
                solver_elapsed = time.time() - solver_start
                
                if result is not None:
                    # Для Lookup не валидируем - он возвращает только валидные решения из базы
                    if name == "Lookup":
                        if result:
                            self.stats.time_elapsed = time.time() - start_time
                            self.stats.solution_length = len(result)
                            self._log(f"✓ Решение найдено с {name}! ({len(result)} ходов, {solver_elapsed:.2f}s, всего {self.stats.time_elapsed:.2f}s)")
                            return result
                        else:
                            self._log(f"✗ {name} не нашёл решение ({solver_elapsed:.2f}s)")
                    # Для остальных решателей проверяем валидность
                    elif self._validate_solution(board, result):
                        self.stats.time_elapsed = time.time() - start_time
                        self.stats.solution_length = len(result)
                        self._log(f"✓ Решение найдено с {name}! ({len(result)} ходов, {solver_elapsed:.2f}s, всего {self.stats.time_elapsed:.2f}s)")
                        return result
                    else:
                        self._log(f"✗ {name} вернул нелегальное решение, продолжаем...")
                else:
                    self._log(f"✗ {name} не нашёл решение ({solver_elapsed:.2f}s)")
                    
            except Exception as e:
                self._log(f"✗ {name} завершился с ошибкой: {e}")
                continue
        
        # Все решатели попробованы, решения не найдено
        self.stats.time_elapsed = time.time() - start_time
        self._log(f"✗ Решение не найдено после перебора всех {len(strategies)} решателей ({self.stats.time_elapsed:.2f}s)")
        self._log(f"Общее время: {self.stats.time_elapsed:.2f}s, timeout был: {self.timeout}s")
        return None
    
    def _validate_solution(self, initial_board: BitBoard, solution: List[Tuple[int, int, int]]) -> bool:
        """
        Проверяет, что решение легальное (приводит к победному состоянию - 1 колышек).
        
        Args:
            initial_board: начальная доска
            solution: список ходов
        
        Returns:
            True если решение валидное и приводит к победному состоянию
        """
        try:
            current_board = initial_board
            for move in solution:
                current_board = current_board.apply_move(*move)
            
            # Проверяем, что остался ровно 1 колышек (победное состояние)
            return current_board.peg_count() == 1
        except Exception as e:
            self._log(f"Ошибка валидации решения: {e}")
            return False
