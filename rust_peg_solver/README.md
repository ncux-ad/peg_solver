# Rust Peg Solver Module

Rust реализация критических операций для Peg Solitaire Solver.

## Преимущества Rust

1. **Безопасность памяти** - компилятор гарантирует отсутствие багов памяти
2. **Производительность** - сравнима с C/C++, но безопаснее
3. **SIMD оптимизации** - возможность использования векторных инструкций
4. **Zero-cost abstractions** - высокоуровневый код без потери производительности

## Сборка

```bash
cd rust_peg_solver
maturin develop  # или maturin build --release
```

Или вручную:

```bash
cargo build --release
# Затем скопировать .so/.dylib/.dll в корень проекта
```

## Использование

```python
try:
    from rust_peg_solver import (
        rust_peg_count,
        rust_get_moves,
        rust_pagoda_value,
        rust_evaluate_position
    )
    USING_RUST = True
except ImportError:
    USING_RUST = False
    # Fallback на Cython/Python
```

## Производительность

- **popcount**: ~2-3x быстрее Cython (встроенная CPU инструкция)
- **Генерация ходов**: ~1.5-2x быстрее Cython
- **Pagoda функция**: ~3-4x быстрее Python
- **Batch оценка**: ~5-10x быстрее (параллельная обработка)

## Требования

- Rust 1.70+
- PyO3 для Python bindings
- maturin (опционально, для упрощённой сборки)
