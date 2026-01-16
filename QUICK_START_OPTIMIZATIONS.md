# 🚀 Быстрый старт с оптимизациями

## 📦 Установка

### Базовые зависимости (всегда нужны)

```bash
pip install -r requirements.txt
```

Это установит:
- ✅ **Numba** - для JIT компиляции эвристик (автоматически)
- ✅ **Cython** - для компиляции текущих расширений

### Cython расширения (рекомендуется)

```bash
python setup.py build_ext --inplace
```

### Rust модуль (опционально, для максимальной производительности)

```bash
# Установите Rust (если ещё не установлен)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Установите maturin (рекомендуется)
pip install maturin

# Скомпилируйте Rust модуль
cd rust_peg_solver
./build.sh
# или
maturin develop --release
```

## ✅ Проверка установки

```bash
python -c "
from core.rust_fast import USING_RUST, get_implementation_info
from core.fast import USING_CYTHON
from heuristics.fast_pagoda import NUMBA_AVAILABLE

print(f'✅ Rust: {USING_RUST}')
print(f'✅ Cython: {USING_CYTHON}')
print(f'✅ Numba: {NUMBA_AVAILABLE}')
print(f'📊 Текущая реализация: {get_implementation_info()}')
"
```

Ожидаемый вывод (если всё установлено):
```
✅ Rust: True
✅ Cython: True
✅ Numba: True
📊 Текущая реализация: Rust (compiled, fastest - 2-10x faster than Cython)
```

Если Rust не установлен:
```
✅ Rust: False
✅ Cython: True
✅ Numba: True
📊 Текущая реализация: Cython (compiled, 26x faster than Python)
```

## 🎯 Использование оптимизированных функций

### Автоматический выбор (рекомендуется)

```python
from core.rust_fast import (
    rust_get_moves,
    rust_evaluate_position,
    rust_pagoda_value
)
from heuristics.fast_pagoda import pagoda_value_fast

board = BitBoard.english_start()

# Автоматически использует Rust → Cython → Python (fallback)
moves = rust_get_moves(board.pegs)
score = rust_evaluate_position(board.pegs, len(moves))

# Автоматически использует Numba JIT → Python (fallback)
pagoda_val = pagoda_value_fast(board.pegs)
```

### Использование в решателях

Все решатели автоматически используют оптимизированные функции через `core.rust_fast`:

```python
from solvers import BeamSolver, GovernorSolver

solver = BeamSolver(beam_width=500)
solution = solver.solve(board)  # Автоматически использует оптимизации
```

## 📊 Ожидаемое ускорение

| Реализация | Генерация ходов | Pagoda функция | Оценка позиции |
|------------|----------------|----------------|----------------|
| **Rust** | 3.5M ops/s | 8M ops/s | 2M ops/s |
| **Cython** | 1M ops/s | - | - |
| **Numba JIT** | - | 4M ops/s | 1M ops/s |
| **Python** | 50K ops/s | 1M ops/s | 200K ops/s |

## 🐛 Устранение проблем

### Rust модуль не компилируется

**Проблема:** `ImportError: No module named 'rust_peg_solver'`

**Решение:**
1. Убедитесь, что Rust установлен: `rustc --version`
2. Попробуйте пересобрать: `cd rust_peg_solver && maturin develop --release`
3. Или используйте Cython/Python (автоматический fallback)

### Numba не работает

**Проблема:** Предупреждения о Numba

**Решение:**
1. Убедитесь, что numba установлена: `pip install numba`
2. Numba имеет fallback на Python (работает, но медленнее)

### Cython не компилируется

**Проблема:** `ImportError: No module named 'core.fast_bitboard'`

**Решение:**
1. Установите Cython: `pip install Cython`
2. Скомпилируйте: `python setup.py build_ext --inplace`
3. Или используйте Python версию (медленнее, но работает)

## 💡 Рекомендации

1. **Для начала**: Установите базовые зависимости + Cython (это даст 26x ускорение)
2. **Для максимума**: Добавьте Rust модуль (ещё 2-10x ускорение)
3. **Всегда работает**: Fallback на Python, если ничего не скомпилировано

## 📚 Дополнительная информация

- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** - Полное руководство по оптимизациям
- **[OPTIMIZATION_SUMMARY_RU.md](OPTIMIZATION_SUMMARY_RU.md)** - Сводка по оптимизациям
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** - Полный бриф проекта
