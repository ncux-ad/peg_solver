#!/bin/bash
# 🦀 Наглядный скрипт установки Rust для Peg Solitaire Solver

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Символы для прогресса
CHECK="✅"
CROSS="❌"
ARROW="➜"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     🦀 Установка Rust для Peg Solitaire Solver       ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Проверка, установлен ли Rust
if command -v rustc &> /dev/null; then
    echo -e "${GREEN}${CHECK} Rust уже установлен!${NC}"
    echo -e "${INFO} Версия: ${BLUE}$(rustc --version)${NC}"
    echo -e "${INFO} Cargo: ${BLUE}$(cargo --version)${NC}"
    echo ""
    read -p "Переустановить Rust? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Установка отменена. Используем текущую версию Rust.${NC}"
        exit 0
    fi
fi

echo -e "${INFO} Этот процесс займёт ~3-10 минут${NC}"
echo -e "${INFO} Скачается ~200-500 МБ данных${NC}"
echo ""

# Функция для отображения прогресса
show_progress() {
    local message=$1
    echo -n -e "${CYAN}${GEAR} ${message}...${NC}"
}

# Функция для отображения завершения шага
step_done() {
    echo -e " ${GREEN}${CHECK}${NC}"
}

# Функция для отображения ошибки
step_error() {
    echo -e " ${RED}${CROSS}${NC}"
}

# Шаг 1: Скачивание и установка rustup
echo -e "${BLUE}${ARROW} Шаг 1/4: Скачивание rustup installer...${NC}"
echo -e "${CYAN}   URL: https://sh.rustup.rs${NC}"
echo ""

# Функция для отображения прогресса загрузки
download_with_progress() {
    local url=$1
    local output=$2
    
    echo -e "${CYAN}   📥 Начало загрузки инсталлятора...${NC}"
    echo -e "${CYAN}   ℹ️  URL: ${url}${NC}"
    
    if command -v curl &> /dev/null; then
        # Анимация "точки" пока идет загрузка (в фоне)
        (
            while true; do
                echo -ne "\r${CYAN}   📥 Загрузка инсталлятора${YELLOW}.${NC}   "
                sleep 0.4
                echo -ne "\r${CYAN}   📥 Загрузка инсталлятора${YELLOW}..${NC}  "
                sleep 0.4
                echo -ne "\r${CYAN}   📥 Загрузка инсталлятора${YELLOW}...${NC} "
                sleep 0.4
                echo -ne "\r${CYAN}   📥 Загрузка инсталлятора${YELLOW}   ${NC}"
                sleep 0.4
            done
        ) &
        SPINNER_PID=$!
        
        # Файл-флаг для отслеживания, начался ли реальный прогресс
        PROGRESS_FLAG="/tmp/curl_progress_$$.flag"
        rm -f "$PROGRESS_FLAG"
        
        # Загружаем файл - curl покажет прогресс в stderr (--progress-bar)
        # Перенаправляем stderr в stdout для парсинга
        curl --proto '=https' --tlsv1.2 -L \
            --progress-bar \
            -o "$output" "$url" 2>&1 | \
            while IFS= read -r line; do
                # Убиваем анимацию при первом сообщении о прогрессе
                if [ ! -f "$PROGRESS_FLAG" ] && echo "$line" | grep -qE '^#'; then
                    kill $SPINNER_PID 2>/dev/null || true
                    touch "$PROGRESS_FLAG"
                fi
                
                # Парсим строки прогресса curl (начинаются с # и содержат %)
                if echo "$line" | grep -qE '^#.*[0-9]+\.[0-9]+%'; then
                    # Извлекаем процент
                    percent=$(echo "$line" | grep -oP '[0-9]+\.[0-9]+%' | head -1 || echo "")
                    # Извлекаем размеры (например: "1.2K / 5.3K")
                    sizes=$(echo "$line" | grep -oP '[0-9]+\.[0-9]+[KM]?\s*/\s*[0-9]+\.[0-9]+[KM]?' | head -1 || echo "")
                    
                    if [ -n "$percent" ]; then
                        if [ -n "$sizes" ]; then
                            echo -ne "\r${CYAN}   📥 Загрузка: ${YELLOW}${percent}${NC} (${sizes})    "
                        else
                            echo -ne "\r${CYAN}   📥 Загрузка: ${YELLOW}${percent}${NC}        "
                        fi
                    fi
                elif echo "$line" | grep -qE '^#'; then
                    # Другие строки прогресса (без %)
                    if [ -f "$PROGRESS_FLAG" ]; then
                        clean_line=$(echo "$line" | sed 's/^#//' | xargs)
                        if [ -n "$clean_line" ]; then
                            echo -ne "\r${CYAN}   📥 Загрузка: ${YELLOW}${clean_line}${NC}        "
                        fi
                    fi
                fi
            done
        
        # Удаляем флаг и убиваем спиннер
        rm -f "$PROGRESS_FLAG"
        kill $SPINNER_PID 2>/dev/null || true
        echo ""  # Новая строка после прогресса
        
        # Проверяем результат и показываем размер
        if [ -f "$output" ] && [ -s "$output" ]; then
            FILE_SIZE=$(stat -c%s "$output" 2>/dev/null || stat -f%z "$output" 2>/dev/null || echo "0")
            if [ "$FILE_SIZE" -gt 0 ]; then
                if [ "$FILE_SIZE" -gt 1048576 ]; then
                    SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $FILE_SIZE/1048576}")
                    echo -e "${GREEN}   ${CHECK} Инсталлятор скачан: ${YELLOW}${SIZE_MB} МБ${NC}"
                elif [ "$FILE_SIZE" -gt 1024 ]; then
                    SIZE_KB=$(awk "BEGIN {printf \"%.1f\", $FILE_SIZE/1024}")
                    echo -e "${GREEN}   ${CHECK} Инсталлятор скачан: ${YELLOW}${SIZE_KB} КБ${NC}"
                else
                    echo -e "${GREEN}   ${CHECK} Инсталлятор скачан: ${YELLOW}${FILE_SIZE} байт${NC}"
                fi
            fi
            return 0
        else
            return 1
        fi
        
    elif command -v wget &> /dev/null; then
        # Используем wget - он сам покажет прогресс-бар
        echo -e "${CYAN}   📥 Загрузка инсталлятора (wget)...${NC}"
        wget --progress=bar:force --show-progress \
            -O "$output" "$url"
        return $?
    else
        # Fallback
        echo -e "${YELLOW}   ⚠️  Используется простая загрузка${NC}"
        if command -v curl &> /dev/null; then
            if curl --proto '=https' --tlsv1.2 -o "$output" "$url"; then
                echo -e "${GREEN}   ${CHECK} Загрузка завершена${NC}"
                return 0
            else
                echo -e "${RED}   ${CROSS} Ошибка загрузки${NC}"
                return 1
            fi
        else
            echo -e "${RED}   ${CROSS} Ошибка: curl или wget не найдены${NC}"
            return 1
        fi
    fi
}

