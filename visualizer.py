"""
visualizer.py

Модули для вывода состояний и решений Peg Solitaire.
"""

def display_board(board):
    """
    Красиво форматирует текстовое представление доски.
    Args:
        board (list[list[str]])
    Returns:
        str
    """
    header = "   " + " ".join([f"{chr(c + ord('A'))}" for c in range(len(board[0]))])
    lines = [header]
    rows_count = len(board)
    for r in range(rows_count):
        row_str = f"{r + 1:<2} " + " ".join(board[r])
        lines.append(row_str)
    return "\n".join(lines)

def format_solution(moves):
    """
    Форматирует список ходов решения для вывода пользователю.
    Args:
        moves (list[str] или None)
    Returns:
        str
    """
    if not moves:
        return "Решение не найдено"
    return f"Найдено решение за {len(moves)} ходов:\n" + "\n".join(f"{i+1}. {move}" for i, move in enumerate(moves))
