/**
 * Peg Solitaire Solver - Frontend
 */

// Валидные позиции английской доски (для визуальной подсветки и пресетов)
// Всё поле 7x7 теперь доступно для произвольных досок
const ENGLISH_VALID_POSITIONS = new Set([
    '0,2', '0,3', '0,4',
    '1,2', '1,3', '1,4',
    '2,0', '2,1', '2,2', '2,3', '2,4', '2,5', '2,6',
    '3,0', '3,1', '3,2', '3,3', '3,4', '3,5', '3,6',
    '4,0', '4,1', '4,2', '4,3', '4,4', '4,5', '4,6',
    '5,2', '5,3', '5,4',
    '6,2', '6,3', '6,4'
]);

// Состояние
let boardState = {}; // {row,col} -> 'peg' | 'hole' | undefined (пусто)
let validPositions = ENGLISH_VALID_POSITIONS; // Можно менять для разных типов досок
let solution = null;
let currentMoveIndex = -1;
let isPlaying = false;
let playInterval = null;
let initialBoardState = null; // для воспроизведения
let screenshotImageData = null; // Данные загруженного скриншота
let trainingMode = false; // Режим обучения
let pegSamples = []; // Примеры колышков [[row, col], ...]
let holeSamples = []; // Примеры пустых мест [[row, col], ...]

// Recent Boards
const RECENT_BOARDS_KEY = 'peg_solver_recent_boards';
const MAX_RECENT_BOARDS = 10;

// Описания решателей
const solverDescriptions = {
    'lookup': {
        name: '📚 Lookup',
        description: 'Мгновенное решение для известных позиций из базы решений. Полный алгоритм с автоматическим fallback.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐⭐⭐',
        use: 'Стандартные позиции'
    },
    'governor': {
        name: '🎯 Governor',
        description: 'Умный выбор алгоритма на основе анализа позиции (количество колышков, доступных ходов, сложности). Рекомендуется для большинства случаев.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐⭐⭐',
        use: 'Рекомендуется'
    },
    'parallel_beam': {
        name: '⚡ Parallel Beam',
        description: 'Параллельный Beam Search - распараллеливает обработку каждого уровня. Эффективен для больших позиций (>25 колышков).',
        completeness: '❌ Неполный',
        speed: '⭐⭐⭐⭐',
        use: 'Большие позиции (>25)'
    },
    'parallel': {
        name: '⚡ Parallel DFS',
        description: 'Многопроцессный DFS - распределяет первые ходы между процессами. Полный алгоритм с ускорением на многоядерных системах.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐⭐',
        use: 'Глубокие позиции'
    },
    'beam': {
        name: 'Beam Search',
        description: 'Ограниченный по ширине поиск - сохраняет только K лучших состояний на каждом уровне. Быстрый, но может пропустить решение.',
        completeness: '❌ Неполный',
        speed: '⭐⭐⭐⭐⭐',
        use: 'Универсальный'
    },
    'dfs': {
        name: 'DFS',
        description: 'Поиск в глубину с мемоизацией - исчерпывающий полный алгоритм. Гарантирует нахождение решения, если оно существует.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐',
        use: 'Маленькие позиции (<10)'
    },
    'zobrist_dfs': {
        name: '🔐 Zobrist DFS',
        description: 'DFS с Zobrist Hashing - использует инкрементальное хеширование для быстрой проверки посещённых состояний. Эффективен для глубокого поиска.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐⭐',
        use: 'Глубокий поиск'
    },
    'astar': {
        name: '⭐ A*',
        description: 'A* с эвристиками - оптимальный алгоритм поиска пути. Использует эвристическую оценку для приоритизации состояний.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐⭐',
        use: 'Средние позиции'
    },
    'ida': {
        name: '📊 IDA*',
        description: 'IDA* (Iterative Deepening A*) - экономит память, не храня все состояния. Эффективен для сложных позиций (>20 колышков).',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐',
        use: 'Сложные позиции (>20)'
    },
    'pattern_astar': {
        name: '🎨 Pattern A*',
        description: 'A* с Pattern Database - использует предвычисленные эвристики для 5 регионов доски. Оптимизированный вариант A*.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐⭐',
        use: 'Оптимизированный A*'
    },
    'bidirectional': {
        name: '↔️ Bidirectional',
        description: 'Двунаправленный поиск - ищет от начальной и целевой позиций одновременно. Ускоряет поиск за счёт сокращения пространства.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐⭐',
        use: 'Ускоренный поиск'
    },
    'sequential': {
        name: '🔄 Sequential',
        description: 'Систематический перебор решателей от простых к сложным (Lookup → DFS → Beam → A* → IDA* → Parallel). Продолжает до получения легального решения. Гарантирует проверку всех алгоритмов.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐',
        use: 'Перебор от простых к сложным'
    },
    'hybrid': {
        name: '🔄 Hybrid',
        description: 'Комбинация всех алгоритмов - пробует несколько стратегий по очереди (Beam Search, DFS, A*, IDA*). Автоматический выбор лучшего.',
        completeness: '✅ Полный',
        speed: '⭐⭐⭐⭐',
        use: 'Автоматический выбор'
    },
    'exhaustive': {
        name: '🔍 Exhaustive',
        description: 'Полный перебор всех возможных путей с оценкой промежуточных состояний. Самый медленный, но самый надёжный для сложных позиций. Может занять много времени.',
        completeness: '✅ Полный',
        speed: '⭐',
        use: 'Самые сложные позиции (может занять много времени)'
    },
    'brute_force': {
        name: '💪 Brute Force',
        description: 'Максимально агрессивный поиск БЕЗ Pagoda pruning. Используется только когда все остальные методы не работают. Может работать ОЧЕНЬ долго (30+ минут).',
        completeness: '✅ Полный',
        speed: '🐌',
        use: 'Последняя попытка для нерешаемых позиций (может занять 30+ минут)'
    }
};

