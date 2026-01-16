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

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    initBoard();
    loadPreset('english');
});

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
    
    updateStats();
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
    updateStats();
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
        
        updateStats();
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

async function updateStats() {
    const pegs = getPegs();
    document.getElementById('peg-count').textContent = pegs.length;
    
    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pegs })
        });
        
        const data = await response.json();
        
        document.getElementById('moves-available').textContent = data.moves_available;
        
        const indicator = document.getElementById('solvable-indicator');
        indicator.querySelector('.stat-value').textContent = data.is_solvable ? '✓' : '✗';
        indicator.className = `stat ${data.is_solvable ? 'solvable' : 'unsolvable'}`;
        
        document.getElementById('solve-btn').disabled = !data.is_solvable || pegs.length < 2;
    } catch (error) {
        console.error('Error validating:', error);
    }
}

async function solve() {
    const pegs = getPegs();
    if (pegs.length < 2) return;
    
    const solver = document.getElementById('solver-select').value;
    const loading = document.getElementById('loading');
    
    loading.style.display = 'flex';
    
    try {
        const response = await fetch('/api/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pegs, solver })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSolution(data);
        } else {
            alert(`Ошибка: ${data.error}`);
        }
    } catch (error) {
        console.error('Error solving:', error);
        alert('Ошибка при решении');
    } finally {
        loading.style.display = 'none';
    }
}

function showSolution(data) {
    solution = data.moves;
    currentMoveIndex = -1;
    initialBoardState = { ...boardState };
    
    const section = document.getElementById('solution-section');
    section.style.display = 'block';
    
    document.getElementById('solution-stats').textContent = 
        `${data.move_count} ходов • ${data.time}с • ${data.solver}`;
    
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
    
    try {
        // Конвертируем в base64
        const reader = new FileReader();
        
        reader.onload = async function(e) {
            try {
                const response = await fetch('/api/recognize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_data: e.target.result })
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
                    alert(`Распознано ${data.peg_count} колышков`);
                } else {
                    alert(`Ошибка: ${data.error}`);
                }
            } catch (error) {
                console.error('Error recognizing:', error);
                alert('Ошибка при распознавании');
            } finally {
                loading.style.display = 'none';
                loading.querySelector('p').textContent = 'Поиск решения...';
            }
        };
        
        reader.readAsDataURL(file);
    } catch (error) {
        console.error('Error uploading:', error);
        loading.style.display = 'none';
    }
    
    // Сбрасываем input
    event.target.value = '';
}
