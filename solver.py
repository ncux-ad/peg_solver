# solver.py

from copy import deepcopy
from heapq import heappush, heappop
from patterns import available_patterns
from heuristics import combined_heuristic
from solutions_db import get_solution, store_solution
from reverse_solver import reverse_solver
from utils import DIRECTIONS, board_to_str, index_to_pos

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def apply_move(board, r, c, dr, dc):
    new_board = deepcopy(board)
    r1, c1 = r + dr, c + dc
    r2, c2 = r + 2*dr, c + 2*dc
    new_board[r][c] = '○'
    new_board[r1][c1] = '○'
    new_board[r2][c2] = '●'
    return new_board

def index_to_pos(row, col):
    return f"{chr(col + ord('A'))}{row + 1}"

def board_to_str(board):
    return ''.join([''.join(row) for row in board])

def valid_move(board, r, c, dr, dc):
    r1, c1 = r + dr, c + dc
    r2, c2 = r + 2*dr, c + 2*dc
    rows, cols = len(board), len(board[0])
    return (0 <= r2 < rows and 0 <= c2 < cols and
            board[r][c] == '●' and board[r1][c1] == '●' and board[r2][c2] == '○')

def pattern_based_solver(board):
    path = []
    while True:
        matched = False
        for pattern_func in available_patterns():
            pattern = pattern_func(board)
            if pattern:
                r, c, dr, dc = pattern
                board = apply_move(board, r, c, dr, dc)
                move = f"{index_to_pos(r, c)} → {index_to_pos(r + 2*dr, c + 2*dc)}"
                path.append(move)
                matched = True
                break
        if not matched:
            break
    return path if sum(row.count('●') for row in board) == 1 else None

def a_star_solver(board, center):
    heap = []
    visited = set()
    initial_pegs = sum(row.count('●') for row in board)

    heappush(heap, (combined_heuristic(initial_pegs, 0, board, center), 0, board, []))
    visited.add(board_to_str(board))

    while heap:
        _, steps, current_board, path = heappop(heap)
        pegs = sum(row.count('●') for row in current_board)
        if pegs == 1:
            return path

        for r in range(len(current_board)):
            for c in range(len(current_board[0])):
                for dr, dc in DIRECTIONS:
                    if valid_move(current_board, r, c, dr, dc):
                        new_board = apply_move(current_board, r, c, dr, dc)
                        board_str = board_to_str(new_board)
                        if board_str not in visited:
                            visited.add(board_str)
                            move = f"{index_to_pos(r, c)} → {index_to_pos(r + 2*dr, c + 2*dc)}"
                            heappush(
                                heap,
                                (combined_heuristic(pegs - 1, steps + 1, new_board, center),
                                 steps + 1, new_board, path + [move])
                            )
    return None

def hybrid_solver(board, center=(3, 3)):
    # Check cache
    cached = get_solution(board)
    if cached:
        print("→ Решение найдено в базе.")
        return cached

    print("→ Пробуем шаблонный решатель...")
    pattern_solution = pattern_based_solver(deepcopy(board))
    if pattern_solution:
        store_solution(board, pattern_solution)
        return pattern_solution

    print("→ Пробуем A* решатель...")
    a_star_solution = a_star_solver(deepcopy(board), center)
    if a_star_solution:
        store_solution(board, a_star_solution)
        return a_star_solution

    print("→ Пробуем обратный решатель...")
    reverse_solution = reverse_solver(deepcopy(board))
    if reverse_solution:
        store_solution(board, reverse_solution)
        return reverse_solution

    print("→ Решение не найдено.")
    return None