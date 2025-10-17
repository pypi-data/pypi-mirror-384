"""
PyVisual Graph Module

This module provides various graph types for data visualization,
based on an object-oriented architecture with a common base class.
"""

from pyvisual.ui.outputs.graphs.pv_base_graph import PvBaseGraph
from pyvisual.ui.outputs.graphs.pv_line_graph import PvLineGraph


__all__ = [
    'PvBaseGraph',
    'PvLineGraph',

] 