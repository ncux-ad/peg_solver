"""
solvers/governor.py

Governor (Диспетчер) — умный выбор алгоритма на основе анализа позиции.
"""

from typing import List, Tuple, Optional
import time

from .base import BaseSolver, SolverStats
from .dfs import DFSSolver
from .astar import AStarSolver, IDAStarSolver
from .beam import BeamSolver
from .pattern_astar import PatternAStarSolver
from core.bitboard import BitBoard, CENTER_POS
from heuristics import pagoda_value, PAGODA_WEIGHTS


class GovernorSolver(BaseSolver):
    """
    Governor решатель — анализирует позицию и выбирает оптимальный алгоритм.
    
    Критерии выбора:
    - Мало колышков (< 10) → DFS (быстрое исчерпывающее решение)
    - Средне колышков (10-20) → Beam Search или Pattern A* (баланс скорости/качества)
    - Много колышков (> 20) → Beam Search или IDA* (эффективность памяти)
    - Доступно много ходов → Beam Search (ширина важнее глубины)
    - Мало ходов → DFS или A* (нужна точность)
    - Сложная эвристика → Pattern A* (использует предвычисленные паттерны)
    """
    
    def __init__(self, verbose: bool = True, timeout: float = 120.0):
        super().__init__(use_symmetry=True, verbose=verbose)
        self.timeout = timeout
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """Анализирует позицию и выбирает лучший алгоритм."""
        self.stats = SolverStats()
        start_time = time.time()
        
        peg_count = board.peg_count()
        self._log(f"Governor: Analyzing position (pegs={peg_count})...")
        
        # Анализ позиции
        analysis = self._analyze_position(board)
        self._log(f"Analysis: {analysis}")
        
        # Выбор алгоритма
        chosen_solver = self._choose_solver(analysis)
        self._log(f"→ Chosen: {chosen_solver['name']} ({chosen_solver['reason']})")
        
        # Запуск выбранного алгоритма
        try:
            solution = chosen_solver['solver']().solve(board)
            
            if solution:
                self.stats.time_elapsed = time.time() - start_time
                self.stats.solution_length = len(solution)
                self._log(f"✓ Solution found: {len(solution)} moves in {self.stats.time_elapsed:.2f}s")
                return solution
            else:
                # Fallback: пробуем другие алгоритмы
                self._log("Primary solver failed, trying fallbacks...")
                return self._try_fallbacks(board, analysis, chosen_solver['name'], start_time)
                
        except Exception as e:
            self._log(f"✗ {chosen_solver['name']} failed: {e}")
            return self._try_fallbacks(board, analysis, chosen_solver['name'], start_time)
    
    def _analyze_position(self, board: BitBoard) -> dict:
        """Анализирует позицию и возвращает характеристики."""
        peg_count = board.peg_count()
        moves = board.get_moves()
        moves_count = len(moves)
        
        # Эвристические метрики
        pagoda = pagoda_value(board)
        center_dist = self._avg_distance_to_center(board)
        mobility = moves_count / max(peg_count, 1)  # Ходов на колышек
        
        # Оценка сложности
        # Больше колышков + меньше ходов = сложнее
        complexity = peg_count / max(moves_count, 1)
        
        return {
            'peg_count': peg_count,
            'moves_count': moves_count,
            'mobility': mobility,
            'pagoda': pagoda,
            'center_dist': center_dist,
            'complexity': complexity,
            'is_easy': peg_count < 10 and moves_count > 3,
            'is_medium': 10 <= peg_count <= 20,
            'is_hard': peg_count > 20 or moves_count < 2,
        }
    
    def _avg_distance_to_center(self, board: BitBoard) -> float:
        """Среднее расстояние колышков до центра."""
        if board.peg_count() == 0:
            return 0.0
        
        total_dist = 0
        count = 0
        
        for pos in range(49):  # 7x7
            if board.has_peg(pos):
                row, col = pos // 7, pos % 7
                dist = abs(row - 3) + abs(col - 3)
                total_dist += dist
                count += 1
        
        return total_dist / count if count > 0 else 0.0
    
    def _choose_solver(self, analysis: dict) -> dict:
        """
        Выбирает оптимальный алгоритм на основе анализа.
        
        Returns:
            dict с ключами: 'name', 'solver', 'reason'
        """
        peg_count = analysis['peg_count']
        moves_count = analysis['moves_count']
        mobility = analysis['mobility']
        is_easy = analysis['is_easy']
        is_hard = analysis['is_hard']
        
        # Мало колышков (< 10) → DFS (быстрое исчерпывающее решение)
        if peg_count < 10:
            return {
                'name': 'DFS',
                'solver': lambda: DFSSolver(verbose=False),
                'reason': f'Мало колышков ({peg_count}), DFS быстро найдёт решение'
            }
        
        # Очень много ходов → Beam Search (ширина важнее глубины)
        if mobility > 1.5:
            return {
                'name': 'Beam Search',
                'solver': lambda: BeamSolver(beam_width=300, verbose=False),
                'reason': f'Высокая мобильность ({mobility:.2f}), Beam Search эффективен'
            }
        
        # Средне колышков (10-20) → Pattern A* или Beam Search
        if analysis['is_medium']:
            # Если есть доступ к Pattern DB, используем Pattern A*
            try:
                from heuristics.pattern_db import PATTERN_DB_PATH
                import os
                if os.path.exists(PATTERN_DB_PATH):
                    return {
                        'name': 'Pattern A*',
                        'solver': lambda: PatternAStarSolver(verbose=False),
                        'reason': f'Средняя сложность ({peg_count} колышков), Pattern A* оптимален'
                    }
            except:
                pass
            
            return {
                'name': 'Beam Search',
                'solver': lambda: BeamSolver(beam_width=250, verbose=False),
                'reason': f'Средняя сложность ({peg_count} колышков), Beam Search'
            }
        
        # Много колышков (> 20) или сложная позиция
        if is_hard:
            # IDA* экономит память для сложных позиций
            if peg_count > 25:
                return {
                    'name': 'IDA*',
                    'solver': lambda: IDAStarSolver(verbose=False),
                    'reason': f'Сложная позиция ({peg_count} колышков), IDA* эффективен по памяти'
                }
            
            # Beam Search с широким лучом
            return {
                'name': 'Beam Search (wide)',
                'solver': lambda: BeamSolver(beam_width=400, verbose=False),
                'reason': f'Сложная позиция ({peg_count} колышков), широкий луч'
            }
        
        # По умолчанию: Beam Search (универсальный)
        return {
            'name': 'Beam Search',
            'solver': lambda: BeamSolver(beam_width=200, verbose=False),
            'reason': 'Универсальный выбор'
        }
    
    def _try_fallbacks(self, board: BitBoard, analysis: dict, failed_solver: str, start_time: float) -> Optional[List]:
        """Пробует альтернативные алгоритмы, если основной не сработал."""
        fallbacks = []
        
        # Формируем список fallback'ов
        if failed_solver != 'DFS':
            fallbacks.append(('DFS', lambda: DFSSolver(verbose=False)))
        
        if failed_solver not in ['Beam Search', 'Beam Search (wide)']:
            fallbacks.append(('Beam Search', lambda: BeamSolver(beam_width=300, verbose=False)))
        
        if failed_solver != 'IDA*':
            fallbacks.append(('IDA*', lambda: IDAStarSolver(verbose=False)))
        
        if failed_solver != 'Pattern A*':
            try:
                from heuristics.pattern_db import PATTERN_DB_PATH
                import os
                if os.path.exists(PATTERN_DB_PATH):
                    fallbacks.append(('Pattern A*', lambda: PatternAStarSolver(verbose=False)))
            except:
                pass
        
        # Пробуем fallback'и
        for name, solver_fn in fallbacks:
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                self._log(f"Timeout ({self.timeout}s)")
                return None
            
            self._log(f"Trying fallback: {name}...")
            
            try:
                solution = solver_fn().solve(board)
                if solution:
                    self.stats.time_elapsed = time.time() - start_time
                    self.stats.solution_length = len(solution)
                    self._log(f"✓ Found with {name}! ({len(solution)} moves, {self.stats.time_elapsed:.2f}s)")
                    return solution
            except Exception as e:
                self._log(f"✗ {name} failed: {e}")
        
        self.stats.time_elapsed = time.time() - start_time
        self._log(f"✗ No solution found ({self.stats.time_elapsed:.2f}s)")
        return None
