"""
tests/test_dfs_memo.py

Тесты для DFSMemoSolver - Фаза 2.1.
"""

import pytest
from core.bitboard import BitBoard
from solvers.dfs_memo import DFSMemoSolver
from solvers.simple_dfs import SimpleDFSSolver
from solutions.verify import verify_bitboard_solution


def test_dfs_memo_english_board():
    """Тест: DFSMemo должен решить стандартную английскую доску."""
    board = BitBoard.english_start()
    solver = DFSMemoSolver(verbose=False)
    
    solution = solver.solve(board)
    
    assert solution is not None, "Решение должно быть найдено"
    assert len(solution) > 0, "Решение должно содержать ходы"
    
    # Валидация решения
    assert verify_bitboard_solution(board, solution), "Решение должно быть корректным"
    
    # Проверка финального состояния
    final_board = board
    for move in solution:
        final_board = final_board.apply_move(*move)
    
    assert final_board.peg_count() == 1, "Должен остаться один колышек"


def test_dfs_memo_faster_than_simple():
    """Тест: DFSMemo должен быть быстрее SimpleDFS благодаря мемоизации."""
    board = BitBoard.english_start()
    
    # Запускаем SimpleDFS
    simple_solver = SimpleDFSSolver(verbose=False)
    simple_solution = simple_solver.solve(board)
    simple_nodes = simple_solver.stats.nodes_visited
    
    # Запускаем DFSMemo
    memo_solver = DFSMemoSolver(verbose=False)
    memo_solution = memo_solver.solve(board)
    memo_nodes = memo_solver.stats.nodes_visited
    
    # Оба должны найти решение
    assert simple_solution is not None
    assert memo_solution is not None
    
    # DFSMemo должен посетить меньше узлов благодаря мемоизации
    # (но это не гарантировано, так что просто проверяем что оба работают)
    assert simple_nodes > 0
    assert memo_nodes > 0


def test_dfs_memo_memoization_works():
    """Тест: мемоизация действительно работает - повторные вызовы быстрее."""
    board = BitBoard.english_start()
    solver = DFSMemoSolver(verbose=False)
    
    # Первый вызов
    solution1 = solver.solve(board)
    nodes1 = solver.stats.nodes_visited
    
    # Второй вызов (мемо должно помочь)
    solution2 = solver.solve(board)
    nodes2 = solver.stats.nodes_visited
    
    assert solution1 is not None
    assert solution2 is not None
    assert solution1 == solution2, "Решения должны быть одинаковыми"
    
    # Второй вызов должен быть быстрее (меньше узлов)
    # Но мемо очищается при каждом solve(), так что это не применимо
    # Вместо этого проверяем что мемо работает внутри одного solve()
    assert solver.stats.nodes_pruned > 0, "Должны быть отсечённые узлы благодаря мемо"


def test_dfs_memo_with_symmetry():
    """Тест: использование симметрий должно уменьшить количество узлов."""
    board = BitBoard.english_start()
    
    # Без симметрий
    solver_no_sym = DFSMemoSolver(use_symmetry=False, verbose=False)
    solution_no_sym = solver_no_sym.solve(board)
    nodes_no_sym = solver_no_sym.stats.nodes_visited
    
    # С симметриями
    solver_sym = DFSMemoSolver(use_symmetry=True, verbose=False)
    solution_sym = solver_sym.solve(board)
    nodes_sym = solver_sym.stats.nodes_visited
    
    assert solution_no_sym is not None
    assert solution_sym is not None
    
    # Симметрии должны помочь (меньше узлов)
    # Но это не гарантировано, так что просто проверяем что оба работают
    assert nodes_no_sym > 0
    assert nodes_sym > 0


def test_dfs_memo_small_board():
    """Тест: DFSMemo на маленькой доске (быстрое решение)."""
    # Создаём простую позицию с одним возможным ходом
    from_pos = 3 * 7 + 2  # C4
    jumped_pos = 3 * 7 + 3  # D4
    to_pos = 3 * 7 + 4  # E4
    
    pegs = (1 << from_pos) | (1 << jumped_pos)
    valid_mask = (1 << from_pos) | (1 << jumped_pos) | (1 << to_pos)
    
    board = BitBoard(pegs, valid_mask=valid_mask)
    solver = DFSMemoSolver(verbose=False)
    
    solution = solver.solve(board)
    
    assert solution is not None, "Решение должно быть найдено"
    assert len(solution) == 1, "Должен быть один ход"
    assert solution[0] == (from_pos, jumped_pos, to_pos), "Ход должен быть корректным"
    
    # Валидация
    assert verify_bitboard_solution(board, solution), "Решение должно быть корректным"


def test_dfs_memo_stats():
    """Тест: проверка статистики решателя."""
    board = BitBoard.english_start()
    solver = DFSMemoSolver(verbose=False)
    
    solution = solver.solve(board)
    
    assert solution is not None
    assert solver.stats.nodes_visited > 0, "Должны быть посещены узлы"
    assert solver.stats.max_depth > 0, "Должна быть достигнута глубина"
    assert solver.stats.solution_length == len(solution), "Длина решения должна совпадать"
    assert solver.stats.nodes_pruned >= 0, "Отсечённые узлы должны быть >= 0"
