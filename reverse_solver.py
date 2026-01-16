"""
reverse_solver.py

Обратный решатель: строит решение от целевого состояния к начальному.
Полезен для проверки достижимости и bidirectional search.
"""

from typing import List, Optional, Set
from collections import deque
from copy import deepcopy

from board import Board, index_to_pos, DIRECTIONS
from utils import board_to_str


def reverse_move_matrix(board: List[List[str]], r: int, c: int, dr: int, dc: int) -> Optional[List[List[str]]]:
    """
    Выполняет обратный ход на матричной доске.
    Обратный ход: ○○● → ●●○
    """
    rows, cols = len(board), len(board[0])
    r1, c1 = r + dr, c + dc
    r2, c2 = r + 2 * dr, c + 2 * dc

    # Проверка границ
    if not (0 <= r1 < rows and 0 <= c1 < cols and 0 <= r2 < rows and 0 <= c2 < cols):
        return None

    # Проверка условий обратного хода
    if board[r][c] != '○' or board[r1][c1] != '○' or board[r2][c2] != '●':
        return None

    new_board = deepcopy(board)
    new_board[r][c] = '●'
    new_board[r1][c1] = '●'
    new_board[r2][c2] = '○'
    return new_board


def reverse_solver(target_board: List[List[str]], initial_peg_count: int = 32,
                   max_depth: int = 31) -> Optional[List[str]]:
    """
    BFS от целевого состояния к начальному.

    Args:
        target_board: целевая позиция (обычно 1 колышек)
        initial_peg_count: количество колышков в начальном состоянии
        max_depth: максимальная глубина поиска

    Returns:
        Список ходов от начала к концу, или None
    """
    rows, cols = len(target_board), len(target_board[0])

    queue = deque()
    visited: Set[str] = set()

    queue.append((target_board, [], 0))
    visited.add(board_to_str(target_board))

    while queue:
        board, path, depth = queue.popleft()

        if depth > max_depth:
            continue

        peg_count = sum(row.count('●') for row in board)

        # Достигли начального состояния?
        if peg_count == initial_peg_count:
            # Возвращаем путь в прямом порядке
            return list(reversed(path))

        # Генерируем все обратные ходы
        for r in range(rows):
            for c in range(cols):
                if board[r][c] != '○':
                    continue

                for dr, dc in DIRECTIONS:
                    new_board = reverse_move_matrix(board, r, c, dr, dc)
                    if new_board is None:
                        continue

                    board_str = board_to_str(new_board)
                    if board_str in visited:
                        continue

                    visited.add(board_str)

                    # Формируем ход в прямом направлении
                    # Обратный ход (r,c) → означает прямой ход (r+2dr, c+2dc) → (r, c)
                    from_r, from_c = r + 2 * dr, c + 2 * dc
                    to_r, to_c = r, c
                    move_str = f"{index_to_pos(from_r, from_c)} → {index_to_pos(to_r, to_c)}"

                    queue.append((new_board, path + [move_str], depth + 1))

    return None


def reverse_solver_optimized(target: Board, initial_peg_count: int = 32,
                             max_depth: int = 31) -> Optional[List[str]]:
    """
    Оптимизированный обратный решатель с использованием Board класса.
    """
    queue = deque()
    visited: Set = set()

    queue.append((target, [], 0))
    visited.add(target.pegs)

    while queue:
        board, path, depth = queue.popleft()

        if depth > max_depth:
            continue

        if board.peg_count() == initial_peg_count:
            return list(reversed(path))

        # Генерируем обратные ходы
        for r, c in list(board.holes):
            for dr, dc in DIRECTIONS:
                new_board = board.reverse_move(r, c, dr, dc)
                if new_board is None:
                    continue

                if new_board.pegs in visited:
                    continue

                visited.add(new_board.pegs)

                from_r, from_c = r + 2 * dr, c + 2 * dc
                move_str = f"{index_to_pos(from_r, from_c)} → {index_to_pos(r, c)}"

                queue.append((new_board, path + [move_str], depth + 1))

    return None
