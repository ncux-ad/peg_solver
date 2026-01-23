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

from .simple_dfs import SimpleDFSSolver
from .dfs_memo import DFSMemoSolver
from .astar_simple import AStarSimpleSolver
from .beam_simple import BeamSimpleSolver
from .ida_simple import IDASimpleSolver
from .bidirectional_simple import BidirectionalSimpleSolver
from .pattern_astar_simple import PatternAStarSimpleSolver
from .parallel_simple import ParallelSimpleSolver
from .backward_simple import BackwardSimpleSolver
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
from .exhaustive import ExhaustiveSolver
from .brute_force import BruteForceSolver

__all__ = [
    'SimpleDFSSolver',
    'DFSMemoSolver',
    'AStarSimpleSolver',
    'BeamSimpleSolver',
    'IDASimpleSolver',
    'BidirectionalSimpleSolver',
    'PatternAStarSimpleSolver',
    'ParallelSimpleSolver',
    'BackwardSimpleSolver',
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
    'ExhaustiveSolver',
    'BruteForceSolver',
]
