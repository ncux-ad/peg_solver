"""
solvers/beam.py

Beam Search — ограниченный по ширине поиск.
"""

from typing import List, Tuple, Optional

from .base import BaseSolver, SolverStats
from core.bitboard import (
    BitBoard, ENGLISH_VALID_POSITIONS, CENTER_POS,
    get_valid_positions, is_english_board, get_center_position
)
from heuristics import pagoda_value, PAGODA_WEIGHTS
from .optimized_utils import evaluate_position_optimized


class BeamSolver(BaseSolver):
    """
    Beam Search решатель.
    
    Сохраняет только K лучших состояний на каждом уровне.
    
    Плюсы:
    - Контролируемый расход памяти
    - Быстрее чем полный BFS
    
    Минусы:
    - Может пропустить решение (неполный алгоритм)
    """
    
    def __init__(self, beam_width: int = 100, max_depth: int = 35,
                 use_symmetry: bool = True, verbose: bool = False):
        super().__init__(use_symmetry, verbose)
        self.beam_width = beam_width
        self.max_depth = max_depth
    
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        self.stats = SolverStats()
        
        self._log(f"Starting Beam Search (width={self.beam_width})")
        
        beam = [(board, [])]
        visited = {self._get_key(board)}
        
        for depth in range(self.max_depth):
            if not beam:
                break
            
            self.stats.max_depth = depth
            candidates = []
            
            for current, path in beam:
                self.stats.nodes_visited += 1
                
                if current.peg_count() == 1:
                    self.stats.solution_length = len(path)
                    self._log(f"Found at depth {depth}! {self.stats}")
                    return path
                
                for move in current.get_moves():
                    new_board = current.apply_move(*move)
                    key = self._get_key(new_board)
                    
                    if key in visited:
                        continue
                    visited.add(key)
                    
                    # Используем оптимизированную версию оценки
                    num_moves = len(new_board.get_moves())
                    score = evaluate_position_optimized(new_board, num_moves)
                    candidates.append((score, new_board, path + [move]))
            
            # Оставляем лучшие
            candidates.sort(key=lambda x: x[0])
            beam = [(b, p) for _, b, p in candidates[:self.beam_width]]
            
            if depth % 5 == 0:
                self._log(f"Depth {depth}, beam: {len(beam)}")
        
        self._log(f"No solution. {self.stats}")
        return None
    
    def _evaluate(self, board: BitBoard) -> float:
        """Оценка позиции (меньше = лучше).
        
        Автоматически использует оптимизированную версию (Numba/Rust) если доступна.
        """
        # Пробуем использовать оптимизированную функцию оценки
        try:
            from heuristics.evaluation import evaluate_position
            base_score = evaluate_position(board)
            
            # Добавляем изолированные колышки (дополнительная эвристика)
            isolated_penalty = self._count_isolated(board) * 15
            return base_score + isolated_penalty
        except ImportError:
            pass
        
        # Fallback на оригинальную версию
        score = board.peg_count() * 10
        
        # Расстояние до центра
        center_pos = get_center_position(board)
        if center_pos is not None:
            center_r, center_c = center_pos // 7, center_pos % 7
            valid_positions = get_valid_positions(board)
            for pos in valid_positions:
                if board.has_peg(pos):
                    r, c = pos // 7, pos % 7
                    score += abs(r - center_r) + abs(c - center_c)
        
        # Мобильность
        score -= len(board.get_moves()) * 2
        
        # Изолированные колышки
        score += self._count_isolated(board) * 15
        
        # Pagoda (только для английской доски)
        if is_english_board(board):
            min_pagoda = min(PAGODA_WEIGHTS.values())
            current_pagoda = pagoda_value(board)
            
            if board.peg_count() > 15:
                # В начале: строгая проверка
                if current_pagoda < PAGODA_WEIGHTS[CENTER_POS]:
                    score += 1000
            else:
                # Ближе к концу: мягкая проверка
                if current_pagoda < min_pagoda:
                    score += 1000
        
        return score
    
    def _count_isolated(self, board: BitBoard) -> int:
        """Количество изолированных колышков (оптимизированная версия)."""
        count = 0
        pegs = board.pegs
        valid_positions = get_valid_positions(board)
        
        # Предвычисляем соседей для каждой позиции
        for pos in valid_positions:
            if not (pegs & (1 << pos)):
                continue
            
            r, c = pos // 7, pos % 7
            # Проверяем соседей битовыми операциями
            has_neighbor = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                neighbor_pos = nr * 7 + nc
                if neighbor_pos in valid_positions and (pegs & (1 << neighbor_pos)):
                    has_neighbor = True
                    break
            
            if not has_neighbor:
                count += 1
        
        return count
