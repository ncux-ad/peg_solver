"""
solvers/base.py

Базовый класс для всех решателей.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
import time

from core.bitboard import BitBoard


@dataclass
class SolverStats:
    """Статистика работы решателя."""
    nodes_visited: int = 0
    nodes_pruned: int = 0
    max_depth: int = 0
    time_elapsed: float = 0.0
    solution_length: int = 0
    
    def __str__(self) -> str:
        return (
            f"Nodes: {self.nodes_visited}, "
            f"Pruned: {self.nodes_pruned}, "
            f"Depth: {self.max_depth}, "
            f"Time: {self.time_elapsed:.3f}s"
        )


class BaseSolver(ABC):
    """
    Базовый класс решателя.
    
    Все решатели наследуют от него и реализуют метод solve().
    """
    
    def __init__(self, use_symmetry: bool = True, verbose: bool = False):
        self.use_symmetry = use_symmetry
        self.verbose = verbose
        self.stats = SolverStats()
    
    @abstractmethod
    def solve(self, board: BitBoard) -> Optional[List[Tuple[int, int, int]]]:
        """
        Решает головоломку.
        
        Args:
            board: начальная позиция
            
        Returns:
            Список ходов (from, jumped, to) или None
        """
        pass
    
    def _log(self, message: str) -> None:
        """Выводит сообщение если verbose=True."""
        if self.verbose:
            print(f"  [{self.__class__.__name__}] {message}")
    
    def _get_key(self, board: BitBoard) -> int:
        """Возвращает ключ для visited set."""
        if self.use_symmetry:
            return board.canonical().pegs
        return board.pegs
    
    @staticmethod
    def format_move(from_pos: int, jumped: int, to_pos: int) -> str:
        """Форматирует ход для вывода."""
        fr, fc = from_pos // 7, from_pos % 7
        tr, tc = to_pos // 7, to_pos % 7
        return f"{chr(fc + ord('A'))}{fr + 1} → {chr(tc + ord('A'))}{tr + 1}"
    
    @staticmethod
    def format_solution(moves: List[Tuple[int, int, int]]) -> List[str]:
        """Форматирует список ходов."""
        return [BaseSolver.format_move(*m) for m in moves]
