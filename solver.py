"""
solver.py

Оптимизированные решатели для Peg Solitaire:
- A* с parent pointers (экономия памяти)
- IDA* (Iterative Deepening A*)
- Bidirectional search
- Гибридный решатель
"""

from typing import List, Optional, Tuple, Dict, Set
from heapq import heappush, heappop
from collections import deque
from copy import deepcopy

from board import Board, index_to_pos, DIRECTIONS
from heuristics import combined_heuristic, combined_heuristic_aggressive
from invariants import (
    is_solvable_by_pagoda, is_dead_position,
    get_symmetry_canonical, count_mobility
)
from patterns import apply_pattern_sequence
from solutions_db import get_solution, store_solution

# Тип для хода
Move = Tuple[int, int, int, int]


def format_move(r: int, c: int, dr: int, dc: int) -> str:
    """Форматирует ход для вывода."""
    return f"{index_to_pos(r, c)} → {index_to_pos(r + 2*dr, c + 2*dc)}"


def reconstruct_path(parents: Dict, end_state, start_state) -> List[str]:
    """Восстанавливает путь по parent pointers."""
    path = []
    current = end_state
    while current != start_state:
        prev_state, move = parents[current]
        r, c, dr, dc = move
        path.append(format_move(r, c, dr, dc))
        current = prev_state
    return list(reversed(path))


class SolverStats:
    """Статистика работы решателя."""
    def __init__(self):
        self.nodes_visited = 0
        self.nodes_pruned = 0
        self.max_depth = 0


def a_star_solver(board: Board, center: Tuple[int, int] = (3, 3),
                  target_pos: Tuple[int, int] = (3, 3),
                  use_symmetry: bool = True,
                  aggressive: bool = False) -> Optional[List[str]]:
    """
    Оптимизированный A* с:
    - Parent pointers вместо хранения путей
    - Pagoda pruning
    - Symmetry reduction
    - Dead-end detection

    Args:
        board: начальная позиция
        center: центр доски для эвристики
        target_pos: целевая позиция для последнего колышка
        use_symmetry: использовать ли симметрии для сокращения
        aggressive: использовать агрессивную эвристику

    Returns:
        Список ходов или None
    """
    stats = SolverStats()

    # Проверка решаемости через pagoda
    if not is_solvable_by_pagoda(board, target_pos):
        print("  [Pagoda] Позиция недостижима")
        return None

    heuristic_fn = combined_heuristic_aggressive if aggressive else combined_heuristic

    # Куча: (priority, counter, board)
    # counter для стабильной сортировки при равных приоритетах
    counter = 0
    heap = []
    heappush(heap, (heuristic_fn(board, 0, center), counter, 0, board))

    # Visited: board_hash -> (steps, parent_hash, move)
    # Используем хэш вместо полного состояния
    start_key = board.pegs if not use_symmetry else get_symmetry_canonical(board.pegs, board.rows, board.cols)
    visited: Dict = {start_key: (0, None, None)}

    while heap:
        _, _, steps, current = heappop(heap)
        stats.nodes_visited += 1
        stats.max_depth = max(stats.max_depth, steps)

        # Проверка победы
        if current.peg_count() == 1:
            # Восстанавливаем путь
            path = []
            key = current.pegs if not use_symmetry else get_symmetry_canonical(current.pegs, current.rows, current.cols)
            while visited[key][1] is not None:
                _, parent_key, move = visited[key]
                if move:
                    path.append(format_move(*move))
                key = parent_key
            print(f"  [A*] Найдено! Узлов: {stats.nodes_visited}, глубина: {steps}")
            return list(reversed(path))

        # Dead-end check
        if is_dead_position(current):
            stats.nodes_pruned += 1
            continue

        current_key = current.pegs if not use_symmetry else get_symmetry_canonical(current.pegs, current.rows, current.cols)

        # Генерируем все ходы
        for move in current.get_all_moves():
            r, c, dr, dc = move
            new_board = current.apply_move(r, c, dr, dc)

            # Ключ для нового состояния
            new_key = new_board.pegs if not use_symmetry else get_symmetry_canonical(new_board.pegs, new_board.rows, new_board.cols)

            new_steps = steps + 1

            # Проверяем, посещали ли мы это состояние с меньшим числом шагов
            if new_key in visited:
                if visited[new_key][0] <= new_steps:
                    continue

            visited[new_key] = (new_steps, current_key, move)

            priority = heuristic_fn(new_board, new_steps, center)
            counter += 1
            heappush(heap, (priority, counter, new_steps, new_board))

    print(f"  [A*] Решение не найдено. Узлов: {stats.nodes_visited}")
    return None


def ida_star_solver(board: Board, center: Tuple[int, int] = (3, 3),
                    max_depth: int = 32) -> Optional[List[str]]:
    """
    IDA* (Iterative Deepening A*) — экономит память.
    Хорош для глубоких деревьев поиска.
    """
    def search(current: Board, g: int, bound: float, path: List[str]) -> Tuple[Optional[List[str]], float]:
        f = g + (current.peg_count() - 1)

        if f > bound:
            return None, f

        if current.peg_count() == 1:
            return path, f

        if is_dead_position(current):
            return None, float('inf')

        min_threshold = float('inf')

        for move in current.get_all_moves():
            r, c, dr, dc = move
            new_board = current.apply_move(r, c, dr, dc)
            move_str = format_move(r, c, dr, dc)

            result, threshold = search(new_board, g + 1, bound, path + [move_str])
            if result is not None:
                return result, threshold
            min_threshold = min(min_threshold, threshold)

        return None, min_threshold

    bound = board.peg_count() - 1
    path: List[str] = []

    while bound <= max_depth:
        print(f"  [IDA*] Bound: {bound}")
        result, new_bound = search(board, 0, bound, path)
        if result is not None:
            return result
        if new_bound == float('inf'):
            break
        bound = new_bound

    return None


