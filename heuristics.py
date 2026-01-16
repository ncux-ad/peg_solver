# heuristics.py

def heuristic_basic(pegs, steps):
    return pegs + steps

def heuristic_distance_to_center(board, center):
    return sum(
        abs(r - center[0]) + abs(c - center[1])
        for r in range(len(board))
        for c in range(len(board[0]))
        if board[r][c] == '●'
    )

def heuristic_isolated_penalty(board):
    from invariants import count_isolated_pegs
    return 5 * count_isolated_pegs(board)

def combined_heuristic(pegs, steps, board, center):
    return (
        heuristic_basic(pegs, steps) +
        heuristic_distance_to_center(board, center) +
        heuristic_isolated_penalty(board)
    )