// Toast уведомления
function showToast(message, type = 'info', title = null, duration = 0) {
    /**
     * Показывает красивое toast-уведомление.
     * 
     * @param {string} message - Текст сообщения
     * @param {string} type - Тип: 'error', 'warning', 'success', 'info'
     * @param {string|null} title - Заголовок (опционально)
     * @param {number} duration - Длительность показа в мс (0 = без автоскрытия, показывается до закрытия пользователем)
     */
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        error: '❌',
        warning: '⚠️',
        success: '✅',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            ${title ? `<div class="toast-title">${title}</div>` : ''}
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.closest('.toast').remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    // Автоматическое скрытие только если duration > 0
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    // Если duration = 0, уведомление остаётся до закрытия пользователем
    
    return toast;
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    initBoard();
    loadPreset('english');
    
    // Обработчик изменения решателя
    const solverSelect = document.getElementById('solver-select');
    if (solverSelect) {
        solverSelect.addEventListener('change', updateSolverDescription);
        updateSolverDescription(); // Показываем описание для выбранного решателя
    }
    
    // Обработчик Enter для поля ввода координат
    const notationInput = document.getElementById('board-notation-input');
    if (notationInput) {
        notationInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                loadBoardFromNotation();
            }
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter - найти решение
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const solveBtn = document.getElementById('solve-btn');
            if (solveBtn && !solveBtn.disabled) {
                e.preventDefault();
                solve();
            }
        }
        
        // Стрелки для навигации по решению (если решение показано)
        if (solution && solution.length > 0) {
            if (e.key === 'ArrowLeft' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                prevMove();
            } else if (e.key === 'ArrowRight' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                nextMove();
            } else if (e.key === ' ' && !e.ctrlKey && !e.metaKey) {
                // Space для play/pause
                const activeElement = document.activeElement;
                if (activeElement.tagName !== 'INPUT' && activeElement.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    togglePlay();
                }
            } else if (e.key === 'Home' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                goToMove(-1);
            } else if (e.key === 'End' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                goToMove(solution.length - 1);
            }
        }
        
        // Escape для закрытия модальных окон
        if (e.key === 'Escape') {
            const loading = document.getElementById('loading');
            if (loading && loading.style.display !== 'none') {
                // Можно добавить отмену решения, но это сложнее
            }
        }
    });
    
    // Загружаем информацию о модулях
    loadModulesInfo();
    
    // Загружаем список недавних досок
    loadRecentBoards();
    
    // Проверяем решения для недавних досок
    checkBoardsForSolutions();
});

async function loadModulesInfo() {
    /**
     * Загружает и отображает информацию о доступных модулях оптимизации.
     */
    try {
        const response = await fetch('/api/modules');
        const data = await response.json();
        
        if (data.success) {
            displayModulesInfo(data.modules, data.summary);
        }
    } catch (error) {
        console.error('Ошибка при загрузке информации о модулях:', error);
    }
}

function displayModulesInfo(modules, summary) {
    /**
     * Отображает информацию о модулях в info-panel и footer.
     */
    // Отображение в info-panel (детальное)
    const modulesListDiv = document.getElementById('modules-list');
    if (modulesListDiv) {
        modulesListDiv.innerHTML = '';
        
        const moduleOrder = ['cython', 'rust', 'numba'];
        
        for (const moduleKey of moduleOrder) {
            const module = modules[moduleKey];
            if (!module) continue;
            
            const item = document.createElement('div');
            item.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 0.25rem 0;';
            
            const nameDiv = document.createElement('div');
            nameDiv.style.cssText = 'display: flex; align-items: center; gap: 0.5rem;';
            
            const icon = document.createElement('span');
            icon.textContent = module.available ? '✅' : '❌';
            icon.style.cssText = 'font-size: 0.875rem;';
            
            const name = document.createElement('span');
            name.textContent = module.name;
            name.style.cssText = `font-weight: 500; color: ${module.available ? 'var(--success)' : 'var(--danger)'};`;
            
            nameDiv.appendChild(icon);
            nameDiv.appendChild(name);
            
            const speedup = document.createElement('span');
            speedup.textContent = module.speedup;
            speedup.style.cssText = 'font-size: 0.7rem; color: var(--text-secondary);';
            
            item.appendChild(nameDiv);
            item.appendChild(speedup);
            
            item.title = module.description;
            item.style.cursor = 'help';
            
            modulesListDiv.appendChild(item);
        }
        
        // Добавляем общую информацию
        if (summary.available < summary.total) {
            const summaryDiv = document.createElement('div');
            summaryDiv.style.cssText = 'margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--cell-border); font-size: 0.7rem; color: var(--text-secondary);';
            summaryDiv.textContent = `Доступно: ${summary.available}/${summary.total} модулей`;
            modulesListDiv.appendChild(summaryDiv);
        }
    }
    
    // Отображение в footer (компактное)
    const modulesInfoDiv = document.getElementById('modules-info');
    if (modulesInfoDiv) {
        modulesInfoDiv.innerHTML = '';
        
        const moduleOrder = ['cython', 'rust', 'numba'];
        
        for (const moduleKey of moduleOrder) {
            const module = modules[moduleKey];
            if (!module) continue;
            
            const badge = document.createElement('span');
            badge.className = 'module-badge';
            badge.title = `${module.name}: ${module.description} (${module.speedup})`;
            
            if (module.available) {
                badge.classList.add('module-available');
                badge.innerHTML = `✅ ${module.name}`;
            } else {
                badge.classList.add('module-unavailable');
                badge.innerHTML = `❌ ${module.name}`;
            }
            
            modulesInfoDiv.appendChild(badge);
        }
    }
}

function updateSolverDescription() {
    const solverSelect = document.getElementById('solver-select');
    const descriptionDiv = document.getElementById('solver-description');
    const selectedSolver = solverSelect.value;
    
    if (solverDescriptions[selectedSolver]) {
        const info = solverDescriptions[selectedSolver];
        descriptionDiv.innerHTML = `
            <strong>${info.name}:</strong> ${info.description}<br>
            <small style="color: var(--text-secondary); margin-top: 0.25rem; display: block;">
                Полнота: ${info.completeness} • Скорость: ${info.speed} • Применение: ${info.use}
            </small>
        `;
    } else {
        descriptionDiv.textContent = 'Описание недоступно';
    }

    // Показываем доп. опцию 24 часа только для Brute Force
    const bruteWrapper = document.getElementById('bruteforce-24h-wrapper');
    const bruteHint = document.getElementById('bruteforce-24h-hint');
    const bruteCheckbox = document.getElementById('bruteforce-24h-checkbox');
    if (bruteWrapper && bruteHint && bruteCheckbox) {
        const show = selectedSolver === 'brute_force';
        bruteWrapper.style.display = show ? 'flex' : 'none';
        bruteHint.style.display = show ? 'block' : 'none';
        if (!show) {
            bruteCheckbox.checked = false;
        }
    }
}

function initBoard() {
    const board = document.getElementById('board');
    board.innerHTML = '';
    
    // Создаём полное поле 7x7 - все ячейки кликабельны
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.row = row;
            cell.dataset.col = col;
            
            const key = `${row},${col}`;
            // Все ячейки кликабельны - поддерживаем произвольные доски
            cell.classList.add('empty'); // Начальное состояние - пусто
            cell.addEventListener('click', () => toggleCell(row, col));
            
            // Визуальная индикация валидных позиций английской доски (опционально)
            if (ENGLISH_VALID_POSITIONS.has(key)) {
                cell.classList.add('english-valid');
            } else {
                cell.classList.add('custom-pos');
            }
            
            board.appendChild(cell);
        }
    }
}

