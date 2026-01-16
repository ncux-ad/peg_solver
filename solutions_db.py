# solutions_db.py

import json
import os
from utils import board_to_str

DB_FILE = "solutions_cache.json"

def load_solutions():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_solutions(solutions):
    with open(DB_FILE, 'w') as f:
        json.dump(solutions, f)

def get_solution(board):
    db = load_solutions()
    key = board_to_str(board)
    return db.get(key, None)

def store_solution(board, moves):
    db = load_solutions()
    key = board_to_str(board)
    db[key] = moves
    save_solutions(db)
