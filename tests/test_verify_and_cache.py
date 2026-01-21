"""
tests/test_verify_and_cache.py

Тесты для:
- verify_bitboard_solution (валидация решений на BitBoard)
- bitboard_to_matrix + peg_io.cache (кэширование решений)
"""

from typing import List, Tuple

from core.bitboard import BitBoard
from core.utils import PEG, HOLE, EMPTY, board_to_str
from peg_io import cache as cache_module
from peg_io.cache import load_solutions, get_cached_solution, save_solution
from solutions.verify import verify_bitboard_solution, bitboard_to_matrix


def _make_simple_board() -> BitBoard:
    """
    Конструирует простую позицию с одним допустимым ходом:

    Ряд 3 (0-based):
      col=2 (C4)  - колышек (from)
      col=3 (D4)  - колышек (jumped)
      col=4 (E4)  - дырка (to)

    Ход: C4 -> E4 через D4.
    """
    pegs_bits = 0
    holes_bits = 0

    # from = (3, 2), jumped = (3, 3), to = (3, 4)
    from_pos = 3 * 7 + 2
    jumped_pos = 3 * 7 + 3
    to_pos = 3 * 7 + 4

    pegs_bits |= 1 << from_pos
    pegs_bits |= 1 << jumped_pos
    holes_bits |= 1 << to_pos

    valid_mask = pegs_bits | holes_bits
    return BitBoard(pegs_bits, valid_mask=valid_mask), (from_pos, jumped_pos, to_pos)


def test_verify_bitboard_solution_valid():
    """Корректная последовательность ходов должна проходить проверку."""
    board, move = _make_simple_board()
    moves: List[Tuple[int, int, int]] = [move]

    assert verify_bitboard_solution(board, moves) is True


def test_verify_bitboard_solution_invalid_wrong_target():
    """Ход в занятую цель или вне valid_mask должен отклоняться."""
    board, move = _make_simple_board()
    from_pos, jumped_pos, _ = move

    # Цель совпадает с occupied клеткой (from_pos) — некорректно
    bad_move = (from_pos, jumped_pos, from_pos)
    assert verify_bitboard_solution(board, [bad_move]) is False


def test_verify_bitboard_solution_invalid_out_of_range():
    """Позиции вне диапазона 0..48 должны отклоняться."""
    board, move = _make_simple_board()
    from_pos, jumped_pos, to_pos = move

    bad_move = (from_pos, jumped_pos, 100)  # вне диапазона
    assert verify_bitboard_solution(board, [bad_move]) is False


def test_bitboard_to_matrix_and_cache_roundtrip(tmp_path, monkeypatch):
    """
    Проверяет, что:
    - bitboard_to_matrix создаёт корректную матрицу (PEG/HOLE/EMPTY);
    - save_solution / get_cached_solution работают с этой матрицей,
      используя board_to_str как ключ.
    """
    # Перенастраиваем файл кэша на временный
    cache_file = tmp_path / "solutions_cache_test.json"
    monkeypatch.setattr(cache_module, "CACHE_FILE", str(cache_file), raising=True)

    board, move = _make_simple_board()

    # Строим матрицу из BitBoard
    matrix = bitboard_to_matrix(board)

    # Проверяем семантику матрицы: from/jumped = PEG, to = HOLE
    from_pos, jumped_pos, to_pos = move
    fr, fc = divmod(from_pos, 7)
    jr, jc = divmod(jumped_pos, 7)
    tr, tc = divmod(to_pos, 7)

    assert matrix[fr][fc] == PEG
    assert matrix[jr][jc] == PEG
    assert matrix[tr][tc] == HOLE

    # Подготавливаем решение в строковом формате
    moves_str = ["C4 → E4"]

    # Сохраняем решение и проверяем, что оно попало в кэш
    save_solution(matrix, moves_str)

    db = load_solutions()
    key = board_to_str(matrix)
    assert key in db
    assert db[key] == moves_str

    # Проверяем удобный доступ через get_cached_solution
    cached = get_cached_solution(matrix)
    assert cached == moves_str

