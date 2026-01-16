"""
web/app.py

Flask веб-приложение для Peg Solitaire Solver.
"""

import os
import sys
import base64
import io
import time
from flask import Flask, render_template, request, jsonify

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bitboard import BitBoard, ENGLISH_VALID_POSITIONS, CENTER_POS
from core.fast import FastBitBoard, USING_CYTHON, get_implementation_info
from solvers import DFSSolver, BeamSolver, HybridSolver
from heuristics import pagoda_value, PAGODA_WEIGHTS

app = Flask(__name__)

# Маппинг позиции (row, col) -> bit position
def coords_to_bit(row, col):
    return row * 7 + col

def bit_to_coords(bit):
    return bit // 7, bit % 7

# Валидные позиции в координатах
VALID_COORDS = set()
for pos in ENGLISH_VALID_POSITIONS:
    r, c = bit_to_coords(pos)
    VALID_COORDS.add((r, c))


@app.route('/')
def index():
    """Главная страница."""
    return render_template('index.html', 
                          implementation=get_implementation_info(),
                          using_cython=USING_CYTHON)


@app.route('/api/solve', methods=['POST'])
def solve():
    """
    API для решения головоломки.
    
    Входные данные:
    {
        "pegs": [[row, col], ...],  // позиции колышков
        "holes": [[row, col], ...], // позиции пустых мест
        "solver": "beam"            // тип решателя
    }
    """
    data = request.json
    
    pegs_coords = data.get('pegs', [])
    holes_coords = data.get('holes', [])
    solver_type = data.get('solver', 'beam')
    
    # Конвертируем в битовую маску
    pegs_bits = 0
    for row, col in pegs_coords:
        pos = coords_to_bit(row, col)
        if pos in ENGLISH_VALID_POSITIONS:
            pegs_bits |= (1 << pos)
    
    if pegs_bits == 0:
        return jsonify({
            'success': False,
            'error': 'Нет колышков на доске'
        })
    
    peg_count = bin(pegs_bits).count('1')
    
    # Проверка Pagoda
    board = BitBoard(pegs_bits)
    if pagoda_value(board) < PAGODA_WEIGHTS[CENTER_POS]:
        return jsonify({
            'success': False,
            'error': 'Позиция недостижима (Pagoda pruning)',
            'peg_count': peg_count
        })
    
    # Выбор решателя
    solvers = {
        'dfs': lambda: DFSSolver(verbose=False),
        'beam': lambda: BeamSolver(beam_width=200, verbose=False),
        'hybrid': lambda: HybridSolver(timeout=30, verbose=False),
    }
    
    solver = solvers.get(solver_type, solvers['beam'])()
    
    # Решаем
    start_time = time.time()
    try:
        solution = solver.solve(board)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ошибка решателя: {str(e)}'
        })
    
    elapsed = time.time() - start_time
    
    if solution is None:
        return jsonify({
            'success': False,
            'error': 'Решение не найдено',
            'peg_count': peg_count,
            'time': round(elapsed, 3)
        })
    
    # Форматируем решение
    moves = []
    for from_pos, jumped, to_pos in solution:
        fr, fc = bit_to_coords(from_pos)
        tr, tc = bit_to_coords(to_pos)
        jr, jc = bit_to_coords(jumped)
        moves.append({
            'from': {'row': fr, 'col': fc, 'pos': from_pos},
            'jumped': {'row': jr, 'col': jc, 'pos': jumped},
            'to': {'row': tr, 'col': tc, 'pos': to_pos},
            'notation': f"{chr(fc + ord('A'))}{fr + 1} → {chr(tc + ord('A'))}{tr + 1}"
        })
    
    return jsonify({
        'success': True,
        'moves': moves,
        'move_count': len(moves),
        'peg_count': peg_count,
        'time': round(elapsed, 3),
        'solver': solver_type
    })


