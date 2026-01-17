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

# Функция для проверки целостности скачанного файла
check_file_integrity() {
    local file=$1
    
    # Проверяем, что файл существует и не пуст
    if [ ! -f "$file" ] || [ ! -s "$file" ]; then
        return 1
    fi
    
    # Проверяем, что файл заканчивается корректно (не обрезан)
    # Для bash скрипта последняя строка не должна быть обрезана
    if [ -n "$(tail -c 1 "$file" | od -An -tx1 | grep -v ' 0a')" ]; then
        # Файл не заканчивается переводом строки - может быть нормально
        :
    fi
    
    # Проверяем синтаксис скрипта
    if head -1 "$file" | grep -q "^#!/bin/sh"; then
        # Это sh скрипт - проверяем синтаксис
        if ! sh -n "$file" 2>/dev/null; then
            return 1
        fi
    fi
    
    # Проверяем минимальный размер (rustup installer обычно > 20KB)
    local size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo "0")
    if [ "$size" -lt 10000 ]; then
        echo -e "${YELLOW}   ⚠️  Предупреждение: файл кажется слишком маленьким (${size} байт)${NC}"
    fi
    
    return 0
}

# Функция для отображения прогресса загрузки
download_with_progress() {
    local url=$1
    local output=$2
    local max_retries=3
    local retry=0
    
    echo -e "${CYAN}   📥 Начало загрузки инсталлятора...${NC}"
    echo -e "${CYAN}   ℹ️  URL: ${url}${NC}"
    
    while [ $retry -lt $max_retries ]; do
        if [ $retry -gt 0 ]; then
            echo -e "${YELLOW}   🔄 Повторная попытка загрузки (${retry}/${max_retries})...${NC}"
            sleep 2
        fi
        
        # Удаляем старый файл при повторной попытке
        if [ $retry -gt 0 ]; then
            rm -f "$output"
        fi
        
        if command -v curl &> /dev/null; then
            # Используем curl БЕЗ перенаправления в pipe - это более надёжно
            # Показываем простой индикатор
            echo -ne "${CYAN}   📥 Загрузка инсталлятора...${NC}"
            
            # Загружаем файл с прогресс-баром (выводится в stderr, не перехватываем)
            # Используем -f для fail на ошибки HTTP, -S для показа ошибок
            if curl --proto '=https' --tlsv1.2 -L \
                --fail \
                --show-error \
                --connect-timeout 30 \
                --max-time 300 \
                --progress-bar \
                -o "$output" "$url"; then
                
                echo ""  # Новая строка после прогресс-бара
                
                # Проверяем целостность файла
                if check_file_integrity "$output"; then
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
                    echo -e "${RED}   ${CROSS} Файл повреждён или обрезан${NC}"
                    retry=$((retry + 1))
                    continue
                fi
            else
                echo -e "\r${RED}   ${CROSS} Ошибка загрузки${NC}"
                retry=$((retry + 1))
                continue
            fi
        
        elif command -v wget &> /dev/null; then
            # Используем wget - он сам покажет прогресс-бар
            echo -e "${CYAN}   📥 Загрузка инсталлятора (wget)...${NC}"
            if wget --progress=bar:force --show-progress \
                --timeout=30 \
                -O "$output" "$url"; then
                
                # Проверяем целостность
                if check_file_integrity "$output"; then
                    FILE_SIZE=$(stat -c%s "$output" 2>/dev/null || stat -f%z "$output" 2>/dev/null || echo "0")
                    if [ "$FILE_SIZE" -gt 1024 ]; then
                        SIZE_KB=$(awk "BEGIN {printf \"%.1f\", $FILE_SIZE/1024}")
                        echo -e "${GREEN}   ${CHECK} Инсталлятор скачан: ${YELLOW}${SIZE_KB} КБ${NC}"
                    fi
                    return 0
                else
                    echo -e "${RED}   ${CROSS} Файл повреждён или обрезан${NC}"
                    retry=$((retry + 1))
                    continue
                fi
            else
                retry=$((retry + 1))
                continue
            fi
        else
            # Fallback
            echo -e "${YELLOW}   ⚠️  Используется простая загрузка${NC}"
            if command -v curl &> /dev/null; then
                if curl --proto '=https' --tlsv1.2 --fail -o "$output" "$url"; then
                    if check_file_integrity "$output"; then
                        echo -e "${GREEN}   ${CHECK} Загрузка завершена${NC}"
                        return 0
                    else
                        echo -e "${RED}   ${CROSS} Файл повреждён${NC}"
                        retry=$((retry + 1))
                        continue
                    fi
                else
                    echo -e "${RED}   ${CROSS} Ошибка загрузки${NC}"
                    retry=$((retry + 1))
                    continue
                fi
            else
                echo -e "${RED}   ${CROSS} Ошибка: curl или wget не найдены${NC}"
                return 1
            fi
        fi
    done
    
    # Все попытки исчерпаны
    echo -e "${RED}   ${CROSS} Не удалось скачать файл после ${max_retries} попыток${NC}"
    echo -e "${YELLOW}   💡 Возможные причины:${NC}"
    echo -e "${YELLOW}      - Проблемы с доступностью сервера из вашего региона${NC}"
    echo -e "${YELLOW}      - Проблемы с интернет-соединением${NC}"
    echo -e "${YELLOW}      - Блокировка антивирусом/файрволом${NC}"
    echo ""
    echo -e "${CYAN}   💡 Альтернатива: используйте системный пакетный менеджер${NC}"
    echo -e "${CYAN}      Ubuntu/Debian: sudo apt install rustc cargo${NC}"
    echo -e "${CYAN}      Или скачайте вручную с https://rustup.rs${NC}"
    return 1
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