function toggleCell(row, col) {
    const key = `${row},${col}`;
    const cell = getCell(row, col);
    
    // Циклическое переключение: empty → peg → hole → empty
    const currentState = boardState[key];
    
    if (currentState === 'peg') {
        boardState[key] = 'hole';
        cell.classList.remove('peg');
        cell.classList.add('hole');
    } else if (currentState === 'hole') {
        delete boardState[key]; // Удаляем из состояния = пусто
        cell.classList.remove('hole', 'peg');
        cell.classList.add('empty');
    } else {
        // empty → peg
        boardState[key] = 'peg';
        cell.classList.remove('empty', 'hole');
        cell.classList.add('peg');
    }
    
    updateStats(); // Это также обновит текстовое представление
    hideSolution();
}

function getCell(row, col) {
    return document.querySelector(`.cell[data-row="${row}"][data-col="${col}"]`);
}

function clearBoard() {
    // Очищаем всю доску 7x7
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const key = `${row},${col}`;
            delete boardState[key];
            const cell = getCell(row, col);
            cell.classList.remove('peg', 'hole');
            cell.classList.add('empty');
        }
    }
    updateStats(); // Обновит также текстовое представление
    hideSolution();
}

function fillBoard() {
    // Заполняем всю доску 7x7 колышками
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const key = `${row},${col}`;
            boardState[key] = 'peg';
            const cell = getCell(row, col);
            cell.classList.remove('empty', 'hole');
            cell.classList.add('peg');
        }
    }
    updateStats();
    hideSolution();
}

async function loadPreset(name) {
    try {
        const response = await fetch(`/api/preset/${name}`);
        const data = await response.json();
        
        clearBoard();
        
        // Загружаем колышки
        for (const [row, col] of data.pegs || []) {
            const key = `${row},${col}`;
            if (row >= 0 && row < 7 && col >= 0 && col < 7) {
                boardState[key] = 'peg';
                const cell = getCell(row, col);
                cell.classList.remove('empty', 'hole');
                cell.classList.add('peg');
            }
        }
        
        // Загружаем пустые места (holes) если указаны
        for (const [row, col] of data.holes || []) {
            const key = `${row},${col}`;
            if (row >= 0 && row < 7 && col >= 0 && col < 7 && !boardState[key]) {
                boardState[key] = 'hole';
                const cell = getCell(row, col);
                cell.classList.remove('empty', 'peg');
                cell.classList.add('hole');
            }
        }
        
        updateStats(); // Обновит также текстовое представление
        hideSolution();
    } catch (error) {
        console.error('Error loading preset:', error);
    }
}

function getPegs() {
    const pegs = [];
    // Собираем все колышки со всего поля 7x7
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const key = `${row},${col}`;
            if (boardState[key] === 'peg') {
                pegs.push([row, col]);
            }
        }
    }
    return pegs;
}

function getHoles() {
    const holes = [];
    // Собираем все пустые места (holes) со всего поля 7x7
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const key = `${row},${col}`;
            if (boardState[key] === 'hole') {
                holes.push([row, col]);
            }
        }
    }
    return holes;
}

function getBoardNotation() {
    /**
     * Генерирует текстовое представление доски в формате координат.
     * Формат: A1, B2, C3... где A-G это колонки (0-6), 1-7 это строки (0-6)
     * Пустые места помечаются как (hole)
     */
    const pegs = getPegs();
    const holes = [];
    
    // Собираем пустые места (holes)
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const key = `${row},${col}`;
            if (boardState[key] === 'hole') {
                holes.push([row, col]);
            }
        }
    }
    
    // Преобразуем координаты в буквенно-цифровой формат
    function coordToString(row, col, isHole = false) {
        const letter = String.fromCharCode(65 + col); // A-G (0-6 -> A-G)
        const number = row + 1; // 1-7 (0-6 -> 1-7)
        const coord = `${letter}${number}`;
        return isHole ? `${coord}(hole)` : coord;
    }
    
    // Формируем координатное описание - все в одном списке, пустые места с пометкой (hole)
    const allCoords = [];
    
    // Добавляем колышки
    for (const [row, col] of pegs) {
        allCoords.push(coordToString(row, col, false));
    }
    
    // Добавляем пустые места с пометкой (hole)
    for (const [row, col] of holes) {
        allCoords.push(coordToString(row, col, true));
    }
    
    return allCoords.length > 0 ? allCoords.join(' ') : '(доска пуста)';
}

function updateBoardNotation() {
    const notationTextarea = document.getElementById('board-notation');
    if (notationTextarea) {
        notationTextarea.value = getBoardNotation();
    }
}

function copyBoardNotation() {
    const notationTextarea = document.getElementById('board-notation');
    if (!notationTextarea) return;
    
    notationTextarea.select();
    notationTextarea.setSelectionRange(0, 99999); // Для мобильных устройств
    
    const btn = document.querySelector('.btn-copy');
    const originalText = btn ? btn.textContent : '📋 Копировать';
    
    // Пробуем использовать Clipboard API (современный способ)
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(notationTextarea.value).then(() => {
            if (btn) {
                btn.textContent = '✅ Скопировано!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }, 2000);
            }
        }).catch(err => {
            console.error('Failed to copy:', err);
            // Fallback на execCommand
            fallbackCopy();
        });
    } else {
        // Fallback на execCommand для старых браузеров
        fallbackCopy();
    }
    
    function fallbackCopy() {
        try {
            const successful = document.execCommand('copy');
            if (successful && btn) {
                btn.textContent = '✅ Скопировано!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }, 2000);
            } else {
                showToast('Используйте Ctrl+C (или Cmd+C на Mac) для копирования', 'info', 'Копирование');
            }
        } catch (err) {
            console.error('Failed to copy:', err);
            showToast('Используйте Ctrl+C (или Cmd+C на Mac) для копирования', 'info', 'Копирование');
        }
    }
}

