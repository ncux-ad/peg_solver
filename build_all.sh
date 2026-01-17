#!/bin/bash
# 🚀 Скрипт для установки и сборки всех оптимизаций
# Rust, Numba, Cython для Peg Solitaire Solver

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Символы
CHECK="✅"
CROSS="❌"
ARROW="➜"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   🚀 Установка и сборка оптимизаций Peg Solitaire    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}${CROSS} Python 3 не найден!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}${CHECK} Python: ${BLUE}${PYTHON_VERSION}${NC}"

# Проверка pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo -e "${RED}${CROSS} pip не найден!${NC}"
    exit 1
fi

PIP_CMD=$(command -v pip3 || command -v pip)
echo -e "${GREEN}${CHECK} pip найден${NC}"

# Проверка наличия Python.h (для компиляции Cython)
PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))" 2>/dev/null || echo "")
if [ -z "$PYTHON_INCLUDE" ] || [ ! -f "$PYTHON_INCLUDE/Python.h" ]; then
    echo -e "${YELLOW}   ⚠️  Python.h не найден - нужны заголовочные файлы Python${NC}"
    echo -e "${CYAN}   💡 Установите python3-dev (Ubuntu/Debian) или python3-devel (Fedora/RHEL)${NC}"
    echo ""
    read -p "Попытаться установить автоматически? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v apt-get &> /dev/null; then
            echo -e "${CYAN}   📦 Установка python3-dev через apt-get...${NC}"
            sudo apt-get update && sudo apt-get install -y python3-dev python3-distutils
        elif command -v yum &> /dev/null; then
            echo -e "${CYAN}   📦 Установка python3-devel через yum...${NC}"
            sudo yum install -y python3-devel
        elif command -v dnf &> /dev/null; then
            echo -e "${CYAN}   📦 Установка python3-devel через dnf...${NC}"
            sudo dnf install -y python3-devel
        elif command -v pacman &> /dev/null; then
            echo -e "${CYAN}   📦 Установка python через pacman...${NC}"
            sudo pacman -S --noconfirm python
        else
            echo -e "${RED}   ${CROSS} Не удалось определить пакетный менеджер${NC}"
            echo -e "${YELLOW}   Установите вручную:${NC}"
            echo -e "${YELLOW}     Ubuntu/Debian: sudo apt-get install python3-dev${NC}"
            echo -e "${YELLOW}     Fedora/RHEL: sudo dnf install python3-devel${NC}"
            echo -e "${YELLOW}     Arch: sudo pacman -S python${NC}"
        fi
    else
        echo -e "${YELLOW}   ⚠️  Cython расширения не будут скомпилированы без Python.h${NC}"
    fi
fi

# Проверка компилятора C
if ! command -v gcc &> /dev/null && ! command -v clang &> /dev/null; then
    echo -e "${YELLOW}   ⚠️  Компилятор C не найден - нужен для сборки Cython${NC}"
    echo -e "${CYAN}   💡 Установите build-essential (Ubuntu/Debian) или gcc (другие дистрибутивы)${NC}"
    read -p "Попытаться установить автоматически? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v apt-get &> /dev/null; then
            echo -e "${CYAN}   📦 Установка build-essential через apt-get...${NC}"
            sudo apt-get update && sudo apt-get install -y build-essential
        elif command -v yum &> /dev/null; then
            echo -e "${CYAN}   📦 Установка gcc через yum...${NC}"
            sudo yum install -y gcc gcc-c++ make
        elif command -v dnf &> /dev/null; then
            echo -e "${CYAN}   📦 Установка gcc через dnf...${NC}"
            sudo dnf install -y gcc gcc-c++ make
        elif command -v pacman &> /dev/null; then
            echo -e "${CYAN}   📦 Установка base-devel через pacman...${NC}"
            sudo pacman -S --noconfirm base-devel
        fi
    fi
fi

echo ""