@app.route('/api/validate', methods=['POST'])
def validate():
    """Валидация позиции."""
    data = request.json
    pegs_coords = data.get('pegs', [])
    
    pegs_bits = 0
    for row, col in pegs_coords:
        pos = coords_to_bit(row, col)
        if pos in ENGLISH_VALID_POSITIONS:
            pegs_bits |= (1 << pos)
    
    peg_count = bin(pegs_bits).count('1')
    
    # Проверка Pagoda
    board = BitBoard(pegs_bits)
    pagoda = pagoda_value(board)
    is_solvable = pagoda >= PAGODA_WEIGHTS[CENTER_POS]
    
    # Проверка ходов
    moves_count = len(board.get_moves())
    
    return jsonify({
        'peg_count': peg_count,
        'moves_available': moves_count,
        'is_solvable': is_solvable,
        'pagoda_value': pagoda,
        'min_pagoda': PAGODA_WEIGHTS[CENTER_POS]
    })


@app.route('/api/recognize', methods=['POST'])
def recognize_image():
    """
    Распознавание позиции по скриншоту.
    """
    if 'image' not in request.files and 'image_data' not in request.json:
        return jsonify({'success': False, 'error': 'Изображение не предоставлено'})
    
    try:
        from PIL import Image
        import numpy as np
        
        if 'image' in request.files:
            image_file = request.files['image']
            img = Image.open(image_file)
        else:
            # Base64 данные
            image_data = request.json['image_data']
            image_bytes = base64.b64decode(image_data.split(',')[1])
            img = Image.open(io.BytesIO(image_bytes))
        
        # Простое распознавание по цветам
        pegs, holes = recognize_board(img)
        
        return jsonify({
            'success': True,
            'pegs': pegs,
            'holes': holes,
            'peg_count': len(pegs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ошибка распознавания: {str(e)}'
        })


def recognize_board(img):
    """
    Простое распознавание доски по изображению.
    Ищет круглые объекты определённых цветов.
    """
    from PIL import Image
    
    # Преобразуем в RGB
    img = img.convert('RGB')
    width, height = img.size
    
    # Определяем размер ячейки (предполагаем квадратную доску 7x7)
    cell_w = width / 7
    cell_h = height / 7
    
    pegs = []
    holes = []
    
    for row in range(7):
        for col in range(7):
            if (row, col) not in VALID_COORDS:
                continue
            
            # Центр ячейки
            cx = int((col + 0.5) * cell_w)
            cy = int((row + 0.5) * cell_h)
            
            # Средний цвет в области
            region = img.crop((
                max(0, cx - int(cell_w * 0.3)),
                max(0, cy - int(cell_h * 0.3)),
                min(width, cx + int(cell_w * 0.3)),
                min(height, cy + int(cell_h * 0.3))
            ))
            
            # Анализируем цвет
            pixels = list(region.getdata())
            if pixels:
                avg_r = sum(p[0] for p in pixels) / len(pixels)
                avg_g = sum(p[1] for p in pixels) / len(pixels)
                avg_b = sum(p[2] for p in pixels) / len(pixels)
                
                # Определяем по цвету (эвристика)
                brightness = (avg_r + avg_g + avg_b) / 3
                
                # Тёмный цвет = колышек, светлый = пустое
                if brightness < 128:
                    pegs.append([row, col])
                else:
                    holes.append([row, col])
    
    return pegs, holes


@app.route('/api/preset/<name>')
def get_preset(name):
    """Получить предустановленную позицию."""
    presets = {
        'english': {
            'name': 'Английская доска',
            'pegs': [[r, c] for r, c in VALID_COORDS if (r, c) != (3, 3)],
            'holes': [[3, 3]]
        },
        'plus': {
            'name': 'Плюс',
            'pegs': [[3, 2], [3, 3], [3, 4], [2, 3], [4, 3]],
            'holes': [[3, 1], [3, 5], [1, 3], [5, 3]]
        },
        'test': {
            'name': 'Тест (8 колышков)',
            'pegs': [[2, 2], [2, 3], [2, 4], [3, 2], [3, 3], [3, 4], [4, 2], [4, 3]],
            'holes': [[r, c] for r, c in VALID_COORDS 
                     if [r, c] not in [[2, 2], [2, 3], [2, 4], [3, 2], [3, 3], [3, 4], [4, 2], [4, 3]]]
        }
    }
    
    if name not in presets:
        return jsonify({'error': 'Preset not found'}), 404
    
    return jsonify(presets[name])


if __name__ == '__main__':
    print("=" * 50)
    print("Peg Solitaire Solver - Web UI")
    print(f"Implementation: {get_implementation_info()}")
    print("=" * 50)
    print("\nOpen http://localhost:5000 in your browser")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