function parseBoardNotation(notation) {
    /**
     * Парсит координатное описание доски.
     * Формат: "A1 B2 C3 D4(hole) E5..." где:
     * - A1, B2, C3 - колышки (pegs)
     * - D4(hole), E5(hole) - пустые места (holes)
     * 
     * Возвращает: { pegs: [[row, col], ...], holes: [[row, col], ...] }
     */
    const pegs = [];
    const holes = [];
    
    if (!notation || notation.trim() === '') {
        return { pegs, holes };
    }
    
    // Разбиваем по пробелам и фильтруем пустые строки
    const parts = notation.trim().split(/\s+/).filter(p => p.length > 0);
    
    for (const part of parts) {
        // Проверяем формат координаты: буква + цифра + опционально (hole)
        const match = part.match(/^([A-G])([1-7])(\(hole\))?$/i);
        
        if (match) {
            const letter = match[1].toUpperCase();
            const number = parseInt(match[2], 10);
            const isHole = match[3] !== undefined;
            
            // Преобразуем в индексы (A=0, B=1, ..., G=6; 1=0, 2=1, ..., 7=6)
            const col = letter.charCodeAt(0) - 65; // A=0, B=1, ..., G=6
            const row = number - 1; // 1=0, 2=1, ..., 7=6
            
            // Проверяем валидность координат
            if (0 <= row && row < 7 && 0 <= col && col < 7) {
                if (isHole) {
                    holes.push([row, col]);
                } else {
                    pegs.push([row, col]);
                }
            } else {
                console.warn(`Некорректные координаты: ${part}`);
            }
        } else {
            console.warn(`Не удалось распарсить: ${part}`);
        }
    }
    
    return { pegs, holes };
}

function loadBoardFromNotation() {
    /**
     * Загружает доску из координатного описания.
     */
    const input = document.getElementById('board-notation-input');
    if (!input) return;
    
        const notation = input.value.trim();
        if (!notation) {
            showToast('Введите координатное описание доски в поле выше.', 'warning', 'Пустое поле');
            return;
        }
    
    try {
        const { pegs, holes } = parseBoardNotation(notation);
        
        if (pegs.length === 0 && holes.length === 0) {
            showToast(
                'Проверьте формат координат. Пример: C1 D1 F1 C2 E2 G2 A3 B3 C3 D3 E3 F3 G3 A4 C4 E4 G4 A5 B5 C5 D5 E5 F5 G5 A6 C6 E6 B7 C7 D7 E7 E1(hole)',
                'error',
                'Не удалось распознать координаты',
                8000
            );
            return;
        }
        
        // Очищаем доску
        clearBoard();
        
        // Применяем колышки
        for (const [row, col] of pegs) {
            const key = `${row},${col}`;
            if (row >= 0 && row < 7 && col >= 0 && col < 7) {
                boardState[key] = 'peg';
                const cell = getCell(row, col);
                cell.classList.remove('empty', 'hole');
                cell.classList.add('peg');
            }
        }
        
        // Применяем пустые места
        for (const [row, col] of holes) {
            const key = `${row},${col}`;
            if (row >= 0 && row < 7 && col >= 0 && col < 7) {
                // Если там уже есть колышек, заменяем на пустое место
                boardState[key] = 'hole';
                const cell = getCell(row, col);
                cell.classList.remove('empty', 'peg');
                cell.classList.add('hole');
            }
        }
        
        // Обновляем статистику и представление
        updateStats();
        hideSolution();
        
        // Сохраняем доску в "известные" при явной загрузке из нотации (кнопка "Применить")
        saveCurrentBoard();
        
        // Показываем сообщение об успехе
        const message = `Загружено: ${pegs.length} колышков, ${holes.length} пустых мест`;
        console.log(message);
        
        // Опционально: можно показать временное уведомление
        const inputContainer = input.closest('.notation-container');
        if (inputContainer) {
            const successMsg = document.createElement('div');
            successMsg.style.cssText = 'color: var(--success); font-size: 0.75rem; margin-top: 0.25rem;';
            successMsg.textContent = `✅ ${message}`;
            inputContainer.appendChild(successMsg);
            setTimeout(() => successMsg.remove(), 3000);
        }
        
    } catch (error) {
        console.error('Ошибка при загрузке доски:', error);
        showToast(error.message || 'Произошла ошибка при загрузке доски', 'error', 'Ошибка');
    }
}

async function updateStats() {
    const pegs = getPegs();
    document.getElementById('peg-count').textContent = pegs.length;
    
    // Обновляем текстовое представление доски
    updateBoardNotation();
    
    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pegs })
        });
        
        const data = await response.json();
        
        document.getElementById('moves-available').textContent = data.moves_available;
        
        // Отображаем теоретическое количество ходов до решения (N-1)
        const movesToSolutionEl = document.getElementById('moves-to-solution');
        if (movesToSolutionEl) {
            movesToSolutionEl.textContent = data.moves_to_solution || (pegs.length > 0 ? pegs.length - 1 : 0);
        }
        
        const indicator = document.getElementById('solvable-indicator');
        indicator.querySelector('.stat-value').textContent = data.is_solvable ? '✓' : '✗';
        indicator.className = `stat ${data.is_solvable ? 'solvable' : 'unsolvable'}`;
        
        document.getElementById('solve-btn').disabled = !data.is_solvable || pegs.length < 2;
    } catch (error) {
        console.error('Error validating:', error);
    }
    
    // НЕ сохраняем автоматически - только по явному запросу (кнопка "Найти Решение" или "Применить")
}

