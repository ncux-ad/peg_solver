#!/usr/bin/env python3
"""
main.py

Точка входа для Peg Solitaire Solver.

Использование:
    python main.py                           # демо с английской доской
    python main.py "size=7x7 pegs=... empty=D4"  # своя позиция
    python main.py --solver dfs              # выбор решателя
"""

import sys
import argparse
import time

from core.bitboard import BitBoard
from peg_io import parse_input, create_english_board, display_board, format_solution
from peg_io.cache import save_solution as cache_save_solution
from peg_io.visualizer import format_bitboard_solution
from solutions.verify import verify_bitboard_solution, bitboard_to_matrix
from solvers import (
    DFSSolver, AStarSolver, IDAStarSolver,
    BeamSolver, ParallelSolver, HybridSolver
)


SOLVERS = {
    'dfs': DFSSolver,
    'astar': AStarSolver,
    'ida': IDAStarSolver,
    'beam': BeamSolver,
    'parallel': ParallelSolver,
    'hybrid': HybridSolver,
}


def solve_matrix_board(board_matrix, solver_name='hybrid'):
    """Решает доску в матричном формате и сохраняет корректное решение в кэш."""
    # Конвертируем матрицу в BitBoard: валидные клетки = PEG или HOLE
    pegs_bits = 0
    valid_mask = 0
    rows = len(board_matrix)
    cols = len(board_matrix[0]) if rows > 0 else 0

    for r in range(rows):
        for c in range(cols):
            pos = r * 7 + c
            cell = board_matrix[r][c]
            if cell == '●':  # PEG
                pegs_bits |= (1 << pos)
                valid_mask |= (1 << pos)
            elif cell == '○':  # HOLE
                valid_mask |= (1 << pos)
            # '▫' считаем вырезанной клеткой (вне valid_mask)

    bitboard = BitBoard(pegs_bits, valid_mask=valid_mask if valid_mask else None)
    return solve_bitboard(bitboard, solver_name, initial_matrix=board_matrix)


def solve_bitboard(board, solver_name='hybrid', initial_matrix=None):
    """
    Решает BitBoard, проверяет найденное решение и при успехе сохраняет его в кэш.

    Args:
        board: начальное состояние BitBoard
        solver_name: имя решателя
        initial_matrix: исходная матрица доски (если есть). Если None,
                        матрица будет восстановлена из BitBoard.
    """
    solver_class = SOLVERS.get(solver_name, HybridSolver)
    solver = solver_class(verbose=True)
    
    start = time.time()
    result = solver.solve(board)
    elapsed = time.time() - start
    
    if not result:
        print("\n❌ Решение не найдено")
        print(f"⏱ Время: {elapsed:.3f}с")
        return None

    # Валидация решения на BitBoard (учитывает valid_mask)
    if not verify_bitboard_solution(board, result):
        print("\n❌ Найдено некорректное решение (валидация не пройдена), кэширование пропущено")
        return None

    # Форматируем решение для вывода
    formatted = format_bitboard_solution(result)
    print(f"\n{format_solution(formatted)}")
    print(f"\n⏱ Время: {elapsed:.3f}с")

    # Подготавливаем матрицу для кэширования
    try:
        if initial_matrix is not None:
            start_matrix = initial_matrix
        else:
            # Восстанавливаем матрицу из BitBoard (по valid_mask)
            start_matrix = bitboard_to_matrix(board)

        # Сохраняем решение в общий кэш
        cache_save_solution(start_matrix, formatted)
    except Exception as e:
        # Ошибка кэширования не должна ломать основной сценарий
        print(f"⚠️ Не удалось сохранить решение в кэш: {e}")

    return formatted


def main():
    parser = argparse.ArgumentParser(
        description='Peg Solitaire Solver',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python main.py                     # английская доска
  python main.py --solver beam       # Beam Search
  python main.py --solver dfs        # DFS с мемоизацией
  python main.py --solver parallel   # многопоточный
        """
    )
    parser.add_argument(
        'input', nargs='?',
        help='Позиция в формате: size=7x7 pegs=A1,A2,... empty=D4'
    )
    parser.add_argument(
        '--solver', '-s', choices=list(SOLVERS.keys()),
        default='hybrid', help='Выбор решателя (default: hybrid)'
    )
    parser.add_argument(
        '--test', action='store_true',
        help='Запуск на тестовой позиции (8 колышков)'
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🎯 Peg Solitaire Solver")
    print("=" * 50)
    
    if args.test:
        # Тестовая позиция (8 колышков) — решается быстро
        test_pegs = 0
        for pos in [16, 17, 18, 23, 24, 25, 30, 31]:
            test_pegs |= (1 << pos)
        board = BitBoard(test_pegs)
        print(f"\nТестовая позиция ({board.peg_count()} колышков):")
        print(board.to_string())
    elif args.input:
        try:
            board_matrix = parse_input(args.input)
            print("\nВходная позиция:")
            print(display_board(board_matrix))
            solve_matrix_board(board_matrix, args.solver)
            return
        except ValueError as e:
            print(f"❌ Ошибка: {e}")
            sys.exit(1)
    else:
        # Английская доска
        board = BitBoard.english_start()
        print(f"\nАнглийская доска ({board.peg_count()} колышков):")
        print(board.to_string())
        print("\n⚠️  Полная доска сложна — используйте --test для быстрого теста")
    
    print(f"\n🔧 Решатель: {args.solver}")
    print("-" * 50)
    
    solve_bitboard(board, args.solver)


if __name__ == "__main__":
    main()
