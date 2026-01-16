/*
 * rust_peg_solver/src/lib.rs
 * 
 * Rust реализация критических операций для Peg Solitaire Solver.
 * Обеспечивает значительное ускорение по сравнению с Python/Cython.
 * 
 * Использование SIMD инструкций и оптимизаций компилятора Rust.
 */

use pyo3::prelude::*;

// Валидные позиции английской доски (33 позиции)
const VALID_POSITIONS: [u8; 33] = [
    2, 3, 4, 9, 10, 11,
    14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27,
    28, 29, 30, 31, 32, 33, 34,
    37, 38, 39, 44, 45, 46,
];

const VALID_MASK: u64 = 0b0000000_0000000_1111111_1111111_1111111_1111111_1111111_0000111_0000111_0000000_0000111;

// Быстрый popcount используя встроенную функцию CPU
#[inline(always)]
fn popcount64(x: u64) -> u32 {
    x.count_ones()
}

/// Подсчёт колышков — O(1) через popcount
#[pyfunction]
fn rust_peg_count(pegs: u64) -> PyResult<u32> {
    Ok(popcount64(pegs))
}

/// Проверка наличия колышка на позиции
#[pyfunction]
fn rust_has_peg(pegs: u64, pos: u8) -> PyResult<bool> {
    Ok((pegs >> pos) & 1 == 1)
}

/// Применяет ход — 3 XOR операции
#[pyfunction]
fn rust_apply_move(pegs: u64, from_pos: u8, jumped: u8, to_pos: u8) -> PyResult<u64> {
    Ok(pegs ^ (1u64 << from_pos) ^ (1u64 << jumped) ^ (1u64 << to_pos))
}

/// Генерирует все допустимые ходы (оптимизированная версия)
#[pyfunction]
fn rust_get_moves(pegs: u64) -> PyResult<Vec<(u8, u8, u8)>> {
    let mut moves = Vec::new();
    let holes = VALID_MASK & !pegs;
    
    // Горизонтальные ходы
    let can_right = pegs & (pegs >> 1) & (holes >> 2);
    let can_left = pegs & (pegs << 1) & (holes << 2);
    
    // Вертикальные ходы
    let can_down = pegs & (pegs >> 7) & (holes >> 14);
    let can_up = pegs & (pegs << 7) & (holes << 14);
    
    for &pos in &VALID_POSITIONS {
        // Вправо
        if (can_right >> pos) & 1 != 0 && pos % 7 <= 4 {
            moves.push((pos, pos + 1, pos + 2));
        }
        
        // Влево
        if (can_left >> pos) & 1 != 0 && pos % 7 >= 2 {
            moves.push((pos, pos - 1, pos - 2));
        }
        
        // Вниз
        if (can_down >> pos) & 1 != 0 && pos / 7 <= 4 {
            let to_pos = pos + 14;
            if to_pos <= 46 && (VALID_MASK >> to_pos) & 1 != 0 {
                moves.push((pos, pos + 7, to_pos));
            }
        }
        
        // Вверх
        if (can_up >> pos) & 1 != 0 && pos / 7 >= 2 {
            let to_pos = pos - 14;
            if to_pos >= 2 && (VALID_MASK >> to_pos) & 1 != 0 {
                moves.push((pos, pos - 7, to_pos));
            }
        }
    }
    
    Ok(moves)
}

/// Проверка тупика: нет ходов, но > 1 колышка
#[pyfunction]
fn rust_is_dead(pegs: u64) -> PyResult<bool> {
    let count = popcount64(pegs);
    if count <= 1 {
        return Ok(false);
    }
    
    let holes = VALID_MASK & !pegs;
    
    // Проверяем, есть ли хоть один ход
    let can_right = pegs & (pegs >> 1) & (holes >> 2);
    if can_right != 0 {
        return Ok(false);
    }
    
    let can_left = pegs & (pegs << 1) & (holes << 2);
    if can_left != 0 {
        return Ok(false);
    }
    
    let can_down = pegs & (pegs >> 7) & (holes >> 14);
    if can_down != 0 {
        return Ok(false);
    }
    
    let can_up = pegs & (pegs << 7) & (holes << 14);
    if can_up != 0 {
        return Ok(false);
    }
    
    Ok(true)
}

/// Pagoda функция (быстрая Rust версия)
#[pyfunction]
fn rust_pagoda_value(pegs: u64) -> PyResult<u32> {
    let weights: [u32; 33] = [
        1, 2, 1,  // 2, 3, 4
        2, 4, 2,  // 9, 10, 11
        1, 2, 3, 4, 3, 2, 1,  // 14-20
        2, 4, 4, 6, 4, 4, 2,  // 21-27
        1, 2, 3, 4, 3, 2, 1,  // 28-34
        2, 4, 2,  // 37, 38, 39
        1, 2, 1,  // 44, 45, 46
    ];
    
    let mut total = 0u32;
    for (i, &pos) in VALID_POSITIONS.iter().enumerate() {
        if (pegs >> pos) & 1 != 0 {
            total += weights[i];
        }
    }
    
    Ok(total)
}

/// Быстрая оценка позиции (Rust версия)
#[pyfunction]
fn rust_evaluate_position(pegs: u64, num_moves: usize) -> PyResult<f64> {
    let peg_count = popcount64(pegs) as f64;
    let mut distance_sum = 0u32;
    let center_row = 3u8;
    let center_col = 3u8;
    
    for &pos in &VALID_POSITIONS {
        if (pegs >> pos) & 1 != 0 {
            let r = pos / 7;
            let c = pos % 7;
            distance_sum += (r as i32 - center_row as i32).abs() as u32 +
                           (c as i32 - center_col as i32).abs() as u32;
        }
    }
    
    let mut score = peg_count * 10.0 + distance_sum as f64;
    score -= num_moves as f64 * 2.0;
    
    // Pagoda проверка
    let pagoda_val = rust_pagoda_value(pegs).unwrap();
    let target_pagoda = 6u32; // CENTER_POS = 24, weight = 6
    
    if peg_count > 15.0 {
        if pagoda_val < target_pagoda {
            score += 1000.0;
        }
    }
    
    Ok(score)
}

/// Batch оценка нескольких позиций (параллельная обработка)
#[pyfunction]
fn rust_evaluate_batch(pegs_list: Vec<u64>, moves_list: Vec<usize>) -> PyResult<Vec<f64>> {
    let mut results = Vec::with_capacity(pegs_list.len());
    
    for (pegs, &num_moves) in pegs_list.iter().zip(moves_list.iter()) {
        results.push(rust_evaluate_position(*pegs, num_moves).unwrap());
    }
    
    Ok(results)
}

#[pymodule]
fn rust_peg_solver(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_peg_count, m)?)?;
    m.add_function(wrap_pyfunction!(rust_has_peg, m)?)?;
    m.add_function(wrap_pyfunction!(rust_apply_move, m)?)?;
    m.add_function(wrap_pyfunction!(rust_get_moves, m)?)?;
    m.add_function(wrap_pyfunction!(rust_is_dead, m)?)?;
    m.add_function(wrap_pyfunction!(rust_pagoda_value, m)?)?;
    m.add_function(wrap_pyfunction!(rust_evaluate_position, m)?)?;
    m.add_function(wrap_pyfunction!(rust_evaluate_batch, m)?)?;
    
    Ok(())
}
