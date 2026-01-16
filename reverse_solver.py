# reverse_solver.py

from copy import deepcopy
from utils import DIRECTIONS, board_to_str, index_to_pos


def reverse_move(board, r, c, dr, dc):
    new_board = deepcopy(board)
    r1, c1 = r + dr, c + dc
    r2, c2 = r + 2*dr, c + 2*dc
    if new_board[r][c] != '○' or new_board[r1][c1] != '○' or new_board[r2][c2] != '●':
        return None
    new_board[r][c] = '●'
    new_board[r1][c1] = '●'
    new_board[r2][c2] = '○'
    return new_board

def reverse_solver(target_board, max_depth=31):
    from collections import deque

    queue = deque()
    visited = set()
    queue.append((target_board, []))
    visited.add(board_to_str(target_board))

    while queue:
        board, path = queue.popleft()
        peg_count = sum(row.count('●') for row in board)
        if peg_count == 32:  # стандартное начальное состояние
            return list(reversed(path))

        for r in range(len(board)):
            for c in range(len(board[0])):
                for dr, dc in DIRECTIONS:
                    new_board = reverse_move(board, r, c, dr, dc)
                    if new_board:
                        board_str = board_to_str(new_board)
                        if board_str not in visited:
                            visited.add(board_str)
                            move = f"{index_to_pos(r + 2*dr, c + 2*dc)} ← {index_to_pos(r, c)}"
                            queue.append((new_board, path + [move]))
    return None
