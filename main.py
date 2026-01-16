"""
main.py

Точка входа для запуска решения Peg Solitaire.
Поддерживает как командную строку, так и использование как библиотеки.
"""

import re
import sys
from typing import List, Optional

from solver import hybrid_solver
from visualizer import display_board, format_solution
from board import Board


def parse_input(text: str) -> List[List[str]]:
    """
    Парсит текстовый формат описания позиции.

    Формат: size=7x7 pegs=A2,A6,... empty=D4

    Args:
        text: строка с описанием позиции

    Returns:
        Игровое поле в матричном представлении

    Raises:
        ValueError: если формат неверный
    """
    size_match = re.search(r'size=(\d+)x(\d+)', text)
    pegs_match = re.search(r'pegs=([\w,]+)', text)
    empty_match = re.search(r'empty=([\w,]+)', text)

    if not size_match or not pegs_match or not empty_match:
        raise ValueError(
            "Неверный формат ввода. Ожидается: size=NxM pegs=A1,A2,... empty=D4"
        )

    rows, cols = int(size_match.group(1)), int(size_match.group(2))
    pegs = pegs_match.group(1).split(',')
    empty = empty_match.group(1).split(',')

    # Инициализируем пустую доску
    board = [['▫' for _ in range(cols)] for _ in range(rows)]

    # Расставляем колышки
    for pos in pegs:
        pos = pos.strip()
        if not pos:
            continue
        col = ord(pos[0].upper()) - ord('A')
        row = int(pos[1:]) - 1
        if 0 <= row < rows and 0 <= col < cols:
            board[row][col] = '●'

    # Расставляем пустые места
    for pos in empty:
        pos = pos.strip()
        if not pos:
            continue
        col = ord(pos[0].upper()) - ord('A')
        row = int(pos[1:]) - 1
        if 0 <= row < rows and 0 <= col < cols:
            board[row][col] = '○'

    return board


def create_english_board() -> List[List[str]]:
    """
    Создаёт стандартную английскую доску 7x7 (крест) с пустым центром.
    """
    # Маска английской доски (1 = игровая клетка)
    mask = [
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
    ]

    board = []
    for r in range(7):
        row = []
        for c in range(7):
            if mask[r][c] == 0:
                row.append('▫')  # Недоступная клетка
            elif r == 3 and c == 3:
                row.append('○')  # Центр пустой
            else:
                row.append('●')  # Колышек
        board.append(row)

    return board


def solve_and_display(board: List[List[str]], center=(3, 3)) -> Optional[List[str]]:
    """
    Решает головоломку и выводит результат.
    """
    print("=" * 50)
    print("Начальная позиция:")
    print(display_board(board))
    print("=" * 50)

    # Информация о позиции
    peg_count = sum(row.count('●') for row in board)
    print(f"Колышков: {peg_count}")
    print(f"Минимум ходов: {peg_count - 1}")
    print()

    print("Запускаем гибридный решатель...")
    print()

    solution = hybrid_solver(board, center)

    print()
    print("=" * 50)
    print(format_solution(solution))
    print("=" * 50)

    return solution


def main():
    """Точка входа при запуске из командной строки."""

    if len(sys.argv) > 1:
        # Режим с аргументами командной строки
        text_input = ' '.join(sys.argv[1:])
        try:
            board = parse_input(text_input)
        except ValueError as e:
            print(f"Ошибка: {e}")
            sys.exit(1)
    else:
        # Демо-режим: стандартная английская доска
        print("Peg Solitaire Solver")
        print("Использование: python main.py 'size=7x7 pegs=... empty=D4'")
        print()
        print("Запуск демо с английской доской...")
        print()
        board = create_english_board()

    solve_and_display(board)


if __name__ == "__main__":
    main()
