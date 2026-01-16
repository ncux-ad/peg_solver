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
from peg_io.visualizer import format_bitboard_solution
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
    """Решает доску в матричном формате."""
    from core.board import Board
    
    board_obj = Board.from_matrix(board_matrix)
    # Конвертируем в BitBoard для решателей
    pegs = 0
    for r, c in board_obj.pegs:
        pos = r * 7 + c
        pegs |= (1 << pos)
    
    bitboard = BitBoard(pegs)
    return solve_bitboard(bitboard, solver_name)


def solve_bitboard(board, solver_name='hybrid'):
    """Решает BitBoard."""
    solver_class = SOLVERS.get(solver_name, HybridSolver)
    solver = solver_class(verbose=True)
    
    start = time.time()
    result = solver.solve(board)
    elapsed = time.time() - start
    
    if result:
        formatted = format_bitboard_solution(result)
        print(f"\n{format_solution(formatted)}")
        print(f"\n⏱ Время: {elapsed:.3f}с")
        return formatted
    else:
        print("\n❌ Решение не найдено")
        print(f"⏱ Время: {elapsed:.3f}с")
        return None


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
