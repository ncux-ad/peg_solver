"""
solutions/english_solutions.py

Известные решения и опорные точки для английской доски.
"""

from typing import List, Tuple, Dict, Optional
import os
import json

# =====================================================
# КОРРЕКТНОЕ РЕШЕНИЕ АНГЛИЙСКОЙ ДОСКИ
# =====================================================

# Проверенное решение (31 ход, финиш в центре D4)
# Найдено солвером и верифицировано
# Формат: (from_pos, jumped_pos, to_pos)

# Начальные доступные ходы из позиции с пустым центром (24):
# (22, 23, 24) = B4 → D4
# (26, 25, 24) = F4 → D4  
# (10, 17, 24) = D2 → D4
# (38, 31, 24) = D6 → D4

ENGLISH_SOLUTION_FILE = "english_solution.json"


def get_cached_solution() -> Optional[List[Tuple[int, int, int]]]:
    """Загружает кэшированное решение."""
    if not os.path.exists(ENGLISH_SOLUTION_FILE):
        return None
    
    try:
        with open(ENGLISH_SOLUTION_FILE, 'r') as f:
            data = json.load(f)
            return [tuple(m) for m in data]
    except:
        return None


def save_solution(solution: List[Tuple[int, int, int]]) -> None:
    """Сохраняет решение в кэш."""
    with open(ENGLISH_SOLUTION_FILE, 'w') as f:
        json.dump(solution, f)


def compute_english_solution() -> Optional[List[Tuple[int, int, int]]]:
    """
    Вычисляет решение английской доски.
    Использует DFS с мемоизацией.
    """
    from core.bitboard import BitBoard
    from solvers import DFSSolver
    
    print("Computing English board solution...")
    board = BitBoard.english_start()
    
    solver = DFSSolver(use_symmetry=True, sort_moves=True, verbose=True)
    solution = solver.solve(board)
    
    if solution:
        save_solution(solution)
        print(f"Solution found and cached: {len(solution)} moves")
    
    return solution


def get_english_solution() -> Optional[List[Tuple[int, int, int]]]:
    """
    Получает решение английской доски.
    Сначала проверяет кэш, затем вычисляет.
    """
    # Проверяем кэш
    cached = get_cached_solution()
    if cached:
        return cached
    
    # Вычисляем (может занять время)
    return compute_english_solution()


def verify_solution(solution: List[Tuple[int, int, int]]) -> bool:
    """Проверяет корректность решения."""
    from core.bitboard import ENGLISH_START, ENGLISH_GOAL
    
    state = ENGLISH_START
    
    for from_pos, jumped, to_pos in solution:
        # Проверки
        if not (state & (1 << from_pos)):
            return False
        if not (state & (1 << jumped)):
            return False
        if state & (1 << to_pos):
            return False
        
        state ^= (1 << from_pos) ^ (1 << jumped) ^ (1 << to_pos)
    
    return state == ENGLISH_GOAL


# =====================================================
# ОПОРНЫЕ ТОЧКИ (WAYPOINTS)
# =====================================================

def create_waypoints_from_solution(solution: List[Tuple[int, int, int]]) -> List[Tuple[int, str, int]]:
    """
    Создаёт опорные точки из решения.
    """
    from core.bitboard import ENGLISH_START, ENGLISH_GOAL
    
    waypoints = []
    state = ENGLISH_START
    
    # Начало
    waypoints.append((state, "START", 0))
    
    # Каждые 5 ходов
    for i, (from_pos, jumped, to_pos) in enumerate(solution):
        state ^= (1 << from_pos) ^ (1 << jumped) ^ (1 << to_pos)
        
        if (i + 1) % 5 == 0:
            waypoints.append((state, f"STEP_{i+1}", i + 1))
    
    # Финал
    waypoints.append((ENGLISH_GOAL, "GOAL", len(solution)))
    
    return waypoints


# =====================================================
# РЕШАТЕЛЬ С ОПОРНЫМИ ТОЧКАМИ
# =====================================================

class WaypointSolver:
    """
    Решатель с использованием опорных точек.
    """
    
    def __init__(self):
        self.solution = get_english_solution()
        self.waypoints = []
        
        if self.solution:
            self.waypoints = create_waypoints_from_solution(self.solution)
    
    def solve(self, start_pegs: int) -> Optional[List[Tuple[int, int, int]]]:
        """Решает используя известное решение."""
        from core.bitboard import ENGLISH_START
        
        if start_pegs == ENGLISH_START and self.solution:
            return self.solution
        
        return None
    
    def get_known_solution(self) -> Optional[List[Tuple[int, int, int]]]:
        """Возвращает известное решение."""
        return self.solution


def format_solution_moves(moves: List[Tuple[int, int, int]]) -> List[str]:
    """Форматирует список ходов."""
    result = []
    for from_pos, _, to_pos in moves:
        fr, fc = from_pos // 7, from_pos % 7
        tr, tc = to_pos // 7, to_pos % 7
        from_str = f"{chr(fc + ord('A'))}{fr + 1}"
        to_str = f"{chr(tc + ord('A'))}{tr + 1}"
        result.append(f"{from_str} → {to_str}")
    return result


# =====================================================
# ТЕСТИРОВАНИЕ
# =====================================================

if __name__ == "__main__":
    print("English Board Solutions")
    print("=" * 50)
    
    solution = get_english_solution()
    
    if solution:
        print(f"Solution: {len(solution)} moves")
        
        if verify_solution(solution):
            print("✅ Solution verified!")
        else:
            print("❌ Solution invalid!")
        
        print("\nMoves:")
        for i, move_str in enumerate(format_solution_moves(solution), 1):
            print(f"  {i:2}. {move_str}")
    else:
        print("No solution found")