async function solve() {
    const pegs = getPegs();
    if (pegs.length < 2) return;
    
    const holes = getHoles();
    const solver = document.getElementById('solver-select').value;
    const unlimited = document.getElementById('unlimited-checkbox').checked;
    const bruteForce24h = (document.getElementById('bruteforce-24h-checkbox') || {}).checked || false;
    const loading = document.getElementById('loading');
    const progressContainer = document.getElementById('progress-container');
    const progressList = document.getElementById('progress-list');
    const currentMethod = document.getElementById('current-method');
    
    // Показываем контейнер прогресса для решателей с перебором
    const showProgress = ['governor', 'sequential', 'hybrid'].includes(solver);
    if (showProgress) {
        progressContainer.style.display = 'block';
        progressList.innerHTML = '';
        currentMethod.textContent = 'Инициализация...';
    }
    
    loading.style.display = 'flex';
    
    // Используем SSE для решателей с перебором
    if (showProgress) {
        try {
            const response = await fetch('/api/solve-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pegs, solver, unlimited, brute_force_24h: bruteForce24h })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            const methods = new Map(); // Храним состояние методов
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Оставляем неполную строку в буфере
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.type === 'progress') {
                                updateProgress(data, methods, progressList, currentMethod);
                            } else if (data.type === 'result') {
                                if (data.success) {
                                    showSolution(data);
                                    // Сохраняем доску в "известные" только после явного нажатия "Найти Решение"
                                    saveCurrentBoard();
                                } else {
                                    // Красивое сообщение об ошибке с информацией о решателе и времени
                                    const errorMessage = data.error || 'Решение не найдено';
                                    const solverName = data.solver ? (solverDescriptions[data.solver]?.name || data.solver) : 'Неизвестный решатель';
                                    const timeStr = data.time ? `${data.time.toFixed(2)}с` : '';
                                    const timeInfo = timeStr ? ` (${timeStr})` : '';
                                    
                                    if (errorMessage.includes('не найдено') || errorMessage.includes('не найдено')) {
                                        showToast(
                                            `Попробуйте другой решатель или включите "Без ограничений" для более глубокого поиска.${timeInfo}`,
                                            'warning',
                                            `Решение не найдено (${solverName})`
                                        );
                                    } else {
                                        showToast(
                                            `${errorMessage}${timeInfo}`,
                                            'error',
                                            `Ошибка (${solverName})`
                                        );
                                    }
                                }
                                loading.style.display = 'none';
                                if (showProgress) {
                                    progressContainer.style.display = 'none';
                                }
                                return;
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error solving:', error);
            showToast('Произошла ошибка при попытке найти решение. Проверьте подключение к серверу.', 'error', 'Ошибка соединения');
            loading.style.display = 'none';
            if (showProgress) {
                progressContainer.style.display = 'none';
            }
        }
    } else {
        // Для обычных решателей используем старый API
        try {
            // Логируем запрос на решение для отладки
            console.log('Solve request payload', {
                pegs,
                holes,
                solver,
                unlimited,
                bruteForce24h
            });

            const response = await fetch('/api/solve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pegs, holes, solver, unlimited, brute_force_24h: bruteForce24h })
            });
            
            const data = await response.json();
            console.log('Solve response', data);
            
            if (data.success) {
                showSolution(data);
                // Сохраняем доску в "известные" только после явного нажатия "Найти Решение"
                saveCurrentBoard();
            } else {
                // Красивое сообщение об ошибке с информацией о решателе и времени
                const errorMessage = data.error || 'Решение не найдено';
                const solverName = data.solver ? (solverDescriptions[data.solver]?.name || data.solver) : 'Неизвестный решатель';
                const timeStr = data.time ? `${data.time.toFixed(2)}с` : '';
                const timeInfo = timeStr ? ` (${timeStr})` : '';
                
                if (errorMessage.includes('не найдено') || errorMessage.includes('не найдено')) {
                    showToast(
                        `Попробуйте другой решатель или включите "Без ограничений" для более глубокого поиска.${timeInfo}`,
                        'warning',
                        `Решение не найдено (${solverName})`
                    );
                } else {
                    showToast(
                        `${errorMessage}${timeInfo}`,
                        'error',
                        `Ошибка (${solverName})`
                    );
                }
            }
        } catch (error) {
            console.error('Error solving:', error);
            showToast('Произошла ошибка при попытке найти решение. Проверьте подключение к серверу.', 'error', 'Ошибка соединения');
        } finally {
            loading.style.display = 'none';
        }
    }
}

function updateProgress(data, methods, progressList, currentMethod) {
    const methodName = data.method;
    const status = data.status;
    const elapsed = data.elapsed;
    const total = data.total;
    const current = data.current;
    
    // Обновляем или создаём элемент метода
    if (!methods.has(methodName)) {
        const item = document.createElement('div');
        item.className = 'progress-item';
        item.id = `progress-${methodName.replace(/\s+/g, '-')}`;
        item.innerHTML = `
            <span class="progress-check">⏳</span>
            <span class="progress-name">${methodName}</span>
            <span class="progress-time">-</span>
        `;
        progressList.appendChild(item);
        methods.set(methodName, item);
    }
    
    const item = methods.get(methodName);
    const checkSpan = item.querySelector('.progress-check');
    const timeSpan = item.querySelector('.progress-time');
    
    // Обновляем статус
    if (status === 'starting') {
        checkSpan.textContent = '⏳';
        checkSpan.className = 'progress-check running';
        timeSpan.textContent = 'Запуск...';
        currentMethod.textContent = `${methodName} - запуск...`;
    } else if (status === 'running') {
        checkSpan.textContent = '⏳';
        checkSpan.className = 'progress-check running';
        if (elapsed !== null) {
            timeSpan.textContent = `${elapsed}с`;
            currentMethod.textContent = `${methodName} - ${elapsed}с`;
        }
    } else if (status === 'completed') {
        checkSpan.textContent = '✅';
        checkSpan.className = 'progress-check completed';
        if (elapsed !== null) {
            timeSpan.textContent = `${elapsed}с`;
        }
        currentMethod.textContent = `${methodName} - завершён (${elapsed}с)`;
    } else if (status === 'failed') {
        checkSpan.textContent = '❌';
        checkSpan.className = 'progress-check failed';
        if (elapsed !== null) {
            timeSpan.textContent = `${elapsed}с`;
        }
        currentMethod.textContent = `${methodName} - не найдено (${elapsed}с)`;
    }
    
    // Показываем прогресс если есть
    if (total && current) {
        const progressText = `[${current}/${total}]`;
        if (!item.querySelector('.progress-counter')) {
            const counter = document.createElement('span');
            counter.className = 'progress-counter';
            item.appendChild(counter);
        }
        item.querySelector('.progress-counter').textContent = progressText;
    }
}

function showSolution(data) {
    solution = data.moves;
    currentMoveIndex = -1;
    initialBoardState = { ...boardState };
    
    const section = document.getElementById('solution-section');
    section.style.display = 'block';
    
    // Форматируем название решателя
    const solverName = solverDescriptions[data.solver]?.name || data.solver || 'Неизвестный';
    const timeStr = typeof data.time === 'number' ? data.time.toFixed(2) : data.time || '?';
    
    document.getElementById('solution-stats').textContent = 
        `${data.move_count} ходов • ${timeStr}с • ${solverName}`;
    
    const movesList = document.getElementById('moves-list');
    movesList.innerHTML = '';
    
    for (let i = 0; i < solution.length; i++) {
        const move = solution[i];
        const item = document.createElement('div');
        item.className = 'move-item';
        item.dataset.index = i;
        item.innerHTML = `
            <span class="move-num">${i + 1}.</span>
            <span>${move.notation}</span>
        `;
        item.addEventListener('click', () => goToMove(i));
        movesList.appendChild(item);
    }
    
    section.scrollIntoView({ behavior: 'smooth' });
    
    // Показываем toast-уведомление с информацией о решателе и времени
    const solverDisplayName = solverDescriptions[data.solver]?.name || data.solver || 'Неизвестный решатель';
    showToast(
        `Найдено решение из ${data.move_count} ходов за ${timeStr} секунд`,
        'success',
        `✅ Решение найдено (${solverDisplayName})`
    );
}

