#!/usr/bin/env python3
"""
cli_simple.py

Простой CLI интерфейс для Фазы 1 разработки.
Минимальный рабочий прототип для тестирования SimpleDFSSolver.
"""

import sys
import time
from core.bitboard import BitBoard
from solvers.simple_dfs import SimpleDFSSolver
from solutions.verify import verify_bitboard_solution


def main():
    """Основная функция CLI."""
    print("=" * 60)
    print("Peg Solitaire Solver - Фаза 1: Минимальный прототип")
    print("=" * 60)
    print()
    
    # Создаём стандартную английскую доску
    board = BitBoard.english_start()
    
    print("Начальная позиция:")
    print(board.to_string())
    print(f"Колышков: {board.peg_count()}")
    print()
    
    # Создаём решатель
    solver = SimpleDFSSolver(verbose=True)
    
    # Решаем
    print("Запуск Simple DFS...")
    print("-" * 60)
    start_time = time.time()
    solution = solver.solve(board)
    elapsed = time.time() - start_time
    print("-" * 60)
    print()
    
    # Результаты
    if solution is None:
        print("❌ Решение не найдено")
        print(f"⏱ Время: {elapsed:.3f}с")
        print(f"📊 Статистика: {solver.stats}")
        return 1
    
    print("✅ Решение найдено!")
    print(f"📏 Длина решения: {len(solution)} ходов")
    print(f"⏱ Время: {elapsed:.3f}с")
    print(f"📊 Статистика: {solver.stats}")
    print()
    
    # Валидация
    print("Проверка корректности решения...")
    is_valid = verify_bitboard_solution(board, solution)
    if is_valid:
        print("✅ Решение корректно!")
    else:
        print("❌ Решение некорректно!")
        return 1
    
    # Показываем первые несколько ходов
    print()
    print("Первые 5 ходов:")
    for i, (from_pos, jumped, to_pos) in enumerate(solution[:5], 1):
        from_r, from_c = from_pos // 7, from_pos % 7
        to_r, to_c = to_pos // 7, to_pos % 7
        move_str = f"{chr(from_c + ord('A'))}{from_r + 1} → {chr(to_c + ord('A'))}{to_r + 1}"
        print(f"  {i}. {move_str}")
    
    if len(solution) > 5:
        print(f"  ... и ещё {len(solution) - 5} ходов")
    
    # Проверяем финальное состояние
    print()
    print("Проверка финального состояния...")
    final_board = board
    for move in solution:
        final_board = final_board.apply_move(*move)
    
    print("Финальная позиция:")
    print(final_board.to_string())
    print(f"Колышков: {final_board.peg_count()}")
    
    if final_board.peg_count() == 1:
        print("✅ Успешно! Остался один колышек.")
    else:
        print(f"❌ Ошибка! Осталось {final_board.peg_count()} колышков.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
