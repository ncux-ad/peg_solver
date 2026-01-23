"""
peg_io/notation_parser.py

Парсинг координатного формата доски.
Формат: "A1 B2 C3 D4(hole) E5..."
"""

import re
from typing import Tuple, List
from core.bitboard import BitBoard


def parse_notation(notation: str) -> BitBoard:
    """
    Парсит координатное описание доски.
    
    Формат: "A1 B2 C3 D4(hole) E5..." где:
    - A1, B2, C3 - колышки (pegs)
    - D4(hole), E5(hole) - пустые места (holes)
    
    Args:
        notation: строка с координатами
        
    Returns:
        BitBoard
    """
    pegs_bits = 0
    holes_bits = 0
    
    if not notation or not notation.strip():
        raise ValueError("Пустое описание доски")
    
    # Разбиваем по пробелам
    parts = notation.strip().split()
    
    for part in parts:
        # Проверяем формат: буква + цифра + опционально (hole)
        match = re.match(r'^([A-G])([1-7])(\(hole\))?$', part, re.IGNORECASE)
        
        if match:
            letter = match.group(1).upper()
            number = int(match.group(2))
            is_hole = match.group(3) is not None
            
            # Преобразуем в индексы
            col = ord(letter) - ord('A')  # A=0, B=1, ..., G=6
            row = number - 1  # 1=0, 2=1, ..., 7=6
            
            # Проверяем валидность
            if 0 <= row < 7 and 0 <= col < 7:
                pos = row * 7 + col
                if is_hole:
                    holes_bits |= (1 << pos)
                else:
                    pegs_bits |= (1 << pos)
            else:
                raise ValueError(f"Некорректные координаты: {part}")
        else:
            raise ValueError(f"Не удалось распарсить: {part}")
    
    # valid_mask = все позиции где есть колышки или дырки
    valid_mask = pegs_bits | holes_bits
    
    return BitBoard(pegs_bits, valid_mask=valid_mask if valid_mask else None)