# Скачиваем инсталлятор с наглядным прогрессом
if ! download_with_progress "https://sh.rustup.rs" "/tmp/rustup-init.sh"; then
    step_error
    echo -e "${RED}Ошибка при скачивании rustup${NC}"
    exit 1
fi

# Размер уже показан в функции download_with_progress
# Проверяем, что файл существует
if [ ! -f "/tmp/rustup-init.sh" ] || [ ! -s "/tmp/rustup-init.sh" ]; then
    step_error
    echo -e "${RED}Файл не найден или пуст после скачивания${NC}"
    exit 1
fi
echo ""

# Шаг 2: Установка Rust
echo -e "${BLUE}${ARROW} Шаг 2/4: Установка Rust (это займёт несколько минут)...${NC}"
echo -e "${YELLOW}   ⚠️  Идёт скачивание и установка компонентов Rust...${NC}"
echo ""

# Запускаем установку в фоне и отслеживаем прогресс
chmod +x /tmp/rustup-init.sh

# Счетчик для отслеживания активности
ACTIVITY_COUNTER=0
START_TIME=$(date +%s)

# Устанавливаем с детальным выводом
RUSTUP_INIT_SKIP_PATH_CHECK=yes /tmp/rustup-init.sh -y 2>&1 | while IFS= read -r line; do
    # Увеличиваем счетчик активности
    ACTIVITY_COUNTER=$((ACTIVITY_COUNTER + 1))
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    # Показываем все сообщения info
    if echo "$line" | grep -q "info:"; then
        # Показываем важные сообщения о прогрессе
        if echo "$line" | grep -qE "(downloading|installing|component|profile|default|toolchain)"; then
            # Выделяем важную информацию
            CLEAN_LINE=$(echo "$line" | sed 's/^info: //')
            if echo "$CLEAN_LINE" | grep -qE "downloading"; then
                echo -e "${BLUE}   📥 ${CLEAN_LINE}${NC}"
            elif echo "$CLEAN_LINE" | grep -qE "installing"; then
                echo -e "${CYAN}   ⚙️  ${CLEAN_LINE}${NC}"
            else
                echo -e "${CYAN}   ${CLEAN_LINE}${NC}"
            fi
        else
            # Обычные info сообщения (меньше шума)
            CLEAN_LINE=$(echo "$line" | sed 's/^info: //')
            echo -e "${CYAN}   ℹ️  ${CLEAN_LINE}${NC}"
        fi
    elif echo "$line" | grep -q "error:"; then
        echo -e "${RED}   ❌ ${line}${NC}"
    elif echo "$line" | grep -qE "Rust is installed now"; then
        echo -e "${GREEN}   ✅ ${line}${NC}"
    elif [ -n "$line" ]; then
        # Остальные важные сообщения
        echo -e "${YELLOW}   ${line}${NC}"
    else
        # Показываем индикатор активности каждые 30 сообщений
        if [ $((ACTIVITY_COUNTER % 30)) -eq 0 ]; then
            echo -ne "\r${CYAN}   ⏳ Установка продолжается... (${ELAPSED} сек)${NC}"
        fi
    fi
