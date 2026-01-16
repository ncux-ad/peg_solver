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
from solvers import DFSSolver, BeamSolver, HybridSolver, GovernorSolver
from heuristics import pagoda_value, PAGODA_WEIGHTS

# Минимальный Pagoda вес для любой валидной позиции (для произвольных начальных состояний)
# Цель - 1 колышек в любой позиции, поэтому нужен минимум среди всех позиций
MIN_PAGODA_ANY_POS = min(PAGODA_WEIGHTS.values())  # Минимум = 1

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
    # Поддерживаем произвольные позиции на поле 7x7
    pegs_bits = 0
    for row, col in pegs_coords:
        if 0 <= row < 7 and 0 <= col < 7:
            pos = coords_to_bit(row, col)
            # Принимаем все позиции на поле 7x7 (0-48)
            # Валидация английской доски будет проверена позже через Pagoda
            if 0 <= pos < 49:
                pegs_bits |= (1 << pos)
    
    if pegs_bits == 0:
        return jsonify({
            'success': False,
            'error': 'Нет колышков на доске'
        })
    
    peg_count = bin(pegs_bits).count('1')
    
    # Проверка Pagoda для произвольных начальных состояний
    # Цель - 1 колышек в любой валидной позиции (не обязательно центр)
    board = BitBoard(pegs_bits)
    pagoda_val = pagoda_value(board)
    
    # Для проверки решаемости: текущая Pagoda должна быть >= минимальной среди всех позиций
    # Это мягкая проверка - более строгие проверки сделает сам решатель
    if pagoda_val < MIN_PAGODA_ANY_POS:
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
        'governor': lambda: GovernorSolver(timeout=30, verbose=False),  # Уменьшен timeout
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
        if 0 <= row < 7 and 0 <= col < 7:
            pos = coords_to_bit(row, col)
            if 0 <= pos < 49:
                pegs_bits |= (1 << pos)
    
    peg_count = bin(pegs_bits).count('1')
    
    # Проверка Pagoda для произвольных начальных состояний
    board = BitBoard(pegs_bits)
    pagoda = pagoda_value(board)
    
    # Мягкая проверка: текущая Pagoda >= минимума среди всех позиций
    # Более строгие проверки сделает решатель
    is_solvable = pagoda >= MIN_PAGODA_ANY_POS
    
    # Проверка ходов
    moves_count = len(board.get_moves())
    
    return jsonify({
        'peg_count': peg_count,
        'moves_available': moves_count,
        'is_solvable': is_solvable,
        'pagoda_value': pagoda,
        'min_pagoda': MIN_PAGODA_ANY_POS,
        'note': 'Цель - 1 колышек в любой валидной позиции'
    })


@app.route('/api/recognize', methods=['POST'])
def recognize_image():
    """
    Распознавание позиции по скриншоту.
    Поддерживает два режима:
    1. Автоматическое распознавание (без examples)
    2. Обучение на примерах (с examples: pegs_samples, holes_samples)
    """
    if 'image' not in request.files and 'image_data' not in request.json:
        return jsonify({'success': False, 'error': 'Изображение не предоставлено'})
    
    try:
        from PIL import Image
        
        if 'image' in request.files:
            image_file = request.files['image']
            img = Image.open(image_file)
        else:
            # Base64 данные
            image_data = request.json['image_data']
            image_bytes = base64.b64decode(image_data.split(',')[1])
            img = Image.open(io.BytesIO(image_bytes))
        
        # Проверяем, есть ли примеры для обучения
        pegs_samples = request.json.get('pegs_samples', [])  # [[row, col], ...]
        holes_samples = request.json.get('holes_samples', [])  # [[row, col], ...]
        
        if pegs_samples or holes_samples:
            # Режим обучения на примерах - более точный
            pegs, holes = recognize_board_with_samples(img, pegs_samples, holes_samples)
        else:
            # Автоматическое распознавание (старый алгоритм)
            pegs, holes = recognize_board(img)
        
        return jsonify({
            'success': True,
            'pegs': pegs,
            'holes': holes,
            'peg_count': len(pegs)
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': f'Ошибка распознавания: {str(e)}\n{traceback.format_exc()}'
        })


