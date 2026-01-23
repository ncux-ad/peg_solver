"""
heuristics/arbitrary.py

Эвристики адаптированные для произвольных досок.
Используют get_valid_positions вместо ENGLISH_VALID_POSITIONS.
"""

from core.bitboard import BitBoard, get_valid_positions, get_center_position


def heuristic_distance_to_center_arbitrary(board: BitBoard) -> float:
    """
    Суммарное манхэттенское расстояние колышков до центра.
    Адаптировано для произвольных досок.
    
    Args:
        board: состояние доски
        
    Returns:
        Суммарное расстояние до центра
    """
    center_pos = get_center_position(board)
    if center_pos is None:
        return 0.0
    
    center_r, center_c = center_pos // 7, center_pos % 7
    valid_positions = get_valid_positions(board)
    total = 0.0
    
    for pos in valid_positions:
        if board.has_peg(pos):
            r, c = pos // 7, pos % 7
            total += abs(r - center_r) + abs(c - center_c)
    
    return total


def heuristic_isolated_arbitrary(board: BitBoard) -> int:
    """
    Количество изолированных колышков (без соседей).
    Адаптировано для произвольных досок.
    
    Args:
        board: состояние доски
        
    Returns:
        Количество изолированных колышков
    """
    count = 0
    valid_positions = get_valid_positions(board)
    
    for pos in valid_positions:
        if not board.has_peg(pos):
            continue
        
        r, c = pos // 7, pos % 7
        has_neighbor = False
        
        # Проверяем соседей в 4 направлениях
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            neighbor_pos = nr * 7 + nc
            
            # Проверяем, что сосед в валидных позициях и есть колышек
            if neighbor_pos in valid_positions and board.has_peg(neighbor_pos):
                has_neighbor = True
                break
        
        if not has_neighbor:
            count += 1
    
    return count


def heuristic_cluster_arbitrary(board: BitBoard) -> int:
    """
    Подсчёт соседних пар колышков (кластеризация).
    Адаптировано для произвольных досок.
    
    Args:
        board: состояние доски
        
    Returns:
        Количество соседних пар
    """
    pairs = 0
    valid_positions = get_valid_positions(board)
    
    for pos in valid_positions:
        if not board.has_peg(pos):
            continue
        
        r, c = pos // 7, pos % 7
        # Считаем только вправо и вниз (чтобы не дублировать)
        for dr, dc in [(0, 1), (1, 0)]:
            nr, nc = r + dr, c + dc
            neighbor_pos = nr * 7 + nc
            
            if neighbor_pos in valid_positions and board.has_peg(neighbor_pos):
                pairs += 1
    
    return pairs


def heuristic_mobility_arbitrary(board: BitBoard) -> int:
    """
    Количество доступных ходов (мобильность).
    Работает для произвольных досок (использует board.get_moves()).
    
    Args:
        board: состояние доски
        
    Returns:
        Количество доступных ходов
    """
    return len(board.get_moves())


def combined_heuristic_arbitrary(board: BitBoard, steps: int = 0, 
                                  aggressive: bool = False) -> float:
    """
    Комбинированная эвристика для произвольных досок.
    
    f(n) = g(n) + h(n)
    
    Args:
        board: состояние доски
        steps: количество сделанных ходов (g(n))
        aggressive: использовать агрессивные веса
        
    Returns:
        Комбинированная оценка
    """
    from .basic import heuristic_peg_count
    
    h = heuristic_peg_count(board)  # Работает для любых досок
    
    # Добавляем расстояние до центра
    dist = heuristic_distance_to_center_arbitrary(board)
    if aggressive:
        h += dist * 0.5
    else:
        h += dist * 0.3
    
    # Добавляем изолированные колышки
    isolated = heuristic_isolated_arbitrary(board)
    if aggressive:
        h += isolated * 1.5
    else:
        h += isolated * 0.5
    
    # Вычитаем мобильность (больше ходов = лучше)
    mobility = heuristic_mobility_arbitrary(board)
    if aggressive:
        h -= mobility * 2
    else:
        h -= mobility * 0.5
    
    return steps + h
