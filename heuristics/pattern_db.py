"""
heuristics/pattern_db.py

Pattern Database (PDB) — предвычисленные эвристики.

Идея:
1. Разбиваем доску на несколько регионов
2. Для каждого региона предвычисляем min_moves до очистки
3. Сумма по регионам = admissible эвристика для A*

Это даёт очень сильную нижнюю границу!
"""

from typing import Dict, List, Tuple, Set, Optional
from collections import deque
import pickle
import os

from core.bitboard import ENGLISH_VALID_POSITIONS, CENTER_POS

# =====================================================
# РАЗБИЕНИЕ ДОСКИ НА РЕГИОНЫ
# =====================================================

# Английская доска (33 позиции) разбита на 4 региона:
#
#       2  3  4
#       9 10 11
# 14 15 16 17 18 19 20
# 21 22 23 24 25 26 27
# 28 29 30 31 32 33 34
#      37 38 39
#      44 45 46

# Регион 1: верхний крест (6 позиций)
REGION_TOP = frozenset([2, 3, 4, 9, 10, 11])

# Регион 2: нижний крест (6 позиций)
REGION_BOTTOM = frozenset([37, 38, 39, 44, 45, 46])

# Регион 3: левый край (6 позиций)
REGION_LEFT = frozenset([14, 15, 21, 22, 28, 29])

# Регион 4: правый край (6 позиций)
REGION_RIGHT = frozenset([19, 20, 26, 27, 33, 34])

# Регион 5: центр (9 позиций) — самый важный
REGION_CENTER = frozenset([16, 17, 18, 23, 24, 25, 30, 31, 32])

# Все регионы
REGIONS = [REGION_TOP, REGION_BOTTOM, REGION_LEFT, REGION_RIGHT, REGION_CENTER]
REGION_NAMES = ["TOP", "BOTTOM", "LEFT", "RIGHT", "CENTER"]


def extract_region_state(pegs: int, region: frozenset) -> int:
    """
    Извлекает состояние региона из полной битовой маски.
    
    Returns:
        Битовая маска только для позиций в регионе
    """
    state = 0
    for i, pos in enumerate(sorted(region)):
        if pegs & (1 << pos):
            state |= (1 << i)
    return state


def region_peg_count(state: int, region_size: int) -> int:
    """Количество колышков в состоянии региона."""
    return bin(state).count('1')


# =====================================================
# ПОСТРОЕНИЕ PATTERN DATABASE
# =====================================================

class PatternDatabase:
    """
    База данных паттернов для эвристики.
    
    Для каждого региона хранит: state → min_moves_to_clear
    """
    
    def __init__(self):
        self.databases: Dict[str, Dict[int, int]] = {}
        self.regions = dict(zip(REGION_NAMES, REGIONS))
    
    def build_region_db(self, region_name: str, verbose: bool = True) -> Dict[int, int]:
        """
        Строит БД для одного региона методом обратного BFS.
        
        Начинаем с пустого региона (0 колышков) и идём назад,
        добавляя колышки через "обратные ходы".
        """
        region = self.regions[region_name]
        region_list = sorted(region)
        region_size = len(region)
        
        if verbose:
            print(f"  Building {region_name} ({region_size} positions)...")
        
        db: Dict[int, int] = {}
        
        # BFS от пустого состояния
        # Пустое состояние = 0, требует 0 ходов
        db[0] = 0
        queue = deque([0])
        
        while queue:
            state = queue.popleft()
            current_cost = db[state]
            
            # Генерируем "обратные ходы" — добавляем колышки
            for i in range(region_size):
                if state & (1 << i):
                    continue  # уже есть колышек
                
                # Добавляем колышек на позицию i
                new_state = state | (1 << i)
                
                if new_state not in db:
                    db[new_state] = current_cost + 1
                    queue.append(new_state)
        
        if verbose:
            print(f"    States: {len(db)}, Max cost: {max(db.values())}")
        
        self.databases[region_name] = db
        return db
    
    def build_all(self, verbose: bool = True) -> None:
        """Строит БД для всех регионов."""
        if verbose:
            print("Building Pattern Databases...")
        
        for name in REGION_NAMES:
            self.build_region_db(name, verbose)
        
        if verbose:
            total = sum(len(db) for db in self.databases.values())
            print(f"Total states: {total}")
    
    def get_heuristic(self, pegs: int) -> int:
        """
        Вычисляет эвристику как сумму по всем регионам.
        
        Это admissible (допустимая) эвристика!
        """
        total = 0
        for name, region in self.regions.items():
            if name not in self.databases:
                continue
            
            state = extract_region_state(pegs, region)
            cost = self.databases[name].get(state, 0)
            total += cost
        
        return total
    
    def save(self, filepath: str = "pattern_db.pkl") -> None:
        """Сохраняет БД на диск."""
        with open(filepath, 'wb') as f:
            pickle.dump(self.databases, f)
        print(f"Saved to {filepath}")
    
    def load(self, filepath: str = "pattern_db.pkl") -> bool:
        """Загружает БД с диска."""
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'rb') as f:
            self.databases = pickle.load(f)
        return True


# =====================================================
# УЛУЧШЕННАЯ ЭВРИСТИКА С PDB
# =====================================================

# Глобальная БД (ленивая инициализация)
_pattern_db: Optional[PatternDatabase] = None


def get_pattern_db() -> PatternDatabase:
    """Получает или создаёт Pattern Database."""
    global _pattern_db
    
    if _pattern_db is None:
        _pattern_db = PatternDatabase()
        
        # Пробуем загрузить с диска
        if not _pattern_db.load():
            # Строим заново
            _pattern_db.build_all(verbose=True)
            _pattern_db.save()
    
    return _pattern_db


def pattern_heuristic(pegs: int) -> int:
    """
    Эвристика на основе Pattern Database.
    
    Возвращает нижнюю границу числа ходов до решения.
    """
    db = get_pattern_db()
    return db.get_heuristic(pegs)


# =====================================================
# КОМБИНИРОВАННАЯ ЭВРИСТИКА
# =====================================================

def combined_pattern_heuristic(pegs: int, steps: int) -> float:
    """
    Комбинированная эвристика для A*.
    
    f(n) = g(n) + h(n)
    h(n) = max(pattern_heuristic, peg_count - 1)
    """
    from .pagoda import pagoda_value, PAGODA_WEIGHTS
    from core.bitboard import BitBoard
    
    # Базовая эвристика
    peg_count = bin(pegs).count('1')
    base_h = peg_count - 1
    
    # Pattern heuristic
    pattern_h = pattern_heuristic(pegs)
    
    # Берём максимум (обе admissible → max тоже admissible)
    h = max(base_h, pattern_h)
    
    return steps + h


# =====================================================
# ТЕСТИРОВАНИЕ
# =====================================================

if __name__ == "__main__":
    print("Pattern Database Test")
    print("=" * 50)
    
    # Создаём БД
    db = PatternDatabase()
    db.build_all()
    
    # Тестируем на начальной позиции
    from core.bitboard import ENGLISH_START
    
    h = db.get_heuristic(ENGLISH_START)
    print(f"\nEnglish start heuristic: {h}")
    
    # Сохраняем
    db.save()
    
    # Проверяем загрузку
    db2 = PatternDatabase()
    if db2.load():
        print("Loaded successfully!")
        h2 = db2.get_heuristic(ENGLISH_START)
        print(f"Heuristic after load: {h2}")