function formatSolutionForTelegram() {
    /**
     * Форматирует решение для отправки в Telegram.
     * Формат: компактный список ходов с эмодзи.
     */
    if (!solution || solution.length === 0) {
        return '';
    }
    
    const boardNotation = getBoardNotation();
    const solverName = document.getElementById('solution-stats')?.textContent || 'Решение';
    
    let text = `🎯 Решение Peg Solitaire\n\n`;
    text += `📋 Доска: ${boardNotation}\n`;
    text += `📊 ${solverName}\n\n`;
    text += `📝 Ходы:\n`;
    
    // Группируем ходы по 5 для читаемости
    for (let i = 0; i < solution.length; i++) {
        const move = solution[i];
        const moveNum = (i + 1).toString().padStart(2, '0');
        
        if (i > 0 && i % 5 === 0) {
            text += '\n'; // Новая строка каждые 5 ходов
        }
        
        text += `${moveNum}. ${move.notation}  `;
    }
    
    text += `\n\n✅ Всего ходов: ${solution.length}`;
    
    return text;
}

function copySolutionForTelegram() {
    /**
     * Копирует решение в формате для Telegram в буфер обмена.
     */
    if (!solution || solution.length === 0) {
        showToast('Нет решения для копирования', 'warning', 'Ошибка');
        return;
    }
    
    const text = formatSolutionForTelegram();
    const btn = event?.target || document.querySelector('button[onclick="copySolutionForTelegram()"]');
    const originalText = btn ? btn.textContent : '📱 Telegram';
    
    // Пробуем использовать Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            if (btn) {
                btn.textContent = '✅ Скопировано!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }, 2000);
            }
            showToast('Решение скопировано в буфер обмена для Telegram', 'success', 'Скопировано');
        }).catch(err => {
            console.error('Failed to copy:', err);
            fallbackCopy(text, btn, originalText);
        });
    } else {
        fallbackCopy(text, btn, originalText);
    }
    
    function fallbackCopy(text, btn, originalText) {
        // Fallback на создание временного textarea
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                if (btn) {
                    btn.textContent = '✅ Скопировано!';
                    btn.classList.add('copied');
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.classList.remove('copied');
                    }, 2000);
                }
                showToast('Решение скопировано в буфер обмена для Telegram', 'success', 'Скопировано');
            } else {
                showToast('Не удалось скопировать. Используйте Ctrl+C', 'error', 'Ошибка');
            }
        } catch (err) {
            console.error('Failed to copy:', err);
            showToast('Не удалось скопировать. Используйте Ctrl+C', 'error', 'Ошибка');
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

function hideSolution() {
    document.getElementById('solution-section').style.display = 'none';
    solution = null;
    currentMoveIndex = -1;
    stopPlay();
    clearHighlights();
}

function goToMove(index) {
    if (!solution) return;
    
    // Восстанавливаем начальное состояние
    boardState = { ...initialBoardState };
    renderBoard();
    
    // Применяем ходы до index включительно
    for (let i = 0; i <= index; i++) {
        applyMove(solution[i], false);
    }
    
    currentMoveIndex = index;
    
    // Подсвечиваем текущий ход
    clearHighlights();
    if (index >= 0 && index < solution.length) {
        highlightMove(solution[index]);
    }
    
    // Обновляем активный элемент в списке
    document.querySelectorAll('.move-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });
    
    // Обновляем статистику, но НЕ сохраняем доску (это пошаговое выполнение решения)
    updateStats();
}

function applyMove(move, animate = true) {
    const { from, jumped, to } = move;
    
    // Удаляем колышек с исходной позиции
    const fromKey = `${from.row},${from.col}`;
    boardState[fromKey] = 'hole';
    const fromCell = getCell(from.row, from.col);
    fromCell.classList.remove('peg');
    fromCell.classList.add('hole');
    
    // Удаляем перепрыгнутый колышек
    const jumpedKey = `${jumped.row},${jumped.col}`;
    boardState[jumpedKey] = 'hole';
    const jumpedCell = getCell(jumped.row, jumped.col);
    jumpedCell.classList.remove('peg');
    jumpedCell.classList.add('hole');
    
    // Добавляем колышек на новую позицию
    const toKey = `${to.row},${to.col}`;
    boardState[toKey] = 'peg';
    const toCell = getCell(to.row, to.col);
    toCell.classList.remove('hole');
    toCell.classList.add('peg');
}

function highlightMove(move) {
    const { from, jumped, to } = move;
    
    getCell(from.row, from.col).classList.add('highlight-from');
    getCell(jumped.row, jumped.col).classList.add('highlight-jumped');
    getCell(to.row, to.col).classList.add('highlight-to');
}

function clearHighlights() {
    document.querySelectorAll('.cell').forEach(cell => {
        cell.classList.remove('highlight-from', 'highlight-jumped', 'highlight-to');
    });
}

function renderBoard() {
    // Отрисовываем всё поле 7x7
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const key = `${row},${col}`;
            const cell = getCell(row, col);
            const state = boardState[key];
            
            cell.classList.remove('peg', 'hole', 'empty');
            
            if (state === 'peg') {
                cell.classList.add('peg');
            } else if (state === 'hole') {
                cell.classList.add('hole');
            } else {
                cell.classList.add('empty');
            }
        }
    }
}

function prevMove() {
    if (!solution || currentMoveIndex < 0) return;
    goToMove(currentMoveIndex - 1);
}

function nextMove() {
    if (!solution || currentMoveIndex >= solution.length - 1) return;
    goToMove(currentMoveIndex + 1);
}

function togglePlay() {
    if (isPlaying) {
        stopPlay();
    } else {
        startPlay();
    }
}

function startPlay() {
    if (!solution) return;
    
    isPlaying = true;
    document.getElementById('play-btn').textContent = '⏸️ Пауза';
    
    // Если в конце, начинаем сначала
    if (currentMoveIndex >= solution.length - 1) {
        goToMove(-1);
    }
    
    playInterval = setInterval(() => {
        if (currentMoveIndex >= solution.length - 1) {
            stopPlay();
            return;
        }
        nextMove();
    }, 800);
}

function stopPlay() {
    isPlaying = false;
    document.getElementById('play-btn').textContent = '▶️ Воспроизвести';
    
    if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
    }
}

function resetSolution() {
    if (!solution) return;
    stopPlay();
    goToMove(-1);
    boardState = { ...initialBoardState };
    renderBoard();
    clearHighlights();
    
    document.querySelectorAll('.move-item').forEach(item => {
        item.classList.remove('active');
    });
    
    updateStats();
}