def bidirectional_solver(board: Board, target_board: Board,
                         max_iterations: int = 100000) -> Optional[List[str]]:
    """
    Двунаправленный поиск: от начала к концу и от конца к началу.
    Встречаются посередине — экономия времени O(b^(d/2)) вместо O(b^d).
    """
    # Прямой поиск
    forward_queue = deque([(board, [])])
    forward_visited: Dict = {board.pegs: []}

    # Обратный поиск
    backward_queue = deque([(target_board, [])])
    backward_visited: Dict = {target_board.pegs: []}

    iterations = 0

    while forward_queue or backward_queue:
        iterations += 1
        if iterations > max_iterations:
            print(f"  [BiDir] Превышен лимит итераций: {max_iterations}")
            return None

        # Шаг прямого поиска
        if forward_queue:
            current, path = forward_queue.popleft()

            for move in current.get_all_moves():
                r, c, dr, dc = move
                new_board = current.apply_move(r, c, dr, dc)
                new_path = path + [format_move(r, c, dr, dc)]

                if new_board.pegs in backward_visited:
                    # Встретились!
                    backward_path = backward_visited[new_board.pegs]
                    full_path = new_path + list(reversed(backward_path))
                    print(f"  [BiDir] Встреча на итерации {iterations}")
                    return full_path

                if new_board.pegs not in forward_visited:
                    forward_visited[new_board.pegs] = new_path
                    forward_queue.append((new_board, new_path))

        # Шаг обратного поиска
        if backward_queue:
            current, path = backward_queue.popleft()

            for r, c in list(current.holes):
                for dr, dc in DIRECTIONS:
                    new_board = current.reverse_move(r, c, dr, dc)
                    if new_board is None:
                        continue

                    # Формируем ход в прямом направлении
                    move_str = format_move(r + 2*dr, c + 2*dc, -dr, -dc)
                    new_path = path + [move_str]

                    if new_board.pegs in forward_visited:
                        # Встретились!
                        forward_path = forward_visited[new_board.pegs]
                        full_path = forward_path + list(reversed(new_path))
                        print(f"  [BiDir] Встреча на итерации {iterations}")
                        return full_path

                    if new_board.pegs not in backward_visited:
                        backward_visited[new_board.pegs] = new_path
                        backward_queue.append((new_board, new_path))

    return None


def hybrid_solver(board, center: Tuple[int, int] = (3, 3)) -> Optional[List[str]]:
    """
    Гибридный решатель с несколькими стратегиями.
    Поддерживает как новый Board, так и legacy list[list[str]].
    """
    # Конвертируем если нужно
    if isinstance(board, list):
        board_obj = Board.from_matrix(board)
        board_matrix = board
    else:
        board_obj = board
        board_matrix = board.to_matrix()

    # 1. Проверяем кэш
    from utils import board_to_str
    cached = get_solution(board_matrix)
    if cached:
        print("→ Решение найдено в базе.")
        return cached

    # 2. Быстрая проверка pagoda
    target_pos = center
    if not is_solvable_by_pagoda(board_obj, target_pos):
        print("→ Позиция недостижима (pagoda pruning).")
        return None

    # 3. Пробуем паттерны (быстро)
    print("→ Пробуем шаблонный решатель...")
    pattern_solution = apply_pattern_sequence(deepcopy(board_matrix))
    if pattern_solution:
        store_solution(board_matrix, pattern_solution)
        return pattern_solution

    # 4. A* с агрессивной эвристикой (быстрее, но может быть неоптимально)
    print("→ Пробуем A* (агрессивный)...")
    a_star_solution = a_star_solver(board_obj, center, target_pos, aggressive=True)
    if a_star_solution:
        store_solution(board_matrix, a_star_solution)
        return a_star_solution

    # 5. A* со стандартной эвристикой
    print("→ Пробуем A* (стандартный)...")
    a_star_solution = a_star_solver(board_obj, center, target_pos, aggressive=False)
    if a_star_solution:
        store_solution(board_matrix, a_star_solution)
        return a_star_solution

    # 6. IDA* для экономии памяти
    print("→ Пробуем IDA*...")
    ida_solution = ida_star_solver(board_obj, center)
    if ida_solution:
        store_solution(board_matrix, ida_solution)
        return ida_solution

    print("→ Решение не найдено.")
    return None


# === Legacy функции для обратной совместимости ===

def apply_move(board: List[List[str]], r: int, c: int, dr: int, dc: int) -> List[List[str]]:
    """Legacy: применяет ход на матричной доске."""
    new_board = deepcopy(board)
    r1, c1 = r + dr, c + dc
    r2, c2 = r + 2*dr, c + 2*dc
    new_board[r][c] = '○'
    new_board[r1][c1] = '○'
    new_board[r2][c2] = '●'
    return new_board


def valid_move(board: List[List[str]], r: int, c: int, dr: int, dc: int) -> bool:
    """Legacy: проверяет допустимость хода."""
    r1, c1 = r + dr, c + dc
    r2, c2 = r + 2*dr, c + 2*dc
    rows, cols = len(board), len(board[0])
    return (0 <= r2 < rows and 0 <= c2 < cols and
            board[r][c] == '●' and board[r1][c1] == '●' and board[r2][c2] == '○')
