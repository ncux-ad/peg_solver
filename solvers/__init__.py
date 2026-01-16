"""
solvers - Все решатели Peg Solitaire

Экспортирует:
- DFSSolver: поиск в глубину с мемоизацией
- AStarSolver: A* с эвристиками
- IDAStarSolver: IDA* (экономия памяти)
- BeamSolver: Beam Search (быстрый, неполный)
- ParallelSolver: многопоточный DFS
- BidirectionalSolver: двунаправленный поиск
- HybridSolver: комбинирует все стратегии
"""

from .dfs import DFSSolver
from .astar import AStarSolver, IDAStarSolver
from .beam import BeamSolver
from .parallel import ParallelSolver
from .bidirectional import BidirectionalSolver
from .hybrid import HybridSolver

__all__ = [
    'DFSSolver',
    'AStarSolver', 
    'IDAStarSolver',
    'BeamSolver',
    'ParallelSolver',
    'BidirectionalSolver',
    'HybridSolver'
]
