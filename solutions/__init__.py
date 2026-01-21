"""
solutions - Известные решения и опорные точки.
"""

from .english_solutions import (
    get_english_solution,
    compute_english_solution,
    verify_solution,
    WaypointSolver,
    create_waypoints_from_solution,
    format_solution_moves,
)

__all__ = [
    'get_english_solution',
    'compute_english_solution',
    'verify_solution',
    'WaypointSolver',
    'create_waypoints_from_solution',
    'format_solution_moves',
]
