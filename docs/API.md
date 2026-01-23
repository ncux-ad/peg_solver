# API Документация

## Обзор

Документация API для Peg Solitaire Solver. Описывает основные модули, классы и функции.

## Модуль `core.bitboard`

### Класс `BitBoard`

Битовое представление доски Peg Solitaire.

#### Методы

##### `__init__(pegs: int, valid_mask: int = None)`
Создаёт BitBoard.

**Параметры:**
- `pegs`: битовая маска фишек
- `valid_mask`: маска валидных клеток (если None, определяется автоматически)

**Пример:**
```python
board = BitBoard(pegs=0x1234, valid_mask=0xFFFF)
```

##### `english_start() -> BitBoard`
Создаёт стандартную английскую доску.

**Возвращает:** BitBoard с английской начальной позицией

##### `english_goal() -> BitBoard`
Создаёт целевую позицию (1 колышек в центре).

**Возвращает:** BitBoard с целевой позицией

##### `peg_count() -> int`
Возвращает количество колышков.

**Возвращает:** Количество колышков на доске

##### `has_peg(pos: int) -> bool`
Проверяет наличие колышка в позиции.

**Параметры:**
- `pos`: позиция (0-48)

**Возвращает:** True если есть колышек

##### `get_moves() -> List[Tuple[int, int, int]]`
Генерирует все допустимые ходы.

**Возвращает:** Список ходов (from, jumped, to)

##### `apply_move(from_pos: int, jumped: int, to_pos: int) -> BitBoard`
Применяет ход к доске.

**Параметры:**
- `from_pos`: позиция откуда
- `jumped`: позиция через которую
- `to_pos`: позиция куда

**Возвращает:** Новая BitBoard после хода

##### `is_solved() -> bool`
Проверяет, решена ли доска (1 колышек).

**Возвращает:** True если решена

##### `is_dead() -> bool`
Проверяет, является ли позиция тупиком.

**Возвращает:** True если нет возможных ходов

##### `canonical() -> BitBoard`
Возвращает каноническую форму доски (минимальная из 8 симметрий).

**Возвращает:** Каноническая BitBoard

### Утилиты

##### `get_valid_positions(board: BitBoard) -> Set[int]`
Возвращает множество валидных позиций из valid_mask.

##### `is_english_board(board: BitBoard) -> bool`
Проверяет, является ли доска классической английской доской.

##### `get_center_position(board: BitBoard) -> Optional[int]`
Возвращает центральную позицию для использования в эвристиках.

## Модуль `solvers`

### Базовый класс `BaseSolver`

Базовый класс для всех решателей.

#### Методы

##### `solve(board: BitBoard) -> Optional[List[Tuple[int, int, int]]]`
Решает головоломку.

**Параметры:**
- `board`: начальная позиция

**Возвращает:** Список ходов или None если решение не найдено

### Решатели Фазы 1-3

#### `SimpleDFSSolver`
Простой DFS без оптимизаций.

**Использование:**
```python
solver = SimpleDFSSolver(verbose=False)
solution = solver.solve(board)
```

#### `DFSMemoSolver`
DFS с мемоизацией неудачных состояний.

**Параметры:**
- `use_symmetry`: использовать симметрии (по умолчанию True)
- `sort_moves`: сортировать ходы (по умолчанию True)
- `verbose`: выводить отладочную информацию

#### `AStarSimpleSolver`
A* с простыми эвристиками.

**Параметры:**
- `use_symmetry`: использовать симметрии
- `verbose`: выводить отладочную информацию

#### `BeamSimpleSolver`
Beam Search для быстрой оценки.

**Параметры:**
- `beam_width`: ширина луча (по умолчанию 100)
- `use_symmetry`: использовать симметрии
- `verbose`: выводить отладочную информацию

#### `IDASimpleSolver`
IDA* для экономии памяти.

**Параметры:**
- `use_symmetry`: использовать симметрии
- `max_depth`: максимальная глубина (по умолчанию 50)
- `verbose`: выводить отладочную информацию

#### `BidirectionalSimpleSolver`
Двунаправленный поиск.

**Параметры:**
- `use_symmetry`: использовать симметрии
- `verbose`: выводить отладочную информацию

#### `PatternAStarSimpleSolver`
A* с Pattern Database эвристикой.

**Параметры:**
- `use_symmetry`: использовать симметрии
- `use_pattern_db`: использовать Pattern Database
- `verbose`: выводить отладочную информацию

#### `ParallelSimpleSolver`
Многопоточный DFS.

