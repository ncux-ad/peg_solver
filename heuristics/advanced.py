"""
heuristics/advanced.py

Продвинутые эвристики для оценки позиций.
"""

from core.bitboard import BitBoard, ENGLISH_VALID_POSITIONS


def heuristic_mobility(board: BitBoard) -> int:
    """
    Количество доступных ходов (мобильность).
    Больше ходов = больше гибкости = лучше.
    """
    return len(board.get_moves())


def heuristic_isolated(board: BitBoard) -> int:
    """
    Количество изолированных колышков (без соседей).
    Изолированные колышки — проблема.
    """
    count = 0
    for pos in ENGLISH_VALID_POSITIONS:
        if not board.has_peg(pos):
            continue
        
        r, c = pos // 7, pos % 7
        has_neighbor = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            neighbor_pos = nr * 7 + nc
            if neighbor_pos in ENGLISH_VALID_POSITIONS and board.has_peg(neighbor_pos):
                has_neighbor = True
                break
        
        if not has_neighbor:
            count += 1
    
    return count


def heuristic_cluster(board: BitBoard) -> int:
    """
    Подсчёт соседних пар колышков (кластеризация).
    Больше пар = лучше (колышки рядом легче убирать).
    """
    pairs = 0
    for pos in ENGLISH_VALID_POSITIONS:
        if not board.has_peg(pos):
            continue
        
        r, c = pos // 7, pos % 7
        # Считаем только вправо и вниз (чтобы не дублировать)
        for dr, dc in [(0, 1), (1, 0)]:
            nr, nc = r + dr, c + dc
            neighbor_pos = nr * 7 + nc
            if neighbor_pos in ENGLISH_VALID_POSITIONS and board.has_peg(neighbor_pos):
                pairs += 1
    
    return pairs


def heuristic_edge_penalty(board: BitBoard) -> int:
    """
    Штраф за колышки на краях доски.
    Краевые колышки сложнее использовать.
    """
    penalty = 0
    edge_positions = {2, 4, 9, 11, 14, 20, 21, 27, 28, 34, 37, 39, 44, 46}
    
    for pos in edge_positions:
        if board.has_peg(pos):
            penalty += 1
    
    return penalty
