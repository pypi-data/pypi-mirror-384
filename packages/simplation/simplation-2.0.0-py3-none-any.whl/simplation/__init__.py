"""
Simplation - Simulation Data Analysis Tool

A powerful command-line tool for analyzing and visualizing simulation data from CSV files.
"""

__version__ = "1.0.0"
__author__ = "Mohamed Gueni"
__email__ = "mohamedgueni@outlook.com"

from .cli import SimulationDataAnalyzer, main

__all__ = ["SimulationDataAnalyzer", "main"]