# Функция для проверки установки пакета
check_package() {
    local package=$1
    if python3 -c "import $package" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# ============================================
# 1. Установка базовых зависимостей
# ============================================
echo -e "${BLUE}${ARROW} Шаг 1/4: Установка базовых зависимостей...${NC}"

if [ -f "requirements.txt" ]; then
    echo -e "${CYAN}   📦 Установка из requirements.txt...${NC}"
    $PIP_CMD install --upgrade pip setuptools wheel
    $PIP_CMD install -r requirements.txt
    echo -e "${GREEN}   ${CHECK} Базовые зависимости установлены${NC}"
else
    echo -e "${YELLOW}   ⚠️  requirements.txt не найден, пропускаем${NC}"
fi
echo ""

# ============================================
# 2. Установка и сборка Cython
# ============================================
echo -e "${BLUE}${ARROW} Шаг 2/4: Установка и сборка Cython расширений...${NC}"

if check_package Cython; then
    echo -e "${GREEN}   ${CHECK} Cython уже установлен${NC}"
else
    echo -e "${CYAN}   📦 Установка Cython...${NC}"
    $PIP_CMD install Cython setuptools wheel
    echo -e "${GREEN}   ${CHECK} Cython установлен${NC}"
fi

# Проверяем, нужно ли собирать Cython расширения
if [ -f "core/fast_bitboard.pyx" ]; then
    # Проверяем наличие скомпилированных файлов
    CYTHON_BUILT=false
    if ls core/fast_bitboard*.so 2>/dev/null | grep -q .; then
        CYTHON_BUILT=true
    elif [ -f "core/fast_bitboard.c" ] && [ -f "core/fast_bitboard.o" ]; then
        CYTHON_BUILT=true
    fi
    
    if [ "$CYTHON_BUILT" = true ]; then
        echo -e "${GREEN}   ${CHECK} Cython расширения уже скомпилированы${NC}"
    else
        # Проверяем наличие Python.h перед компиляцией
        PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))" 2>/dev/null || echo "")
        if [ -z "$PYTHON_INCLUDE" ] || [ ! -f "$PYTHON_INCLUDE/Python.h" ]; then
            echo -e "${RED}   ${CROSS} Python.h не найден - невозможно скомпилировать Cython${NC}"
            echo -e "${YELLOW}   Установите python3-dev:${NC}"
            echo -e "${YELLOW}     Ubuntu/Debian: sudo apt-get install python3-dev${NC}"
            echo -e "${YELLOW}     Fedora/RHEL: sudo dnf install python3-devel${NC}"
        elif ! command -v gcc &> /dev/null && ! command -v clang &> /dev/null; then
            echo -e "${RED}   ${CROSS} Компилятор C не найден - невозможно скомпилировать Cython${NC}"
            echo -e "${YELLOW}   Установите build-essential:${NC}"
            echo -e "${YELLOW}     Ubuntu/Debian: sudo apt-get install build-essential${NC}"
        else
            echo -e "${CYAN}   ⚙️  Компиляция Cython расширений...${NC}"
            if [ -f "setup.py" ]; then
                if python3 setup.py build_ext --inplace 2>&1 | tee /tmp/cython_build.log; then
                    echo -e "${GREEN}   ${CHECK} Cython расширения скомпилированы${NC}"
                else
                    echo -e "${RED}   ${CROSS} Ошибка компиляции Cython${NC}"
                    echo -e "${YELLOW}   Проверьте лог: /tmp/cython_build.log${NC}"
                    if grep -q "Python.h" /tmp/cython_build.log 2>/dev/null; then
                        echo -e "${YELLOW}   💡 Установите python3-dev: sudo apt-get install python3-dev${NC}"
                    fi
                fi
            else
                echo -e "${YELLOW}   ⚠️  setup.py не найден, пропускаем сборку${NC}"
            fi
        fi
    fi
else
    echo -e "${YELLOW}   ⚠️  core/fast_bitboard.pyx не найден, пропускаем${NC}"
fi
echo ""

# ============================================
# 3. Установка Numba
# ============================================
echo -e "${BLUE}${ARROW} Шаг 3/4: Установка Numba JIT...${NC}"

if check_package numba; then
    NUMBA_VERSION=$(python3 -c "import numba; print(numba.__version__)" 2>/dev/null || echo "установлен")
    echo -e "${GREEN}   ${CHECK} Numba уже установлен (${NUMBA_VERSION})${NC}"
else
    echo -e "${CYAN}   📦 Установка Numba...${NC}"
    echo -e "${YELLOW}   ⚠️  Это может занять несколько минут...${NC}"
    $PIP_CMD install numba
    echo -e "${GREEN}   ${CHECK} Numba установлен${NC}"
fi
echo ""

# ============================================
# 4. Установка и сборка Rust (опционально)
# ============================================
echo -e "${BLUE}${ARROW} Шаг 4/4: Установка и сборка Rust модуля (опционально)...${NC}"

