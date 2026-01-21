"""
solvers/lookup.py

Решатель с использованием известных решений (lookup table).
Использует канонические формы для поиска эквивалентных позиций.
"""

from typing import List, Tuple, Optional, Dict
import os
import json
import pickle

from .base import BaseSolver, SolverStats
from core.bitboard import (
    BitBoard, ENGLISH_START, ENGLISH_GOAL,
    is_english_board
)
from solvers.beam import BeamSolver
from solvers.dfs import DFSSolver


class LookupSolver(BaseSolver):
    """
    Решатель с lookup table известных решений.
    
    Особенности:
    - Проверяет базу известных решений
    - Использует каноническую форму для поиска эквивалентных позиций
    - Использует опорные точки (waypoints) для ускорения
    - Fallback на обычные решатели если решения нет в базе
    """
    
    def __init__(self, solutions_db_path: str = "known_solutions.pkl",
                 use_fallback: bool = True, verbose: bool = False):
        super().__init__(use_symmetry=True, verbose=verbose)
        self.solutions_db_path = solutions_db_path
        self.use_fallback = use_fallback
        self.solutions_db: Dict[int, List[Tuple[int, int, int]]] = {}
        self.waypoints_db: Dict[int, Dict] = {}  # {canonical_pegs: {'from': path, 'to': path}}
        
        self._load_solutions()
        self._build_waypoints()
    
    def _load_solutions(self):
        """Загружает базу известных решений."""
        if os.path.exists(self.solutions_db_path):
            try:
                with open(self.solutions_db_path, 'rb') as f:
                    self.solutions_db = pickle.load(f)
                self._log(f"Loaded {len(self.solutions_db)} known solutions")
            except Exception as e:
                self._log(f"Failed to load solutions DB: {e}")
        
        # Добавляем известное решение английской доски
        self._add_english_solution()
    
    def _add_english_solution(self):
        """Добавляет известное решение английской доски."""
        try:
            from solutions.english_solutions import get_cached_solution
            
            solution = get_cached_solution()
            if solution:
                # Сохраняем для ENGLISH_START
                canonical = BitBoard(ENGLISH_START).canonical()
                self.solutions_db[canonical.pegs] = solution
                self._log(f"Added English board solution ({len(solution)} moves)")
        except Exception as e:
            self._log(f"Could not load English solution: {e}")
    
    def _build_waypoints(self):
        """Строит базу опорных точек из известных решений."""
        for start_pegs, solution in self.solutions_db.items():
            board = BitBoard(start_pegs)
            state = start_pegs
            path = []
            
            # Опорные точки каждые 5-7 ходов
            waypoint_interval = max(5, len(solution) // 10)
            
            for i, move in enumerate(solution):
                path.append(move)
                state = board.apply_move(*move).pegs
                board = BitBoard(state)
                
                if (i + 1) % waypoint_interval == 0 or i == len(solution) - 1:
                    canonical = board.canonical()
                    if canonical.pegs not in self.waypoints_db:
                        self.waypoints_db[canonical.pegs] = {
                            'from_start': path[:],
                            'to_goal': solution[i+1:] if i + 1 < len(solution) else []
                        }
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """Решает используя lookup table или fallback."""
        self.stats = SolverStats()
        
        # Проверяем точное совпадение
        exact_match = self._check_exact_match(board)
        if exact_match:
            self._log(f"Exact match found in DB: {len(exact_match)} moves")
            self.stats.solution_length = len(exact_match)
            return exact_match
        
        # Проверяем каноническую форму
        canonical_match = self._check_canonical_match(board)
        if canonical_match:
            self._log(f"Canonical match found in DB: {len(canonical_match)} moves")
            self.stats.solution_length = len(canonical_match)
            return canonical_match
        
        # Проверяем опорные точки (waypoints)
        waypoint_solution = self._check_waypoints(board)
        if waypoint_solution:
            self._log(f"Waypoint solution found: {len(waypoint_solution)} moves")
            self.stats.solution_length = len(waypoint_solution)
            return waypoint_solution
        
        # Fallback на обычные решатели
        if self.use_fallback:
            self._log("No match in DB, using fallback solver...")
            return self._fallback_solve(board)
        
        return None
    
    def _check_exact_match(self, board: BitBoard) -> Optional[List]:
        """Проверяет точное совпадение позиции."""
        if board.pegs in self.solutions_db:
            return self.solutions_db[board.pegs]
        return None
    
    def _check_canonical_match(self, board: BitBoard) -> Optional[List]:
        """Проверяет совпадение канонической формы (только для английской доски)."""
        # Для произвольных досок canonical() возвращает доску как есть,
        # поэтому проверяем только если это английская доска
        if not is_english_board(board):
            return None
        
        canonical = board.canonical()
        
        if canonical.pegs in self.solutions_db:
            # Нужно трансформировать решение обратно
            solution = self.solutions_db[canonical.pegs]
            return self._transform_solution(board, canonical, solution)
        
        return None
    
    def _transform_solution(self, original: BitBoard, canonical: BitBoard, 
                           solution: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Трансформирует решение из канонической формы обратно к оригинальной.
        Пока возвращает решение как есть (упрощённо).
        TODO: Реализовать обратную трансформацию симметрий.
        """
        # Упрощённая версия - если канонические формы совпадают, используем решение
        if original.canonical().pegs == canonical.pegs:
            return solution
        return solution  # TODO: полная трансформация
    
    def _check_waypoints(self, board: BitBoard) -> Optional[List]:
        """Проверяет опорные точки (waypoints) - только для английской доски."""
        # Для произвольных досок waypoints не применимы
        if not is_english_board(board):
            return None
        
        canonical = board.canonical()
        
        if canonical.pegs in self.waypoints_db:
            waypoint = self.waypoints_db[canonical.pegs]
            # TODO: Построить полное решение от start через waypoint к goal
            # Пока возвращаем None (нужно достроить путь)
            pass
        
        return None
    
    def _fallback_solve(self, board: BitBoard) -> Optional[List]:
        """Fallback на обычные решатели."""
        # Используем Beam Search (быстрый)
        fallback = BeamSolver(beam_width=500, max_depth=35, verbose=False)
        solution = fallback.solve(board)
        
        if solution:
            # Сохраняем в базу для будущего использования
            # Для произвольных досок используем pegs напрямую (без canonical)
            # Для английской доски используем canonical
            if is_english_board(board):
                canonical = board.canonical()
                key = canonical.pegs
            else:
                key = board.pegs
            self.solutions_db[key] = solution
            self._save_solutions()
            self._log(f"Solution found by fallback and saved to DB")
        
        return solution
    
    def add_solution(self, board: BitBoard, solution: List[Tuple[int, int, int]]):
        """Добавляет решение в базу."""
        # Для произвольных досок используем pegs напрямую (без canonical)
        # Для английской доски используем canonical
        if is_english_board(board):
            canonical = board.canonical()
            key = canonical.pegs
        else:
            key = board.pegs
        self.solutions_db[key] = solution
        self._save_solutions()
        # Пересобираем waypoints только для английской доски
        if is_english_board(board):
            self._build_waypoints()
    
    def _save_solutions(self):
        """Сохраняет базу решений."""
        try:
            with open(self.solutions_db_path, 'wb') as f:
                pickle.dump(self.solutions_db, f)
        except Exception as e:
            self._log(f"Failed to save solutions DB: {e}")


# =====================================================
# ПРЕДЗАГРУЗКА ИЗВЕСТНЫХ РЕШЕНИЙ
# =====================================================

def build_initial_solutions_db():
    """Создаёт начальную базу известных решений."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from solutions.english_solutions import get_cached_solution, compute_english_solution
        
        db_path = "known_solutions.pkl"
        solver = LookupSolver(solutions_db_path=db_path, use_fallback=False, verbose=True)
        
        # Добавляем английскую доску
        board = BitBoard.english_start()
        solution = get_cached_solution()
        
        if not solution:
            # Если нет кэша, вычисляем
            solution = compute_english_solution()
        
        if solution:
            solver.add_solution(board, solution)
            print(f"Added English board solution: {len(solution)} moves")
        
        # Можно добавить другие известные решения
        # TODO: Загрузить из внешних источников
        
        return solver
    except Exception as e:
        print(f"Failed to build solutions DB: {e}")
        return None


if __name__ == "__main__":
    print("Building initial solutions database...")
    solver = build_initial_solutions_db()
    print(f"Database contains {len(solver.solutions_db)} solutions")
