"""
setup.py

Сборка Cython расширений.

ВАЖНО: Перед компиляцией установите системные зависимости:
  Ubuntu/Debian: sudo apt-get install python3-dev build-essential
  Fedora/RHEL: sudo dnf install python3-devel gcc gcc-c++ make
  Arch: sudo pacman -S python base-devel

Использование:
    python setup.py build_ext --inplace
"""

from setuptools import setup, Extension
from Cython.Build import cythonize

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
