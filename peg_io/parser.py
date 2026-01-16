"""
io/parser.py

Парсинг входных данных.
"""

import re
from typing import List

from core.utils import PEG, HOLE, EMPTY


def parse_input(text: str) -> List[List[str]]:
    """
    Парсит текстовый формат описания позиции.
    
    Формат: size=7x7 pegs=A2,A6,... empty=D4
    
    Args:
        text: строка с описанием
        
    Returns:
        Игровое поле в матричном представлении
    """
    size_match = re.search(r'size=(\d+)x(\d+)', text)
    pegs_match = re.search(r'pegs=([\w,]+)', text)
    empty_match = re.search(r'empty=([\w,]+)', text)
    
    if not size_match or not pegs_match or not empty_match:
        raise ValueError(
            "Неверный формат. Ожидается: size=NxM pegs=A1,A2,... empty=D4"
        )
    
    rows, cols = int(size_match.group(1)), int(size_match.group(2))
    pegs = pegs_match.group(1).split(',')
    empty = empty_match.group(1).split(',')
    
    board = [[EMPTY for _ in range(cols)] for _ in range(rows)]
    
    for pos in pegs:
        pos = pos.strip()
        if not pos:
            continue
        col = ord(pos[0].upper()) - ord('A')
        row = int(pos[1:]) - 1
        if 0 <= row < rows and 0 <= col < cols:
            board[row][col] = PEG
    
    for pos in empty:
        pos = pos.strip()
        if not pos:
            continue
        col = ord(pos[0].upper()) - ord('A')
        row = int(pos[1:]) - 1
        if 0 <= row < rows and 0 <= col < cols:
            board[row][col] = HOLE
    
    return board


def create_english_board() -> List[List[str]]:
    """
    Создаёт стандартную английскую доску 7x7 с пустым центром.
    """
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
                row.append(EMPTY)
            elif r == 3 and c == 3:
                row.append(HOLE)
            else:
                row.append(PEG)
        board.append(row)
    
    return board