read -p "Установить Rust и собрать Rust модуль? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Проверяем, установлен ли Rust
    if command -v rustc &> /dev/null && command -v cargo &> /dev/null; then
        echo -e "${GREEN}   ${CHECK} Rust уже установлен${NC}"
        echo -e "${INFO}   Версия: ${BLUE}$(rustc --version)${NC}"
    else
        echo -e "${CYAN}   📦 Установка Rust...${NC}"
        if [ -f "install_rust.sh" ]; then
            bash install_rust.sh
        else
            echo -e "${YELLOW}   ⚠️  install_rust.sh не найден${NC}"
            echo -e "${CYAN}   💡 Установите Rust вручную: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh${NC}"
            exit 1
        fi
        
        # Загружаем переменные окружения Rust
        if [ -f "$HOME/.cargo/env" ]; then
            source "$HOME/.cargo/env"
        fi
    fi
    
    # Проверяем maturin
    if command -v maturin &> /dev/null; then
        echo -e "${GREEN}   ${CHECK} maturin уже установлен${NC}"
    else
        echo -e "${CYAN}   📦 Установка maturin...${NC}"
        $PIP_CMD install maturin
        echo -e "${GREEN}   ${CHECK} maturin установлен${NC}"
    fi
    
    # Собираем Rust модуль
    if [ -d "rust_peg_solver" ]; then
        echo -e "${CYAN}   ⚙️  Сборка Rust модуля...${NC}"
        cd rust_peg_solver
        
        if [ -f "build.sh" ]; then
            bash build.sh
        else
            # Альтернативный способ сборки
            if command -v maturin &> /dev/null; then
                maturin develop --release
            else
                echo -e "${YELLOW}   ⚠️  maturin не найден, используем cargo напрямую${NC}"
                cargo build --release
            fi
        fi
        
        cd ..
        echo -e "${GREEN}   ${CHECK} Rust модуль собран${NC}"
    else
        echo -e "${YELLOW}   ⚠️  rust_peg_solver не найден, пропускаем${NC}"
    fi
else
    echo -e "${YELLOW}   ⏭️  Пропущено (Rust опционален)${NC}"
fi
echo ""

# ============================================
# Проверка результатов
# ============================================
echo -e "${BLUE}${ARROW} Проверка установленных оптимизаций...${NC}"
echo ""

# Проверка Cython
if python3 -c "from core.fast import USING_CYTHON; print('Cython:', USING_CYTHON)" 2>/dev/null; then
    CYTHON_STATUS=$(python3 -c "from core.fast import USING_CYTHON; print('✅' if USING_CYTHON else '❌')" 2>/dev/null || echo "?")
    echo -e "${GREEN}   ${CYTHON_STATUS} Cython: $(python3 -c "from core.fast import USING_CYTHON; print('активен' if USING_CYTHON else 'не активен')" 2>/dev/null || echo "неизвестно")${NC}"
else
    echo -e "${YELLOW}   ⚠️  Cython: не удалось проверить${NC}"
fi

# Проверка Numba
if python3 -c "from heuristics.fast_pagoda import NUMBA_AVAILABLE; print('Numba:', NUMBA_AVAILABLE)" 2>/dev/null; then
    NUMBA_STATUS=$(python3 -c "from heuristics.fast_pagoda import NUMBA_AVAILABLE; print('✅' if NUMBA_AVAILABLE else '❌')" 2>/dev/null || echo "?")
    echo -e "${GREEN}   ${NUMBA_STATUS} Numba: $(python3 -c "from heuristics.fast_pagoda import NUMBA_AVAILABLE; print('активен' if NUMBA_AVAILABLE else 'не активен')" 2>/dev/null || echo "неизвестно")${NC}"
else
    echo -e "${YELLOW}   ⚠️  Numba: не удалось проверить${NC}"
fi

# Проверка Rust
if python3 -c "from core.rust_fast import USING_RUST; print('Rust:', USING_RUST)" 2>/dev/null; then
    RUST_STATUS=$(python3 -c "from core.rust_fast import USING_RUST; print('✅' if USING_RUST else '❌')" 2>/dev/null || echo "?")
    echo -e "${GREEN}   ${RUST_STATUS} Rust: $(python3 -c "from core.rust_fast import USING_RUST; print('активен' if USING_RUST else 'не активен')" 2>/dev/null || echo "неизвестно")${NC}"
else
    echo -e "${YELLOW}   ⚠️  Rust: не установлен или не собран${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         ✅ Установка и сборка завершены!             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${CYAN}${ROCKET} Готово к использованию!${NC}"
echo ""
echo -e "${INFO} Для проверки запустите:${NC}"
echo -e "${YELLOW}   python3 -c \"from core.fast import get_implementation_info; print(get_implementation_info())\"${NC}"
echo ""
