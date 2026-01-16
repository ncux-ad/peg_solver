"""
core - Ядро Peg Solitaire

Базовые структуры данных и утилиты.
"""

from .board import Board
from .bitboard import BitBoard, ENGLISH_VALID_POSITIONS, CENTER_POS
from .zobrist import ZobristBitBoard, compute_zobrist_hash, update_zobrist_hash
from .utils import (
    DIRECTIONS, PEG, HOLE, EMPTY,
    board_to_str, index_to_pos, pos_to_index,
    count_pegs
)

__all__ = [
    'Board', 'BitBoard', 'ZobristBitBoard',
    'compute_zobrist_hash', 'update_zobrist_hash',
    'ENGLISH_VALID_POSITIONS', 'CENTER_POS',
    'DIRECTIONS', 'PEG', 'HOLE', 'EMPTY',
    'board_to_str', 'index_to_pos', 'pos_to_index', 'count_pegs'
]
