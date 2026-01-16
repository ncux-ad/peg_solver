# patterns.py

def match_line_of_three(board):
    rows, cols = len(board), len(board[0])
    for r in range(rows):
        for c in range(cols - 2):
            if board[r][c] == board[r][c+1] == '●' and board[r][c+2] == '○':
                return (r, c, 0, 1)
            if board[r][c] == '○' and board[r][c+1] == board[r][c+2] == '●':
                return (r, c+2, 0, -1)
    for c in range(cols):
        for r in range(rows - 2):
            if board[r][c] == board[r+1][c] == '●' and board[r+2][c] == '○':
                return (r, c, 1, 0)
            if board[r][c] == '○' and board[r+1][c] == board[r+2][c] == '●':
                return (r+2, c, -1, 0)
    return None

def match_line_of_four(board):
    rows, cols = len(board), len(board[0])
    for r in range(rows):
        for c in range(cols - 3):
            if board[r][c] == board[r][c+1] == board[r][c+2] == '●' and board[r][c+3] == '○':
                return (r, c, 0, 1)
            if board[r][c] == '○' and board[r][c+1] == board[r][c+2] == board[r][c+3] == '●':
                return (r, c+3, 0, -1)
    for c in range(cols):
        for r in range(rows - 3):
            if board[r][c] == board[r+1][c] == board[r+2][c] == '●' and board[r+3][c] == '○':
                return (r, c, 1, 0)
            if board[r][c] == '○' and board[r+1][c] == board[r+2][c] == board[r+3][c] == '●':
                return (r+3, c, -1, 0)
    return None

def match_square_2x2(board):
    rows, cols = len(board), len(board[0])
    for r in range(rows - 1):
        for c in range(cols - 1):
            block = [board[r][c], board[r][c+1], board[r+1][c], board[r+1][c+1]]
            if block.count('●') == 3 and block.count('○') == 1:
                if board[r][c] == '○' and board[r][c+1] == board[r+1][c] == '●':
                    return (r+1, c, -1, 0)
                if board[r+1][c+1] == '○' and board[r][c+1] == board[r+1][c] == '●':
                    return (r, c+1, 1, 0)
                if board[r][c+1] == '○' and board[r][c] == board[r+1][c+1] == '●':
                    return (r+1, c+1, -1, 0)
                if board[r+1][c] == '○' and board[r][c] == board[r+1][c+1] == '●':
                    return (r, c, 1, 0)
    return None

def match_edge_cleanup(board):
    rows, cols = len(board), len(board[0])
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == '●':
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    r1, c1 = r + dr, c + dc
                    r2, c2 = r + 2*dr, c + 2*dc
                    if 0 <= r2 < rows and 0 <= c2 < cols:
                        if board[r1][c1] == '●' and board[r2][c2] == '○':
                            return (r, c, dr, dc)
    return None

def available_patterns():
    return [
        match_line_of_three,
        match_line_of_four,
        match_square_2x2,
        match_edge_cleanup
    ]
