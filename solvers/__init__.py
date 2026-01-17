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
from .zobrist_dfs import ZobristDFSSolver
from .astar import AStarSolver, IDAStarSolver
from .beam import BeamSolver
from .parallel import ParallelSolver
from .parallel_beam import ParallelBeamSolver
from .bidirectional import BidirectionalSolver
from .hybrid import HybridSolver
from .pattern_astar import PatternAStarSolver
from .governor import GovernorSolver
from .lookup import LookupSolver
from .sequential import SequentialSolver

__all__ = [
    'DFSSolver',
    'ZobristDFSSolver',
    'AStarSolver', 
    'IDAStarSolver',
    'BeamSolver',
    'ParallelSolver',
    'ParallelBeamSolver',
    'BidirectionalSolver',
    'HybridSolver',
    'PatternAStarSolver',
    'GovernorSolver',
    'LookupSolver',
    'SequentialSolver',
]
