# utils.py

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def board_to_str(board):
    return ''.join([''.join(row) for row in board])

def index_to_pos(row, col):
    return f"{chr(col + ord('A'))}{row + 1}"