async function uploadScreenshot(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const loading = document.getElementById('loading');
    loading.querySelector('p').textContent = 'Распознавание...';
    loading.style.display = 'flex';
    
    // Показываем превью скриншота
    const preview = document.getElementById('screenshot-preview');
    const img = document.getElementById('screenshot-img');
    const actions = document.getElementById('screenshot-actions');
    const reader = new FileReader();
    
    // Сбрасываем режим обучения
    trainingMode = false;
    pegSamples = [];
    holeSamples = [];
    
    reader.onload = function(e) {
        screenshotImageData = e.target.result;
        img.src = e.target.result;
        preview.style.display = 'block';
        actions.style.display = 'block';
        
        // Убираем старые обработчики
        img.onclick = null;
        
        // Отправляем на автоматическое распознавание
        recognizeScreenshot(e.target.result);
    };
    
    reader.readAsDataURL(file);
}

async function recognizeScreenshot(imageData, useSamples = false) {
    const loading = document.getElementById('loading');
    
    try {
        const requestData = { image_data: imageData };
        if (useSamples && (pegSamples.length > 0 || holeSamples.length > 0)) {
            requestData.pegs_samples = pegSamples;
            requestData.holes_samples = holeSamples;
        }
        
        const response = await fetch('/api/recognize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Применяем распознанную позицию
            clearBoard();
            
            for (const [row, col] of data.pegs) {
                const key = `${row},${col}`;
                if (row >= 0 && row < 7 && col >= 0 && col < 7) {
                    boardState[key] = 'peg';
                    const cell = getCell(row, col);
                    cell.classList.remove('empty', 'hole');
                    cell.classList.add('peg');
                }
            }
            
            updateStats();
            const msg = useSamples ? 
                `Распознано с примерами: ${data.peg_count} колышков` :
                `Распознано: ${data.peg_count} колышков. Если неверно - используйте режим обучения.`;
            showToast(msg, 'success', 'Распознавание завершено');
        } else {
            showToast(data.error || 'Не удалось распознать позицию', 'error', 'Ошибка распознавания');
        }
    } catch (error) {
        console.error('Error recognizing:', error);
        showToast('Произошла ошибка при распознавании изображения', 'error', 'Ошибка');
    } finally {
        loading.style.display = 'none';
        loading.querySelector('p').textContent = 'Поиск решения...';
    }
}

function startTrainingMode() {
    trainingMode = true;
    pegSamples = [];
    holeSamples = [];
    
    const img = document.getElementById('screenshot-img');
    const modeDiv = document.getElementById('screenshot-mode');
    const statusSpan = document.getElementById('mode-status');
    const recognizeBtn = document.getElementById('recognize-samples-btn');
    
    modeDiv.style.display = 'block';
    statusSpan.textContent = `Колышков: ${pegSamples.length}, Пустых: ${holeSamples.length}`;
    recognizeBtn.style.display = 'none';
    
    img.onclick = function(e) {
        if (!trainingMode) return;
        
        const rect = img.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Преобразуем координаты клика в координаты доски 7x7
        const imgWidth = img.naturalWidth || img.width;
        const imgHeight = img.naturalHeight || img.height;
        const scaleX = imgWidth / rect.width;
        const scaleY = imgHeight / rect.height;
        
        const imgX = x * scaleX;
        const imgY = y * scaleY;
        
        // Определяем границы доски (предполагаем квадратную область в центре)
        const boardSize = Math.min(imgWidth, imgHeight) * 0.7; // 70% размера
        const boardLeft = (imgWidth - boardSize) / 2;
        const boardTop = (imgHeight - boardSize) / 2;
        
        const cellSize = boardSize / 7;
        const col = Math.floor((imgX - boardLeft) / cellSize);
        const row = Math.floor((imgY - boardTop) / cellSize);
        
        if (row >= 0 && row < 7 && col >= 0 && col < 7) {
            // Переключаем режим: левый клик = колышек, правый = пустое
            if (e.button === 0 || !e.button) { // Левая кнопка
                // Добавляем/удаляем пример колышка
                const idx = pegSamples.findIndex(([r, c]) => r === row && c === col);
                if (idx >= 0) {
                    pegSamples.splice(idx, 1);
                } else {
                    pegSamples.push([row, col]);
                    // Убираем из пустых, если был
                    holeSamples = holeSamples.filter(([r, c]) => !(r === row && c === col));
                }
            } else if (e.button === 2) { // Правая кнопка
                const idx = holeSamples.findIndex(([r, c]) => r === row && c === col);
                if (idx >= 0) {
                    holeSamples.splice(idx, 1);
                } else {
                    holeSamples.push([row, col]);
                    pegSamples = pegSamples.filter(([r, c]) => !(r === row && c === col));
                }
            }
            
            statusSpan.textContent = `Колышков: ${pegSamples.length}, Пустых: ${holeSamples.length}`;
            
            if (pegSamples.length > 0 || holeSamples.length > 0) {
                recognizeBtn.style.display = 'inline-block';
            }
        }
    };
    
    img.oncontextmenu = function(e) {
        e.preventDefault(); // Блокируем контекстное меню
        return false;
    };
    
    showToast(
        '• Левый клик на скриншоте = отметить колышек\n• Правый клик = отметить пустое место\n• Клик ещё раз = снять отметку\n• Затем нажмите "Распознать с примерами"',
        'info',
        'Режим обучения'
    );
}

function recognizeWithSamples() {
    if (!screenshotImageData) return;
    
    const loading = document.getElementById('loading');
    loading.querySelector('p').textContent = 'Распознавание с примерами...';
    loading.style.display = 'flex';
    
    recognizeScreenshot(screenshotImageData, true);
}

// Recent Boards Functions
function getRecentBoards() {
    try {
        const stored = localStorage.getItem(RECENT_BOARDS_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        console.error('Error loading recent boards:', e);
        return [];
    }
}

function saveRecentBoards(boards) {
    try {
        localStorage.setItem(RECENT_BOARDS_KEY, JSON.stringify(boards));
    } catch (e) {
        console.error('Error saving recent boards:', e);
    }
}

function saveCurrentBoard() {
    const pegs = getPegs();
    const holes = [];
    
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const key = `${row},${col}`;
            if (boardState[key] === 'hole') {
                holes.push([row, col]);
            }
        }
    }
    
    if (pegs.length === 0) return; // Не сохраняем пустые доски
    
    const boardData = {
        pegs: pegs,
        holes: holes,
        notation: getBoardNotation(),
        timestamp: Date.now(),
        pegCount: pegs.length
    };
    
    let boards = getRecentBoards();
    
    // Удаляем дубликаты (по координатам)
    const boardKey = JSON.stringify({ 
        pegs: pegs.sort((a, b) => a[0] - b[0] || a[1] - b[1]), 
        holes: holes.sort((a, b) => a[0] - b[0] || a[1] - b[1])
    });
    boards = boards.filter(b => {
        const bPegs = (b.pegs || []).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
        const bHoles = (b.holes || []).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
        const bKey = JSON.stringify({ pegs: bPegs, holes: bHoles });
        return bKey !== boardKey;
    });
    
    // Добавляем в начало
    boards.unshift(boardData);
    
    // Ограничиваем количество
    boards = boards.slice(0, MAX_RECENT_BOARDS);
    
    saveRecentBoards(boards);
    loadRecentBoards();
}