def recognize_board_with_samples(img, pegs_samples, holes_samples):
    """
    Распознавание доски на основе примеров от пользователя.
    Использует примеры колышков и пустых мест для обучения простого классификатора.
    """
    from PIL import Image
    
    img = img.convert('RGB')
    width, height = img.size
    
    # Обнаруживаем область доски
    board_bounds = detect_board_bounds(img)
    if board_bounds:
        left, top, right, bottom = board_bounds
        img = img.crop((left, top, right, bottom))
        width, height = img.size
    
    cell_w = width / 7
    cell_h = height / 7
    
    # Собираем характеристики примеров
    peg_features = []
    hole_features = []
    
    def get_cell_features(row, col):
        """Извлекает характеристики ячейки."""
        cx = int((col + 0.5) * cell_w)
        cy = int((row + 0.5) * cell_h)
        radius = int(min(cell_w, cell_h) * 0.35)
        
        # Берём большую выборку точек
        sample_points = []
        for dx in range(-radius, radius + 1, max(1, radius // 3)):
            for dy in range(-radius, radius + 1, max(1, radius // 3)):
                px, py = cx + dx, cy + dy
                if 0 <= px < width and 0 <= py < height:
                    sample_points.append(img.getpixel((px, py)))
        
        if not sample_points:
            return None
        
        # Метрики
        avg_r = sum(p[0] for p in sample_points) / len(sample_points)
        avg_g = sum(p[1] for p in sample_points) / len(sample_points)
        avg_b = sum(p[2] for p in sample_points) / len(sample_points)
        brightness = (avg_r + avg_g + avg_b) / 3
        
        # Центральная точка
        center_r, center_g, center_b = img.getpixel((cx, cy)) if 0 <= cx < width and 0 <= cy < height else (0, 0, 0)
        center_brightness = (center_r + center_g + center_b) / 3
        
        return {
            'brightness': brightness,
            'center_brightness': center_brightness,
            'r': avg_r, 'g': avg_g, 'b': avg_b,
            'warmth': avg_r + avg_g - avg_b,
        }
    
    # Собираем примеры
    for row, col in pegs_samples:
        features = get_cell_features(row, col)
        if features:
            peg_features.append(features)
    
    for row, col in holes_samples:
        features = get_cell_features(row, col)
        if features:
            hole_features.append(features)
    
    if not peg_features and not hole_features:
        # Нет примеров - используем автоматическое распознавание
        return recognize_board(img)
    
    # Вычисляем средние характеристики примеров
    if peg_features:
        avg_peg_brightness = sum(f['brightness'] for f in peg_features) / len(peg_features)
        avg_peg_warmth = sum(f['warmth'] for f in peg_features) / len(peg_features)
        avg_peg_center = sum(f['center_brightness'] for f in peg_features) / len(peg_features)
    else:
        avg_peg_brightness = avg_peg_warmth = avg_peg_center = 200
    
    if hole_features:
        avg_hole_brightness = sum(f['brightness'] for f in hole_features) / len(hole_features)
        avg_hole_warmth = sum(f['warmth'] for f in hole_features) / len(hole_features)
        avg_hole_center = sum(f['center_brightness'] for f in hole_features) / len(hole_features)
    else:
        avg_hole_brightness = avg_hole_warmth = avg_hole_center = 50
    
    # Порог между колышками и пустыми
    brightness_threshold = (avg_peg_brightness + avg_hole_brightness) / 2
    
    # Классифицируем все ячейки
    pegs = []
    holes = []
    
    for row in range(7):
        for col in range(7):
            features = get_cell_features(row, col)
            if not features:
                continue
            
            # Расстояние до примеров колышков и пустых мест
            if peg_features:
                peg_dist = min(
                    abs(features['brightness'] - f['brightness']) +
                    abs(features['warmth'] - f['warmth']) * 0.1
                    for f in peg_features
                )
            else:
                peg_dist = float('inf')
            
            if hole_features:
                hole_dist = min(
                    abs(features['brightness'] - f['brightness']) +
                    abs(features['warmth'] - f['warmth']) * 0.1
                    for f in hole_features
                )
            else:
                hole_dist = float('inf')
            
            # Классифицируем по ближайшему примеру
            if peg_dist < hole_dist or (not hole_features and features['brightness'] >= brightness_threshold):
                pegs.append([row, col])
            else:
                holes.append([row, col])
    
    return pegs, holes


def recognize_board(img):
    """
    Улучшенное распознавание доски по скриншоту.
    Использует анализ формы, контраста и структуры.
    """
    from PIL import Image, ImageFilter
    
    # Преобразуем в RGB
    img = img.convert('RGB')
    width, height = img.size
    
    # Обнаруживаем область доски (ищем границы)
    board_bounds = detect_board_bounds(img)
    if board_bounds:
        left, top, right, bottom = board_bounds
        # Обрезаем до области доски
        img = img.crop((left, top, right, bottom))
        width, height = img.size
    
    # Размер ячейки
    cell_w = width / 7
    cell_h = height / 7
    
    # Анализируем фон доски (средний цвет вокруг доски)
    # Берём края изображения как фон
    border_pixels = []
    for x in range(0, width, max(1, width // 20)):
        border_pixels.append(img.getpixel((x, 0)))
        border_pixels.append(img.getpixel((x, height - 1)))
    for y in range(0, height, max(1, height // 20)):
        border_pixels.append(img.getpixel((0, y)))
        border_pixels.append(img.getpixel((width - 1, y)))
    
    bg_r = sum(p[0] for p in border_pixels) / len(border_pixels)
    bg_g = sum(p[1] for p in border_pixels) / len(border_pixels)
    bg_b = sum(p[2] for p in border_pixels) / len(border_pixels)
    bg_brightness = (bg_r + bg_g + bg_b) / 3
    
    pegs = []
    holes = []
    cell_data = []
    
    # Обрабатываем все позиции на поле 7x7
    for row in range(7):
        for col in range(7):
            # Координаты центра ячейки
            cx = int((col + 0.5) * cell_w)
            cy = int((row + 0.5) * cell_h)
            
            # Анализируем большую область ячейки (70% вместо 50%)
            radius = int(min(cell_w, cell_h) * 0.35)
            x1, y1 = max(0, cx - radius), max(0, cy - radius)
            x2, y2 = min(width, cx + radius), min(height, cy + radius)
            region = img.crop((x1, y1, x2, y2))
            
            # Анализируем несколько точек в ячейке (центр и края)
            sample_points = [
                (cx, cy),  # Центр
                (cx - radius // 2, cy),  # Лево
                (cx + radius // 2, cy),  # Право
                (cx, cy - radius // 2),  # Верх
                (cx, cy + radius // 2),  # Низ
            ]
            
            pixels_sample = []
            for px, py in sample_points:
                if 0 <= px < width and 0 <= py < height:
                    pixels_sample.append(img.getpixel((px, py)))
            
            if not pixels_sample:
                continue
            
            # Средние значения цвета
            avg_r = sum(p[0] for p in pixels_sample) / len(pixels_sample)
            avg_g = sum(p[1] for p in pixels_sample) / len(pixels_sample)
            avg_b = sum(p[2] for p in pixels_sample) / len(pixels_sample)
            
            # Метрики
            brightness = (avg_r + avg_g + avg_b) / 3
            warmth = avg_r + avg_g * 0.5 - avg_b * 0.5
            max_c = max(avg_r, avg_g, avg_b)
            min_c = min(avg_r, avg_g, avg_b)
            saturation = (max_c - min_c) / max_c if max_c > 0 else 0
            
            # Контраст с фоном
            contrast_with_bg = abs(brightness - bg_brightness)
            
            # Анализ вариации яркости (колышки имеют блики/тени, пустые - более однородные)
            brightness_variance = 0
            if len(pixels_sample) > 1:
                brightnesses = [(p[0] + p[1] + p[2]) / 3 for p in pixels_sample]
                avg_b = sum(brightnesses) / len(brightnesses)
                brightness_variance = sum((b - avg_b) ** 2 for b in brightnesses) / len(brightnesses)
            
            # Анализ формы: проверяем, есть ли круглый объект (колышек)
            # Колышки обычно имеют более высокую яркость в центре (блик)
            center_brightness = (pixels_sample[0][0] + pixels_sample[0][1] + pixels_sample[0][2]) / 3 if pixels_sample else 0
            edges_brightness = 0
            if len(pixels_sample) > 1:
                edge_pixels = pixels_sample[1:]
                edges_brightness = sum((p[0] + p[1] + p[2]) / 3 for p in edge_pixels) / len(edge_pixels)
            
            # Блик в центре (колышек) vs равномерная яркость (пустое)
            center_highlight = center_brightness - edges_brightness if len(pixels_sample) > 1 else 0
            
            cell_data.append({
                'row': row, 'col': col,
                'brightness': brightness,
                'warmth': warmth,
                'saturation': saturation,
                'r': avg_r, 'g': avg_g, 'b': avg_b,
                'contrast_with_bg': contrast_with_bg,
                'brightness_variance': brightness_variance,
                'center_highlight': center_highlight,
                'center_brightness': center_brightness,
            })
    
    if not cell_data:
        return pegs, holes
    
    if not cell_data:
        return pegs, holes
    
    # Комплексная оценка: комбинируем несколько метрик
    # Используем взвешенную оценку для каждой ячейки
    
    # Находим пороговые значения для кластеризации
    brightnesses = [c['brightness'] for c in cell_data]
    contrasts = [c['contrast_with_bg'] for c in cell_data]
    highlights = [c['center_highlight'] for c in cell_data]
    
    min_bright, max_bright = min(brightnesses), max(brightnesses)
    min_contrast, max_contrast = min(contrasts), max(contrasts) if contrasts else (0, 1)
    min_highlight, max_highlight = min(highlights), max(highlights) if highlights else (0, 1)
    
    # Нормализуем метрики (0-1)
    for cell in cell_data:
        cell['brightness_norm'] = (cell['brightness'] - min_bright) / (max_bright - min_bright) if max_bright > min_bright else 0.5
        cell['contrast_norm'] = (cell['contrast_with_bg'] - min_contrast) / (max_contrast - min_contrast) if max_contrast > min_contrast else 0.5
        cell['highlight_norm'] = (cell['center_highlight'] - min_highlight) / (max_highlight - min_highlight) if max_highlight > min_highlight else 0.5
    
    # Вычисляем комбинированную оценку для каждой ячейки
    # Колышки: высокая яркость, хороший контраст с фоном, блик в центре
    for cell in cell_data:
        score = 0.0
        
        # Яркость (40% веса) - колышки светлее фона
        score += cell['brightness_norm'] * 0.4
        
        # Контраст с фоном (30% веса) - колышки контрастнее
        score += cell['contrast_norm'] * 0.3
        
        # Блик в центре (20% веса) - колышки имеют 3D форму
        if cell['center_highlight'] > 0:
            score += min(cell['highlight_norm'], 1.0) * 0.2
        
        # Вариация яркости (10% веса) - колышки неоднородны (блики/тени)
        if cell['brightness_variance'] > 50:
            score += 0.1
        
        cell['score'] = score
    
    # Находим оптимальный порог методом Otsu
    scores = sorted([c['score'] for c in cell_data])
    best_threshold = 0.5
    best_variance = float('inf')
    
    for threshold in [scores[i] for i in range(0, len(scores), max(1, len(scores) // 30))]:
        cluster1 = [c for c in cell_data if c['score'] < threshold]
        cluster2 = [c for c in cell_data if c['score'] >= threshold]
        
        if not cluster1 or not cluster2:
            continue
        
        mean1 = sum(c['score'] for c in cluster1) / len(cluster1)
        mean2 = sum(c['score'] for c in cluster2) / len(cluster2)
        
        var1 = sum((c['score'] - mean1) ** 2 for c in cluster1) / len(cluster1)
        var2 = sum((c['score'] - mean2) ** 2 for c in cluster2) / len(cluster2)
        
        total_variance = var1 * len(cluster1) + var2 * len(cluster2)
        
        if total_variance < best_variance:
            best_variance = total_variance
            best_threshold = threshold
    
    # Классификация ячеек с улучшенной логикой для коричневой доски
    # Колышки: светлые коричневые круглые объекты (яркие, тёплые)
    # Пустые: тёмные круглые отверстия (очень тёмные, низкая яркость)
    
    # Сортируем ячейки по яркости для адаптивного порога
    sorted_by_brightness = sorted(cell_data, key=lambda x: x['brightness'])
    
    # Используем перцентили для определения порогов
    # Самые светлые 60-70% - потенциальные колышки
    # Самые тёмные 10-20% - потенциальные пустые
    light_threshold_idx = int(len(sorted_by_brightness) * 0.3)
    dark_threshold_idx = int(len(sorted_by_brightness) * 0.85)
    
    light_threshold = sorted_by_brightness[light_threshold_idx]['brightness']
    dark_threshold = sorted_by_brightness[dark_threshold_idx]['brightness'] if dark_threshold_idx < len(sorted_by_brightness) else bg_brightness * 0.7
    
    for cell in cell_data:
        is_peg = False
        is_hole = False
        
        # Критерии для колышка (светлый коричневый объект):
        # 1. Яркость выше среднего порога
        # 2. Тёплый цвет (R, G высокие)
        # 3. Контраст с фоном
        # 4. Блик в центре (3D форма)
        
        if cell['brightness'] >= light_threshold:
            # Проверяем тёплый цвет (коричневый/бежевый колышек)
            if cell['r'] > 100 and cell['g'] > 80:
                # Есть контраст с фоном
                if cell['contrast_with_bg'] > 15:
                    # Есть блик в центре (3D форма колышка)
                    if cell['center_highlight'] > -5:  # Может быть небольшой блик
                        is_peg = True
        
        # Дополнительная проверка: очень светлые ячейки с хорошим контрастом
        if cell['brightness'] > bg_brightness * 1.15 and cell['contrast_with_bg'] > 25:
            is_peg = True
        
        # Критерии для пустого места (тёмное отверстие):
        # 1. Очень низкая яркость
        # 2. Темнее фона
        # 3. Низкий контраст с фоном (т.к. это отверстие в фоне)
        
        if cell['brightness'] <= dark_threshold:
            if cell['brightness'] < bg_brightness * 0.75:
                is_hole = True
        
        # Убеждаемся, что не противоречат друг другу
        if is_peg:
            pegs.append([cell['row'], cell['col']])
        elif is_hole:
            holes.append([cell['row'], cell['col']])
        # Иначе - фон, игнорируем
    
    # Валидация: для английской доски должно быть 32 колышка и 1 пустое место
    # Поддерживаем любые начальные позиции (пустое место может быть в любой валидной позиции)
    total_cells = len(pegs) + len(holes)
    expected_cells = 33  # Всего валидных позиций на английской доске
    
    if total_cells != expected_cells:
        # Возможно, распознавание неполное - возвращаем что есть
        # Пользователь может вручную подправить
        pass
    
    return pegs, holes


def detect_board_bounds(img):
    """
    Улучшенное обнаружение границ игровой доски на скриншоте.
    Ищет коричневую деревянную область с круглыми объектами.
    """
    from PIL import Image
    
    width, height = img.size
    
    # Для мобильных скриншотов доска обычно в центральной части
    # Ищем коричневую область (R и G высокие, B низкий)
    
    # Определяем цвет фона UI (обычно тёмный вверху/внизу)
    top_bg = [img.getpixel((x, height // 20)) for x in range(0, width, width // 10)]
    bottom_bg = [img.getpixel((x, height - height // 20)) for x in range(0, width, width // 10)]
    
    ui_bg_brightness = []
    for pixels in [top_bg, bottom_bg]:
        for p in pixels:
            ui_bg_brightness.append((p[0] + p[1] + p[2]) / 3)
    
    ui_bg_avg = sum(ui_bg_brightness) / len(ui_bg_brightness) if ui_bg_brightness else 50
    
    # Ищем коричневую область доски (теплый цвет, средняя яркость)
    row_scores = []
    for y in range(height):
        row_pixels = [img.getpixel((x, y)) for x in range(0, width, max(1, width // 30))]
        if row_pixels:
            # Анализируем цвет - коричневая доска имеет высокие R и G
            avg_r = sum(p[0] for p in row_pixels) / len(row_pixels)
            avg_g = sum(p[1] for p in row_pixels) / len(row_pixels)
            avg_b = sum(p[2] for p in row_pixels) / len(row_pixels)
            brightness = (avg_r + avg_g + avg_b) / 3
            
            # Коричневый = высокие R, G, средний B, средняя яркость
            # Теплота = R + G - B
            warmth = avg_r + avg_g - avg_b
            
            # Счёт для коричневой области (не слишком тёмная, не слишком светлая)
            score = 0
            if 80 < brightness < 200:  # Средняя яркость
                score += 1
            if warmth > 50:  # Тёплый цвет
                score += 1
            if avg_r > avg_b and avg_g > avg_b:  # Коричневый оттенок
                score += 1
            
            # Вариация (на доске есть объекты)
            variance = sum((p[0] - avg_r) ** 2 for p in row_pixels) / len(row_pixels)
            if variance > 200:  # Есть вариация (колышки)
                score += 1
            
            row_scores.append(score)
        else:
            row_scores.append(0)
    
    if not row_scores:
        return None
    
    # Находим область с максимальным счётом
    max_score = max(row_scores)
    threshold = max_score * 0.5
    
    # Находим границы по вертикали
    top = None
    bottom = None
    
    for i, score in enumerate(row_scores):
        if score >= threshold:
            top = max(0, i - 5)
            break
    
    for i in range(len(row_scores) - 1, -1, -1):
        if row_scores[i] >= threshold:
            bottom = min(height, i + 5)
            break
    
    if top is None or bottom is None:
        # Fallback: берём центральные 70% изображения
        top = int(height * 0.15)
        bottom = int(height * 0.85)
    
    # Аналогично по горизонтали
    col_scores = []
    for x in range(width):
        col_pixels = [img.getpixel((x, y)) for y in range(top, bottom, max(1, (bottom - top) // 20))]
        if col_pixels:
            avg_r = sum(p[0] for p in col_pixels) / len(col_pixels)
            avg_g = sum(p[1] for p in col_pixels) / len(col_pixels)
            brightness = (sum(p[0] + p[1] + p[2] for p in col_pixels) / 3) / len(col_pixels)
            warmth = avg_r + avg_g - sum(p[2] for p in col_pixels) / len(col_pixels)
            
            score = 0
            if 80 < brightness < 200:
                score += 1
            if warmth > 50:
                score += 1
            
            col_scores.append(score)
        else:
            col_scores.append(0)
    
    max_col_score = max(col_scores) if col_scores else 0
    col_threshold = max_col_score * 0.5
    
    left = None
    right = None
    
    for i, score in enumerate(col_scores):
        if score >= col_threshold:
            left = max(0, i - 5)
            break
    
    for i in range(len(col_scores) - 1, -1, -1):
        if col_scores[i] >= col_threshold:
            right = min(width, i + 5)
            break
    
    if left is None or right is None:
        # Fallback: центрируем по горизонтали
        board_height = bottom - top
        left = (width - board_height) // 2
        right = left + board_height
        left = max(0, left)
        right = min(width, right)
    
    return (left, top, right, bottom)


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
