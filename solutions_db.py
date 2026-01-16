"""
solutions_db.py

Модуль для загрузки и сохранения найденных решений (дисковый кэш).
"""

import json
import os
from utils import board_to_str

DB_FILE = "solutions_cache.json"

def load_solutions():
    """Загружает всю базу решений из файла (если она есть)."""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_solutions(solutions):
    """Сохраняет все решения в диск по пути DB_FILE."""
    with open(DB_FILE, 'w') as f:
        json.dump(solutions, f)

def get_solution(board):
    """Получить решение для данной позиции (или None).
    Args:
        board: доска (list[list[str]])
    Returns: list[str] or None
    """
    db = load_solutions()
    key = board_to_str(board)
    return db.get(key, None)

def store_solution(board, moves):
    """Записать решение для доски."""
    db = load_solutions()
    key = board_to_str(board)
    db[key] = moves
    save_solutions(db)
