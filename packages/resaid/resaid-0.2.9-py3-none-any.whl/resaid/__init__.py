"""
RESAID - Reservoir Engineering Tools

A comprehensive collection of reservoir engineering tools for production forecasting 
and decline curve analysis.

Classes:
    decline_curve: Main DCA class for production analysis and forecasting
    decline_solver: Solver for decline curve parameter optimization
    npv_calc: Net Present Value and IRR calculations
    well_econ: Well economics analysis and cashflow modeling
    DatabaseInterface: Base class for database operations
    ARIESDatabase: Specialized interface for ARIES databases
    PhdWinDatabase: Specialized interface for PhdWin databases
"""

__version__ = "0.2.3"
__author__ = "Greg Easley"
__email__ = "greg@easley.dev"

from .dca import decline_curve, decline_solver
from .econ import npv_calc, well_econ
from .database import DatabaseInterface, ARIESDatabase, PhdWinDatabase

__all__ = [
    'decline_curve', 
    'decline_solver', 
    'npv_calc', 
    'well_econ',
    'DatabaseInterface',
    'ARIESDatabase', 
    'PhdWinDatabase'
]
