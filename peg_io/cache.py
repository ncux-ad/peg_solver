"""
io/cache.py

Кэширование решений на диск.
"""

import json
import os
from typing import Dict, List, Optional

from core.utils import board_to_str

CACHE_FILE = "solutions_cache.json"


def load_solutions() -> Dict[str, List[str]]:
    """Загружает все решения из кэша."""
    if not os.path.exists(CACHE_FILE):
        return {}
    
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_solutions(solutions: Dict[str, List[str]]) -> None:
    """Сохраняет все решения в кэш."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(solutions, f, indent=2)


def get_cached_solution(board: List[List[str]]) -> Optional[List[str]]:
    """
    Получает решение из кэша.
    
    Args:
        board: доска
        
    Returns:
        Список ходов или None
    """
    db = load_solutions()
    key = board_to_str(board)
    return db.get(key)


def save_solution(board: List[List[str]], moves: List[str]) -> None:
    """
    Сохраняет решение в кэш.
    
    Args:
        board: начальная позиция
        moves: список ходов
    """
    db = load_solutions()
    key = board_to_str(board)
    db[key] = moves
    save_solutions(db)