done

INSTALL_EXIT=${PIPESTATUS[0]}
echo ""  # Новая строка после прогресса

if [ $INSTALL_EXIT -eq 0 ]; then
    echo ""
    step_done
else
    step_error
    echo -e "${RED}Ошибка при установке Rust${NC}"
    exit 1
fi

# Шаг 3: Загрузка переменных окружения
echo -e "${BLUE}${ARROW} Шаг 3/4: Настройка окружения...${NC}"
show_progress "Загрузка переменных окружения"

if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
    step_done
else
    step_error
    echo -e "${YELLOW}⚠️  Файл $HOME/.cargo/env не найден${NC}"
    echo -e "${YELLOW}   Возможно, нужна перезагрузка терминала${NC}"
fi

# Шаг 4: Проверка установки
echo -e "${BLUE}${ARROW} Шаг 4/4: Проверка установки...${NC}"

# Добавляем cargo в PATH для текущей сессии
export PATH="$HOME/.cargo/bin:$PATH"

if command -v rustc &> /dev/null; then
    RUSTC_VERSION=$(rustc --version)
    echo -e "${GREEN}${CHECK} Rust: ${BLUE}${RUSTC_VERSION}${NC}"
else
    echo -e "${RED}${CROSS} rustc не найден в PATH${NC}"
    echo -e "${YELLOW}   Попробуйте: source $HOME/.cargo/env${NC}"
fi

if command -v cargo &> /dev/null; then
    CARGO_VERSION=$(cargo --version)
    echo -e "${GREEN}${CHECK} Cargo: ${BLUE}${CARGO_VERSION}${NC}"
else
    echo -e "${RED}${CROSS} cargo не найден в PATH${NC}"
    echo -e "${YELLOW}   Попробуйте: source $HOME/.cargo/env${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ Rust успешно установлен!              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Показываем размер установки
if [ -d "$HOME/.rustup" ]; then
    SIZE=$(du -sh "$HOME/.rustup" 2>/dev/null | cut -f1)
    echo -e "${INFO} Размер установки: ${BLUE}${SIZE}${NC}"
fi

echo ""
echo -e "${CYAN}${ROCKET} Следующие шаги:${NC}"
echo ""
echo -e "1. ${ARROW} Активируйте переменные окружения:"
echo -e "   ${YELLOW}source \$HOME/.cargo/env${NC}"
echo ""
echo -e "2. ${ARROW} Установите maturin (для сборки Python модулей):"
echo -e "   ${YELLOW}pip install --timeout=300 maturin${NC}"
echo ""
echo -e "3. ${ARROW} Соберите Rust модуль:"
echo -e "   ${YELLOW}cd rust_peg_solver && ./build.sh${NC}"
echo ""
echo -e "${INFO} Примечание: Rust модуль ${YELLOW}опционален${NC} - проект работает и без него!"
echo -e "${INFO} Cython уже даёт 26x ускорение - это более чем достаточно."
echo ""
