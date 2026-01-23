"""
peg_io/waypoints.py

Система waypoints (опорных точек) для сложных позиций - Фаза 6.3.
Позволяет сохранять промежуточные состояния для ускорения поиска.
"""

from typing import Dict, List, Tuple, Optional, Set
from core.bitboard import BitBoard, is_english_board
from solutions.verify import verify_bitboard_solution


class WaypointDatabase:
    """
    База данных опорных точек (waypoints).
    
    Waypoints - это промежуточные состояния в известных решениях,
    которые можно использовать для ускорения поиска.
    """
    
    def __init__(self):
        # waypoints: {canonical_pegs: {'from_start': path, 'to_goal': path, 'board': BitBoard}}
        self.waypoints: Dict[int, Dict] = {}
        # Индекс по количеству колышков для быстрого поиска
        self.index_by_peg_count: Dict[int, Set[int]] = {}
    
    def add_waypoint(self, board: BitBoard, from_start: List[Tuple[int, int, int]],
                    to_goal: List[Tuple[int, int, int]]):
        """
        Добавляет waypoint в базу.
        
        Args:
            board: промежуточное состояние доски
            from_start: путь от начальной позиции до waypoint
            to_goal: путь от waypoint до цели
        """
        # Для произвольных досок используем pegs напрямую
        # Для английской доски используем canonical
        if is_english_board(board):
            key = board.canonical().pegs
        else:
            key = board.pegs
        
        self.waypoints[key] = {
            'from_start': from_start,
            'to_goal': to_goal,
            'board': board,
            'peg_count': board.peg_count()
        }
        
        # Обновляем индекс
        peg_count = board.peg_count()
        if peg_count not in self.index_by_peg_count:
            self.index_by_peg_count[peg_count] = set()
        self.index_by_peg_count[peg_count].add(key)
    
    def find_waypoint(self, board: BitBoard) -> Optional[Dict]:
        """
        Ищет waypoint для заданной позиции.
        
        Args:
            board: позиция для поиска
            
        Returns:
            Словарь с waypoint или None
        """
        # Для произвольных досок используем pegs напрямую
        # Для английской доски используем canonical
        if is_english_board(board):
            key = board.canonical().pegs
        else:
            key = board.pegs
        
        return self.waypoints.get(key)
    
    def find_waypoints_by_peg_count(self, peg_count: int) -> List[Dict]:
        """
        Находит все waypoints с заданным количеством колышков.
        
        Args:
            peg_count: количество колышков
            
        Returns:
            Список waypoints
        """
        keys = self.index_by_peg_count.get(peg_count, set())
        return [self.waypoints[key] for key in keys if key in self.waypoints]
    
    def build_from_solution(self, start_board: BitBoard, 
                           solution: List[Tuple[int, int, int]],
                           interval: int = 5):
        """
        Строит waypoints из известного решения.
        
        Args:
            start_board: начальная позиция
            solution: полное решение
            interval: интервал между waypoints (в ходах)
        """
        board = start_board
        path_from_start = []
        
        for i, move in enumerate(solution):
            path_from_start.append(move)
            board = board.apply_move(*move)
            
            # Создаём waypoint каждые interval ходов
            if (i + 1) % interval == 0 or i == len(solution) - 1:
                path_to_goal = solution[i + 1:] if i + 1 < len(solution) else []
                self.add_waypoint(board, path_from_start[:], path_to_goal)
    
    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику базы waypoints."""
        return {
            'total_waypoints': len(self.waypoints),
            'by_peg_count': {
                count: len(keys) 
                for count, keys in self.index_by_peg_count.items()
            }
        }


def build_waypoints_from_solutions(solutions: Dict[int, List[Tuple[int, int, int]]],
                                  interval: int = 5) -> WaypointDatabase:
    """
    Строит базу waypoints из словаря решений.
    
    Args:
        solutions: словарь {canonical_pegs: solution}
        interval: интервал между waypoints
        
    Returns:
        WaypointDatabase
    """
    db = WaypointDatabase()
    
    for start_pegs, solution in solutions.items():
        start_board = BitBoard(start_pegs)
        db.build_from_solution(start_board, solution, interval)
    
    return db
