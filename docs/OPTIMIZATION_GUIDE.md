# Руководство по оптимизации

## Обзор

Руководство по оптимизации производительности Peg Solitaire Solver.

## Выбор решателя

### Для маленьких позиций (<10 колышков)
- **SimpleDFSSolver** - быстрый базовый поиск
- **DFSMemoSolver** - с мемоизацией для ускорения

### Для средних позиций (10-20 колышков)
- **AStarSimpleSolver** - A* с эвристиками
- **BeamSimpleSolver** - быстрый неполный поиск
- **IDASimpleSolver** - экономия памяти

### Для больших позиций (>20 колышков)
- **BidirectionalSimpleSolver** - двунаправленный поиск
- **PatternAStarSimpleSolver** - с Pattern Database
- **ParallelSimpleSolver** - многопоточный поиск

### Для стандартной английской доски
- **LookupSolver** - мгновенное решение из базы
- **PatternAStarSolver** - оптимизированный A*

## Оптимизация эвристик

### Для английской доски
Используйте специализированные эвристики:
- `pagoda_value()` - Pagoda function
- `pattern_heuristic()` - Pattern Database

### Для произвольных досок
Используйте адаптированные эвристики:
- `heuristic_distance_to_center_arbitrary()`
- `heuristic_isolated_arbitrary()`
- `combined_heuristic_arbitrary()`

## Использование кэша

### Сохранение решений
```python
from peg_io.cache_enhanced import save_solution_enhanced

save_solution_enhanced(
    board_matrix, 
    moves, 
    solver='dfs_memo',
    time_elapsed=12.5
)
```

### Получение из кэша
```python
from peg_io.cache_enhanced import get_cached_solution_enhanced

solution = get_cached_solution_enhanced(board_matrix)
if solution:
    # Используем кэшированное решение
    pass
```

## Waypoints для сложных позиций

### Построение waypoints
```python
from peg_io.waypoints import WaypointDatabase

db = WaypointDatabase()
db.build_from_solution(start_board, solution, interval=5)
```

### Использование waypoints
```python
waypoint = db.find_waypoint(board)
if waypoint:
    # Используем путь через waypoint
    path = waypoint['from_start'] + waypoint['to_goal']
```

## Профилирование

### Базовое профилирование
```python
from tools.profiler import PerformanceProfiler

profiler = PerformanceProfiler()
with profiler.profile('my_function'):
    result = my_function()

print(profiler.get_stats('my_function'))
```

### Сравнение решателей
```python
from tools.profiler import PerformanceProfiler

profiler = PerformanceProfiler()
solvers = [SimpleDFSSolver(), DFSMemoSolver(), AStarSimpleSolver()]

profiler.print_comparison(board, solvers)
```

### Бенчмарк
```python
from tools.profiler import benchmark_solver

results = benchmark_solver(solver, board, iterations=10)
print(f"Среднее время: {results['avg_time']:.3f}s")
```

## Оптимизация памяти

### Использование IDA*
IDA* не хранит все состояния в памяти:
```python
solver = IDASimpleSolver(max_depth=50)
solution = solver.solve(board)
```

### Использование симметрий
Симметрии уменьшают пространство поиска:
```python
solver = DFSMemoSolver(use_symmetry=True)
```

## Параллелизация

### Многопоточный поиск
```python
solver = ParallelSimpleSolver(num_workers=4)
solution = solver.solve(board)
```

### Оптимальное количество потоков
- 2-4 потока для большинства случаев
- Больше потоков для очень больших позиций

## Избегание типичных проблем

### Не используйте SimpleDFS для больших позиций
SimpleDFS без оптимизаций очень медленный.

### Используйте мемоизацию
DFSMemoSolver значительно быстрее SimpleDFS.

### Кэшируйте решения
Используйте кэш для повторных запросов.

### Выбирайте правильный решатель
Разные решатели подходят для разных типов позиций.

## Измерение производительности

### Метрики
- `nodes_visited` - количество посещённых узлов
- `nodes_pruned` - количество отсечённых узлов
- `time_elapsed` - время выполнения
- `solution_length` - длина решения

### Анализ
```python
stats = solver.stats
print(f"Узлов посещено: {stats.nodes_visited}")
print(f"Узлов отсечено: {stats.nodes_pruned}")
print(f"Время: {stats.time_elapsed:.3f}s")
```

## Рекомендации

1. **Начните с LookupSolver** - проверьте кэш
2. **Используйте BeamSearch** для быстрой оценки
3. **Используйте DFSMemo** для полного решения
4. **Используйте A*** для оптимальных решений
5. **Кэшируйте результаты** для повторного использования
