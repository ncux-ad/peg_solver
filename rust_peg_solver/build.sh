#!/bin/bash
# Скрипт сборки Rust модуля для Python

set -e

echo "🔨 Сборка Rust модуля для Peg Solitaire Solver..."

# Проверка наличия Rust
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust не установлен. Установите: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

# Проверка наличия maturin (рекомендуется)
if command -v maturin &> /dev/null; then
    echo "✅ Использование maturin для сборки..."
    maturin develop --release
else
    echo "⚠️  maturin не найден. Используется прямой сборка через cargo..."
    echo "   Для лучшего опыта установите: pip install maturin"
    
    # Прямая сборка
    cd "$(dirname "$0")"
    cargo build --release
    
    # Поиск скомпилированной библиотеки
    if [ -f "target/release/librust_peg_solver.so" ]; then
        cp target/release/librust_peg_solver.so ../rust_peg_solver.so
        echo "✅ Скомпилировано: rust_peg_solver.so"
    elif [ -f "target/release/librust_peg_solver.dylib" ]; then
        cp target/release/librust_peg_solver.dylib ../rust_peg_solver.dylib
        echo "✅ Скомпилировано: rust_peg_solver.dylib"
    elif [ -f "target/release/rust_peg_solver.dll" ]; then
        cp target/release/rust_peg_solver.dll ../rust_peg_solver.dll
        echo "✅ Скомпилировано: rust_peg_solver.dll"
    else
        echo "❌ Не найдена скомпилированная библиотека"
        exit 1
    fi
fi

echo "✅ Сборка завершена!"
echo ""
echo "Проверка:"
echo "  python -c 'from core.rust_fast import USING_RUST; print(f\"Rust: {USING_RUST}\")'"
