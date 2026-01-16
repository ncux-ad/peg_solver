# visualizer.py

def display_board(board):
    header = "   " + " ".join([f"{chr(c + ord('A'))}" for c in range(len(board[0]))])
    lines = [header]
    rows_count = len(board)
    for r in range(rows_count):
        row_str = f"{r + 1:<2} " + " ".join(board[r])
        lines.append(row_str)
    return "\n".join(lines)

def format_solution(moves):
    if not moves:
        return "Решение не найдено"
    return f"Найдено решение за {len(moves)} ходов:\n" + "\n".join(f"{i+1}. {move}" for i, move in enumerate(moves))