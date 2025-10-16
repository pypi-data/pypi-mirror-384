"""
GA4 Reporter - A simple API for running Google Analytics 4 reports
"""

__version__ = "0.1.0"

from .reporter import GA4Reporter, run_report

__all__ = ["GA4Reporter", "run_report"]
