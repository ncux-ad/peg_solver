# invariants.py

def create_standard_pagoda_weights(rows, cols):
    # Простая пагода-функция (центр больше весит)
    return [[1 for _ in range(cols)] for _ in range(rows)]

def pagoda_value(board, weights):
    return sum(
        weights[r][c]
        for r in range(len(board))
        for c in range(len(board[0]))
        if board[r][c] == '●'
    )

def is_valid_by_pagoda(board, weights, target_value):
    current = pagoda_value(board, weights)
    return current >= target_value

def count_isolated_pegs(board):
    rows, cols = len(board), len(board[0])
    count = 0
    for r in range(rows):
        for c in range(cols):
            if board[r][c] != '●':
                continue
            neighbors = 0
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == '●':
                    neighbors += 1
            if neighbors == 0:
                count += 1
    return count
