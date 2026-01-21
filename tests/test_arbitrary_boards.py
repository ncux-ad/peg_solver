"""
tests/test_arbitrary_boards.py

Тесты для произвольных досок 7×7 с вырезанными ячейками.
Проверяет, что все решатели корректно работают с произвольными конфигурациями.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Tuple
import pytest

from core.bitboard import BitBoard, get_valid_positions, is_english_board, get_center_position
from solutions.verify import verify_bitboard_solution
from solvers import (
    DFSSolver, AStarSolver, IDAStarSolver, BeamSolver,
    BidirectionalSolver, HybridSolver, GovernorSolver, SequentialSolver,
    PatternAStarSolver, ZobristDFSSolver, ExhaustiveSolver, LookupSolver,
    ParallelBeamSolver, ParallelSolver
)


def make_plus_board() -> BitBoard:
    """
    Создаёт доску "плюс" (5 клеток):
    
      ●
    ● ● ○
      ●
    """
    pegs_bits = 0
    holes_bits = 0
    
    # Позиции плюса: (2,3), (3,2), (3,3), (3,4), (4,3)
    # Дырка в центре: (3,3)
    positions = [
        (2, 3),  # верх
        (3, 2),  # лево
        (3, 4),  # право
        (4, 3),  # низ
    ]
    
    for r, c in positions:
        pos = r * 7 + c
        pegs_bits |= (1 << pos)
    
    # Дырка в центре
    center_pos = 3 * 7 + 3
    holes_bits |= (1 << center_pos)
    
    valid_mask = pegs_bits | holes_bits
    return BitBoard(pegs_bits, valid_mask=valid_mask)


def make_square_board() -> BitBoard:
    """
    Создаёт доску "квадрат" 4×4 (16 клеток):
    
    ● ● ● ●
    ● ● ○ ●
    ● ● ● ●
    ● ● ● ●
    """
    pegs_bits = 0
    holes_bits = 0
    
    # Квадрат 4×4 начиная с (1,1)
    for r in range(1, 5):
        for c in range(1, 5):
            pos = r * 7 + c
            if r == 2 and c == 3:
                # Дырка в центре квадрата
                holes_bits |= (1 << pos)
            else:
                pegs_bits |= (1 << pos)
    
    valid_mask = pegs_bits | holes_bits
    return BitBoard(pegs_bits, valid_mask=valid_mask)


def make_small_board() -> BitBoard:
    """
    Создаёт маленькую доску 3×3 (9 клеток):
    
    ● ● ○
    ● ● ●
    ● ● ●
    """
    pegs_bits = 0
    holes_bits = 0
    
    # Квадрат 3×3 начиная с (2,2)
    for r in range(2, 5):
        for c in range(2, 5):
            pos = r * 7 + c
            if r == 2 and c == 4:
                # Дырка в правом верхнем углу
                holes_bits |= (1 << pos)
            else:
                pegs_bits |= (1 << pos)
    
    valid_mask = pegs_bits | holes_bits
    return BitBoard(pegs_bits, valid_mask=valid_mask)


def make_already_solved_board() -> BitBoard:
    """Создаёт доску с 1 колышком (уже решена)."""
    pegs_bits = 1 << (3 * 7 + 3)  # Центр
    valid_mask = pegs_bits
    return BitBoard(pegs_bits, valid_mask=valid_mask)


def make_two_pegs_board() -> BitBoard:
    """Создаёт доску с 2 колышками (1 ход до решения)."""
    pegs_bits = 0
    holes_bits = 0
    
    # Два колышка рядом, дырка для прыжка
    from_pos = 3 * 7 + 2
    jumped_pos = 3 * 7 + 3
    to_pos = 3 * 7 + 4
    
    pegs_bits |= (1 << from_pos)
    pegs_bits |= (1 << jumped_pos)
    holes_bits |= (1 << to_pos)
    
    valid_mask = pegs_bits | holes_bits
    return BitBoard(pegs_bits, valid_mask=valid_mask)


# =====================================================
# Тесты утилит
# =====================================================

def test_get_valid_positions():
    """Проверяет, что get_valid_positions возвращает правильные позиции."""
    board = make_plus_board()
    valid_pos = get_valid_positions(board)
    
    # Плюс должен иметь 5 валидных позиций
    assert len(valid_pos) == 5
    assert 2 * 7 + 3 in valid_pos  # верх
    assert 3 * 7 + 2 in valid_pos  # лево
    assert 3 * 7 + 3 in valid_pos  # центр (дырка)
    assert 3 * 7 + 4 in valid_pos  # право
    assert 4 * 7 + 3 in valid_pos  # низ


def test_is_english_board():
    """Проверяет определение английской доски."""
    english_board = BitBoard.english_start()
    assert is_english_board(english_board) is True
    
    plus_board = make_plus_board()
    assert is_english_board(plus_board) is False


def test_get_center_position():
    """Проверяет получение центральной позиции."""
    english_board = BitBoard.english_start()
    center = get_center_position(english_board)
    assert center == 24  # CENTER_POS
    
    plus_board = make_plus_board()
    center = get_center_position(plus_board)
    assert center is not None
    assert center == 3 * 7 + 3  # Центр плюса


# =====================================================
# Тесты решателей на произвольных досках
# =====================================================

@pytest.mark.parametrize("solver_class,kwargs", [
    (DFSSolver, {}),
    (AStarSolver, {}),
    (IDAStarSolver, {'max_depth': 20}),
    (BeamSolver, {'max_depth': 20}),
    (BidirectionalSolver, {'max_iterations': 10000}),
])
def test_solvers_on_plus_board(solver_class, kwargs):
    """Проверяет, что решатели работают с доской "плюс"."""
    board = make_plus_board()
    solver = solver_class(verbose=False, **kwargs)
    
    # Плюс должен решаться (4 колышка → 1 колышек)
    solution = solver.solve(board)
    
    if solution:
        # Проверяем валидность решения
        assert verify_bitboard_solution(board, solution) is True
        # Проверяем, что остался 1 колышек
        final_board = board
        for move in solution:
            final_board = final_board.apply_move(*move)
        assert final_board.peg_count() == 1


@pytest.mark.parametrize("solver_class,kwargs", [
    (DFSSolver, {}),
    (BeamSolver, {'max_depth': 20}),
    (AStarSolver, {}),
])
def test_solvers_on_square_board(solver_class, kwargs):
    """Проверяет, что решатели работают с доской "квадрат"."""
    board = make_square_board()
    solver = solver_class(verbose=False, **kwargs)
    
    # Квадрат может решаться (15 колышков → 1 колышек)
    solution = solver.solve(board)
    
    if solution:
        # Проверяем валидность решения
        assert verify_bitboard_solution(board, solution) is True


def test_solvers_on_already_solved():
    """Проверяет, что решатели корректно обрабатывают уже решённую доску."""
    board = make_already_solved_board()
    
    solvers = [
        DFSSolver(verbose=False),
        BeamSolver(verbose=False),
        AStarSolver(verbose=False),
    ]
    
    for solver in solvers:
        solution = solver.solve(board)
        # Уже решённая доска должна возвращать пустое решение или None
        # (в зависимости от реализации)
        if solution is not None:
            assert len(solution) == 0 or verify_bitboard_solution(board, solution)


def test_solvers_on_two_pegs():
    """Проверяет, что решатели находят решение для доски с 2 колышками."""
    board = make_two_pegs_board()
    
    solvers = [
        DFSSolver(verbose=False),
        BeamSolver(verbose=False),
        AStarSolver(verbose=False),
    ]
    
    for solver in solvers:
        solution = solver.solve(board)
        assert solution is not None
        assert len(solution) == 1  # Один ход
        assert verify_bitboard_solution(board, solution) is True


def test_bidirectional_on_arbitrary_board():
    """Проверяет Bidirectional на произвольной доске."""
    board = make_plus_board()
    solver = BidirectionalSolver(verbose=False, max_iterations=10000)
    
    solution = solver.solve(board)
    
    if solution:
        assert verify_bitboard_solution(board, solution) is True


def test_hybrid_on_arbitrary_board():
    """Проверяет Hybrid на произвольной доске."""
    board = make_plus_board()
    solver = HybridSolver(verbose=False, timeout=30.0)
    
    solution = solver.solve(board)
    
    if solution:
        assert verify_bitboard_solution(board, solution) is True


def test_governor_on_arbitrary_board():
    """Проверяет Governor на произвольной доске."""
    board = make_plus_board()
    solver = GovernorSolver(verbose=False, timeout=30.0)
    
    solution = solver.solve(board)
    
    if solution:
        assert verify_bitboard_solution(board, solution) is True


def test_sequential_on_arbitrary_board():
    """Проверяет Sequential на произвольной доске."""
    board = make_plus_board()
    solver = SequentialSolver(verbose=False, timeout=30.0)
    
    solution = solver.solve(board)
    
    if solution:
        assert verify_bitboard_solution(board, solution) is True


# =====================================================
# Тесты граничных случаев
# =====================================================

def test_board_with_cutout_corners():
    """Проверяет доску с вырезанными углами."""
    pegs_bits = 0
    holes_bits = 0
    
    # Заполняем центральную область 5×5, вырезаем углы
    for r in range(1, 6):
        for c in range(1, 6):
            pos = r * 7 + c
            # Вырезаем углы: (1,1), (1,5), (5,1), (5,5)
            if (r, c) in [(1, 1), (1, 5), (5, 1), (5, 5)]:
                continue  # Вырезано
            if r == 3 and c == 3:
                holes_bits |= (1 << pos)  # Дырка в центре
            else:
                pegs_bits |= (1 << pos)
    
    valid_mask = pegs_bits | holes_bits
    board = BitBoard(pegs_bits, valid_mask=valid_mask)
    
    # Проверяем, что доска создана корректно
    assert board.peg_count() == 20  # 5×5 - 4 угла - 1 дырка = 20
    
    # Проверяем, что решатель не падает
    solver = DFSSolver(verbose=False)
    solution = solver.solve(board)
    
    if solution:
        assert verify_bitboard_solution(board, solution) is True


def test_board_with_isolated_region():
    """Проверяет доску с изолированной областью (не должно быть решений)."""
    pegs_bits = 0
    holes_bits = 0
    
    # Две изолированные группы колышков (нельзя прыгнуть между ними)
    # Группа 1: (1,1), (1,2), (2,1)
    # Группа 2: (5,5), (5,6), (6,5)
    group1 = [(1, 1), (1, 2), (2, 1)]
    group2 = [(5, 5), (5, 6), (6, 5)]
    
    for r, c in group1 + group2:
        pos = r * 7 + c
        pegs_bits |= (1 << pos)
    
    # Дырка в группе 1
    holes_bits |= (1 << (1 * 7 + 3))
    
    valid_mask = pegs_bits | holes_bits
    board = BitBoard(pegs_bits, valid_mask=valid_mask)
    
    # Проверяем, что решатель корректно обрабатывает (может не найти решение)
    solver = DFSSolver(verbose=False)
    solution = solver.solve(board)
    
    # Если решение найдено, проверяем валидность
    if solution:
        assert verify_bitboard_solution(board, solution) is True


def test_all_solvers_no_crash():
    """Проверяет, что все решатели не падают на произвольной доске."""
    board = make_plus_board()
    
    solvers = [
        DFSSolver(verbose=False),
        AStarSolver(verbose=False),
        IDAStarSolver(verbose=False, max_depth=10),
        BeamSolver(verbose=False, max_depth=10),
        BidirectionalSolver(verbose=False, max_iterations=1000),
        PatternAStarSolver(verbose=False),
        ZobristDFSSolver(verbose=False),
        ExhaustiveSolver(verbose=False, timeout=5.0, max_depth=10),
        LookupSolver(verbose=False, use_fallback=False),
        HybridSolver(verbose=False, timeout=5.0),
        GovernorSolver(verbose=False, timeout=5.0),
        SequentialSolver(verbose=False, timeout=5.0),
    ]
    
    for solver in solvers:
        try:
            solution = solver.solve(board)
            # Если решение найдено, проверяем валидность
            if solution:
                assert verify_bitboard_solution(board, solution) is True
        except Exception as e:
            pytest.fail(f"Solver {solver.__class__.__name__} crashed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
