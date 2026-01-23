"""
peg_io/cache_enhanced.py

Улучшенная система кэширования решений - Фаза 6.
Включает метаданные, атомарную запись, версионирование.
"""

import json
import os
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.utils import board_to_str

CACHE_FILE = "solutions_cache.json"
CACHE_VERSION = 1


class SolutionMetadata:
    """Метаданные решения."""
    
    def __init__(self, moves: List[str], solver: str = "unknown", 
                 time_elapsed: float = 0.0, move_count: int = 0,
                 timestamp: Optional[str] = None):
        self.moves = moves
        self.solver = solver
        self.time_elapsed = time_elapsed
        self.move_count = move_count or len(moves)
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь для JSON."""
        return {
            'moves': self.moves,
            'solver': self.solver,
            'time_elapsed': self.time_elapsed,
            'move_count': self.move_count,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SolutionMetadata':
        """Создаёт из словаря."""
        return cls(
            moves=data.get('moves', []),
            solver=data.get('solver', 'unknown'),
            time_elapsed=data.get('time_elapsed', 0.0),
            move_count=data.get('move_count', len(data.get('moves', []))),
            timestamp=data.get('timestamp')
        )


def load_solutions_enhanced() -> Dict[str, SolutionMetadata]:
    """
    Загружает все решения из кэша с метаданными.
    
    Returns:
        Словарь: board_key -> SolutionMetadata
    """
    if not os.path.exists(CACHE_FILE):
        return {}
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Проверка версии
        version = data.get('version', 0)
        if version != CACHE_VERSION:
            # Миграция старого формата
            return _migrate_old_format(data)
        
        solutions = {}
        for key, value in data.get('solutions', {}).items():
            if isinstance(value, dict) and 'moves' in value:
                # Новый формат с метаданными
                solutions[key] = SolutionMetadata.from_dict(value)
            elif isinstance(value, list):
                # Старый формат (только список ходов)
                solutions[key] = SolutionMetadata(moves=value)
        
        return solutions
    except (json.JSONDecodeError, IOError, KeyError) as e:
        print(f"Error loading cache: {e}")
        return {}


def _migrate_old_format(data: Dict) -> Dict[str, SolutionMetadata]:
    """Мигрирует старый формат кэша в новый."""
    solutions = {}
    
    # Старый формат: {"board_key": ["move1", "move2", ...]}
    # Новый формат: {"version": 1, "solutions": {"board_key": {...}}}
    if 'solutions' not in data:
        # Старый формат без версии
        for key, value in data.items():
            if isinstance(value, list):
                solutions[key] = SolutionMetadata(moves=value)
    else:
        # Частично новый формат
        for key, value in data['solutions'].items():
            if isinstance(value, list):
                solutions[key] = SolutionMetadata(moves=value)
            elif isinstance(value, dict):
                solutions[key] = SolutionMetadata.from_dict(value)
    
    return solutions


def save_solutions_enhanced(solutions: Dict[str, SolutionMetadata]) -> None:
    """
    Сохраняет решения в кэш с атомарной записью.
    
    Args:
        solutions: словарь решений
    """
    # Подготавливаем данные
    data = {
        'version': CACHE_VERSION,
        'last_updated': datetime.now().isoformat(),
        'solutions': {key: metadata.to_dict() for key, metadata in solutions.items()}
    }
    
    # Атомарная запись через временный файл
    temp_file = None
    try:
        # Создаём временный файл в той же директории
        temp_fd, temp_file = tempfile.mkstemp(
            suffix='.json',
            dir=os.path.dirname(CACHE_FILE) if os.path.dirname(CACHE_FILE) else '.',
            text=True
        )
        
        # Записываем во временный файл
        with open(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Атомарно переименовываем
        shutil.move(temp_file, CACHE_FILE)
        temp_file = None  # Успешно перемещён
    except Exception as e:
        print(f"Error saving cache: {e}")
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        raise


def get_cached_solution_enhanced(board: List[List[str]], 
                                 prefer_shorter: bool = True) -> Optional[SolutionMetadata]:
    """
    Получает решение из кэша с метаданными.
    
    Args:
        board: доска в матричном формате
        prefer_shorter: если True, выбирает кратчайшее решение при наличии нескольких
        
    Returns:
        SolutionMetadata или None
    """
    db = load_solutions_enhanced()
    key = board_to_str(board)
    
    solution = db.get(key)
    if solution:
        return solution
    
    # Если prefer_shorter и есть несколько решений (в будущем можно расширить)
    # Пока возвращаем первое найденное
    
    return None


def save_solution_enhanced(board: List[List[str]], moves: List[str],
                          solver: str = "unknown", time_elapsed: float = 0.0) -> None:
    """
    Сохраняет решение в кэш с метаданными.
    
    Args:
        board: начальная позиция
        moves: список ходов
        solver: имя решателя
        time_elapsed: время решения в секундах
    """
    db = load_solutions_enhanced()
    key = board_to_str(board)
    
    # Проверяем, есть ли уже решение
    existing = db.get(key)
    if existing:
        # Если новое решение короче, заменяем
        if len(moves) < existing.move_count:
            db[key] = SolutionMetadata(
                moves=moves,
                solver=solver,
                time_elapsed=time_elapsed,
                move_count=len(moves)
            )
        # Иначе оставляем существующее
    else:
        # Новое решение
        db[key] = SolutionMetadata(
            moves=moves,
            solver=solver,
            time_elapsed=time_elapsed,
            move_count=len(moves)
        )
    
    save_solutions_enhanced(db)


def get_cache_stats() -> Dict[str, Any]:
    """
    Возвращает статистику кэша.
    
    Returns:
        Словарь со статистикой
    """
    solutions = load_solutions_enhanced()
    
    if not solutions:
        return {
            'total_solutions': 0,
            'total_moves': 0,
            'average_moves': 0.0,
            'solvers': {},
            'oldest': None,
            'newest': None
        }
    
    total_moves = sum(meta.move_count for meta in solutions.values())
    solvers = {}
    timestamps = []
    
    for meta in solutions.values():
        solvers[meta.solver] = solvers.get(meta.solver, 0) + 1
        if meta.timestamp:
            timestamps.append(meta.timestamp)
    
    return {
        'total_solutions': len(solutions),
        'total_moves': total_moves,
        'average_moves': total_moves / len(solutions) if solutions else 0.0,
        'solvers': solvers,
        'oldest': min(timestamps) if timestamps else None,
        'newest': max(timestamps) if timestamps else None
    }