**Параметры:**
- `num_workers`: количество потоков (по умолчанию 4)
- `use_symmetry`: использовать симметрии
- `verbose`: выводить отладочную информацию

## Модуль `heuristics`

### Базовые эвристики

##### `heuristic_peg_count(board: BitBoard) -> int`
Базовая эвристика: количество колышков - 1.

##### `heuristic_distance_to_center(board: BitBoard, center: tuple = (3, 3)) -> float`
Суммарное манхэттенское расстояние колышков до центра.

### Эвристики для произвольных досок

##### `heuristic_distance_to_center_arbitrary(board: BitBoard) -> float`
Расстояние до центра для произвольных досок.

##### `heuristic_isolated_arbitrary(board: BitBoard) -> int`
Количество изолированных колышков для произвольных досок.

##### `heuristic_cluster_arbitrary(board: BitBoard) -> int`
Кластеризация колышков для произвольных досок.

##### `combined_heuristic_arbitrary(board: BitBoard, steps: int = 0, aggressive: bool = False) -> float`
Комбинированная эвристика для произвольных досок.

## Модуль `solutions.verify`

##### `verify_bitboard_solution(board: BitBoard, moves: List[Tuple[int, int, int]], require_center: bool = False) -> bool`
Проверяет корректность решения.

**Параметры:**
- `board`: начальная позиция
- `moves`: список ходов
- `require_center`: требовать финальный колышек в центре

**Возвращает:** True если решение корректно

##### `bitboard_to_matrix(board: BitBoard) -> List[List[str]]`
Строит матрицу 7x7 из BitBoard.

**Возвращает:** Матрица доски

## Модуль `peg_io.cache_enhanced`

### Улучшенное кэширование

##### `save_solution_enhanced(board: List[List[str]], moves: List[str], solver: str = "unknown", time_elapsed: float = 0.0) -> None`
Сохраняет решение в кэш с метаданными.

##### `get_cached_solution_enhanced(board: List[List[str]], prefer_shorter: bool = True) -> Optional[SolutionMetadata]`
Получает решение из кэша с метаданными.

##### `get_cache_stats() -> Dict[str, Any]`
Возвращает статистику кэша.

## Модуль `peg_io.waypoints`

### Класс `WaypointDatabase`

База данных опорных точек для ускорения поиска.

#### Методы

##### `add_waypoint(board: BitBoard, from_start: List[Tuple[int, int, int]], to_goal: List[Tuple[int, int, int]])`
Добавляет waypoint в базу.

##### `find_waypoint(board: BitBoard) -> Optional[Dict]`
Ищет waypoint для заданной позиции.

##### `build_from_solution(start_board: BitBoard, solution: List[Tuple[int, int, int]], interval: int = 5)`
Строит waypoints из известного решения.

## Модуль `tools.profiler`

### Класс `PerformanceProfiler`

Профилировщик производительности решателей.

#### Методы

##### `profile(name: str)`
Контекстный менеджер для профилирования.

##### `compare_solvers(board: BitBoard, solvers: List[BaseSolver]) -> Dict[str, Dict[str, Any]]`
Сравнивает производительность нескольких решателей.

##### `print_comparison(board: BitBoard, solvers: List[BaseSolver])`
Выводит сравнение решателей в консоль.

##### `benchmark_solver(solver: BaseSolver, board: BitBoard, iterations: int = 1) -> Dict[str, Any]`
Бенчмарк решателя на заданной позиции.

## Примеры использования

### Базовое использование

```python
from core.bitboard import BitBoard
from solvers.simple_dfs import SimpleDFSSolver

# Создаём доску
board = BitBoard.english_start()

# Создаём решатель
solver = SimpleDFSSolver(verbose=False)

# Решаем
solution = solver.solve(board)

if solution:
    print(f"Решение найдено: {len(solution)} ходов")
else:
    print("Решение не найдено")
```

### Использование кэша

```python
from peg_io.cache_enhanced import save_solution_enhanced, get_cached_solution_enhanced
from solutions.verify import bitboard_to_matrix

# Сохраняем решение
matrix = bitboard_to_matrix(board)
save_solution_enhanced(matrix, moves, solver='dfs_memo', time_elapsed=12.5)

# Получаем из кэша
cached = get_cached_solution_enhanced(matrix)
if cached:
    print(f"Решение найдено в кэше: {cached.move_count} ходов")
```

### Профилирование

```python
from tools.profiler import PerformanceProfiler
from solvers import SimpleDFSSolver, DFSMemoSolver

profiler = PerformanceProfiler()
solvers = [SimpleDFSSolver(), DFSMemoSolver()]

profiler.print_comparison(board, solvers)
```
