"""
P-value Corrections Package

A Python package for statistical p-value corrections including:
- Bonferroni correction
- Benjamini-Hochberg correction

Author: Chris-R030307
Version: 0.1.0
"""

from .correction import (
    bonferroni_correction,
    benjamini_hochberg_correction,
    correction
)

__version__ = "0.1.0"
__author__ = "Chris-R030307"
__email__ = "chris.r030307@example.com"

__all__ = [
    "bonferroni_correction",
    "benjamini_hochberg_correction", 
    "correction"
]
