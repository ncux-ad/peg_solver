# main.py

import re
from solver import hybrid_solver
from visualizer import display_board, format_solution

def parse_input(text):
    size_match = re.search(r'size=(\d+)x(\d+)', text)
    pegs_match = re.search(r'pegs=([\w,]+)', text)
    empty_match = re.search(r'empty=([\w,]+)', text)

    if not size_match or not pegs_match or not empty_match:
        raise ValueError("Неверный формат ввода")

    rows, cols = int(size_match.group(1)), int(size_match.group(2))
    pegs = pegs_match.group(1).split(',')
    empty = empty_match.group(1).split(',')

    board = [['▫' for _ in range(cols)] for _ in range(rows)]

    for pos in pegs:
        col = ord(pos[0].upper()) - ord('A')
        row = int(pos[1]) - 1
        board[row][col] = '●'

    for pos in empty:
        col = ord(pos[0].upper()) - ord('A')
        row = int(pos[1]) - 1
        board[row][col] = '○'

    return board

if __name__ == "__main__":
    # Пример: стандартная 7x7 доска, пустая в центре D3
    text_input = (
        "size=7x7 pegs=A2,A6,"
        "B2,B4,B6,"
        "C2,C1,C3,C4,C5,C6,C7,"
        "E1,E2,E3,E4,E5,E6,E7,"
        "F2,F4,F6,"
        "G2,G6"
        "empty=D4"
    )
    board = parse_input(text_input)

    print("Начальная позиция:")
    print(display_board(board))

    print("\n→ Запускаем гибридный решатель...")
    solution = hybrid_solver(board)

    print(format_solution(solution))