"""
setup.py

Сборка Cython расширений.

Использование:
    python setup.py build_ext --inplace
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "core.fast_bitboard",
        ["core/fast_bitboard.pyx"],
        extra_compile_args=["-O3", "-march=native"],
    ),
]

setup(
    name="peg_solver",
    version="2.0.0",
    description="High-performance Peg Solitaire Solver",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
        }
    ),
    zip_safe=False,
)
