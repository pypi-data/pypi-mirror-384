"""
Módulos core del sistema de extracción.
"""
from .patterns import PatternMatcher
from .heuristics import IndexDetector
from .parser import IndexParser
from .normalizer import DataNormalizer
from .mapper import PageMapper

__all__ = [
    "PatternMatcher",
    "IndexDetector",
    "IndexParser",
    "DataNormalizer",
    "PageMapper"
]