function loadRecentBoards() {
    const boards = getRecentBoards();
    const container = document.getElementById('recent-boards-list');
    if (!container) return;
    
    if (boards.length === 0) {
        container.innerHTML = '<div style="font-size: 0.75rem; color: var(--text-secondary); text-align: center; padding: 1rem;">Нет сохранённых досок</div>';
        return;
    }
    
    container.innerHTML = '';
    
    for (const board of boards) {
        const item = createRecentBoardItem(board);
        container.appendChild(item);
    }
}

function createRecentBoardItem(board) {
    const item = document.createElement('div');
    item.className = 'recent-board-item';
    
    // Создаём миниатюру
    const thumbnail = document.createElement('div');
    thumbnail.className = 'recent-board-thumbnail';
    
    // Создаём сетку 7x7
    for (let row = 0; row < 7; row++) {
        for (let col = 0; col < 7; col++) {
            const cell = document.createElement('div');
            cell.className = 'recent-board-thumbnail-cell';
            
            const peg = board.pegs.find(p => p[0] === row && p[1] === col);
            const hole = (board.holes || []).find(h => h[0] === row && h[1] === col);
            
            if (peg) {
                cell.classList.add('peg');
            } else if (hole) {
                cell.classList.add('hole');
            } else {
                cell.classList.add('empty');
            }
            
            thumbnail.appendChild(cell);
        }
    }
    
    // Информация о доске
    const info = document.createElement('div');
    info.className = 'recent-board-info';
    
    const title = document.createElement('div');
    title.className = 'recent-board-title';
    title.textContent = board.notation ? board.notation.substring(0, 40) + (board.notation.length > 40 ? '...' : '') : `Доска (${board.pegCount} колышков)`;
    
    const meta = document.createElement('div');
    meta.className = 'recent-board-meta';
    
    const pegCount = document.createElement('span');
    pegCount.textContent = `${board.pegCount} колышков`;
    
    const date = document.createElement('span');
    const dateObj = new Date(board.timestamp);
    date.textContent = dateObj.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
    
    meta.appendChild(pegCount);
    meta.appendChild(date);
    
    // Проверяем, есть ли решение в lookup
    if (board.hasSolution) {
        const badge = document.createElement('span');
        badge.className = 'recent-board-badge solved';
        badge.textContent = '✅ Решение есть';
        meta.appendChild(badge);
    }
    
    info.appendChild(title);
    info.appendChild(meta);
    
    // Действия
    const actions = document.createElement('div');
    actions.className = 'recent-board-actions';
    
    const loadBtn = document.createElement('button');
    loadBtn.className = 'recent-board-action';
    loadBtn.innerHTML = '📥';
    loadBtn.title = 'Загрузить доску';
    loadBtn.onclick = (e) => {
        e.stopPropagation();
        loadBoardFromRecent(board);
    };
    
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'recent-board-action';
    deleteBtn.innerHTML = '🗑️';
    deleteBtn.title = 'Удалить';
    deleteBtn.onclick = (e) => {
        e.stopPropagation();
        deleteRecentBoard(board);
    };
    
    actions.appendChild(loadBtn);
    actions.appendChild(deleteBtn);
    
    // Клик по всей карточке загружает доску
    item.onclick = () => loadBoardFromRecent(board);
    
    item.appendChild(thumbnail);
    item.appendChild(info);
    item.appendChild(actions);
    
    return item;
}

async function loadBoardFromRecent(board) {
    clearBoard();
    
    // Загружаем колышки
    for (const [row, col] of board.pegs || []) {
        const key = `${row},${col}`;
        if (row >= 0 && row < 7 && col >= 0 && col < 7) {
            boardState[key] = 'peg';
            const cell = getCell(row, col);
            cell.classList.remove('empty', 'hole');
            cell.classList.add('peg');
        }
    }
    
    // Загружаем пустые места
    for (const [row, col] of board.holes || []) {
        const key = `${row},${col}`;
        if (row >= 0 && row < 7 && col >= 0 && col < 7) {
            boardState[key] = 'hole';
            const cell = getCell(row, col);
            cell.classList.remove('empty', 'peg');
            cell.classList.add('hole');
        }
    }
    
    updateStats();
    hideSolution();
    
    // Проверяем lookup и показываем решение если есть
    try {
        const response = await fetch('/api/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                pegs: board.pegs, 
                holes: board.holes || [],
                solver: 'lookup'
            })
        });
        
        const data = await response.json();
        if (data.success && data.moves) {
            // showSolution уже покажет toast с информацией о решателе и времени
            showSolution(data);
        }
    } catch (error) {
        console.error('Error checking lookup:', error);
    }
    
    showToast('Доска загружена', 'success', '');
}

function deleteRecentBoard(board) {
    let boards = getRecentBoards();
    boards = boards.filter(b => b.timestamp !== board.timestamp);
    saveRecentBoards(boards);
    loadRecentBoards();
    showToast('Доска удалена из списка', 'info', '');
}

function clearRecentBoards() {
    if (confirm('Удалить все сохранённые доски?')) {
        saveRecentBoards([]);
        loadRecentBoards();
        showToast('Все доски удалены', 'info', '');
    }
}

// Проверяем lookup для всех досок при загрузке
async function checkBoardsForSolutions() {
    const boards = getRecentBoards();
    if (boards.length === 0) return;
    
    // Проверяем только первые 5 досок (чтобы не перегружать)
    for (const board of boards.slice(0, 5)) {
        if (board.hasSolution !== undefined) continue; // Уже проверено
        
        try {
            const response = await fetch('/api/solve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    pegs: board.pegs, 
                    holes: board.holes || [],
                    solver: 'lookup'
                })
            });
            
            const data = await response.json();
            board.hasSolution = data.success;
        } catch (error) {
            board.hasSolution = false;
        }
    }
    
    // Сохраняем обновлённые данные
    saveRecentBoards(boards);
    loadRecentBoards();
}
