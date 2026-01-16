"""
io/visualizer.py

Визуализация доски и решений.
"""

from typing import List, Optional


def display_board(board: List[List[str]]) -> str:
    """
    Красиво форматирует текстовое представление доски.
    
    Args:
        board: матрица доски
        
    Returns:
        Строка для вывода
    """
    cols = len(board[0]) if board else 0
    header = "   " + " ".join(chr(c + ord('A')) for c in range(cols))
    lines = [header]
    
    for r, row in enumerate(board):
        row_str = f"{r + 1:<2} " + " ".join(row)
        lines.append(row_str)
    
    return "\n".join(lines)


def format_solution(moves: Optional[List[str]]) -> str:
    """
    Форматирует список ходов для вывода.
    
    Args:
        moves: список ходов или None
        
    Returns:
        Форматированная строка
    """
    if not moves:
        return "❌ Решение не найдено"
    
    lines = [f"✅ Найдено решение за {len(moves)} ходов:"]
    for i, move in enumerate(moves, 1):
        lines.append(f"  {i:2}. {move}")
    
    return "\n".join(lines)


def format_bitboard_solution(moves: List[tuple]) -> List[str]:
    """
    Форматирует решение из BitBoard формата.
    
    Args:
        moves: список (from, jumped, to)
        
    Returns:
        Список строк ходов
    """
    result = []
    for from_pos, _, to_pos in moves:
        fr, fc = from_pos // 7, from_pos % 7
        tr, tc = to_pos // 7, to_pos % 7
        from_str = f"{chr(fc + ord('A'))}{fr + 1}"
        to_str = f"{chr(tc + ord('A'))}{tr + 1}"
        result.append(f"{from_str} → {to_str}")
    return result
