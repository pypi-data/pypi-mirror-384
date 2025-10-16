"""Bliss-side for Flint ID26 plots"""

try:
    from flint.client.plots import Plot1D
except ImportError:
    Plot1D = object


class AggregatedScansPlot(Plot1D):
    """Plot for scans mean"""
