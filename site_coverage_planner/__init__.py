"""Site Coverage Planner — QGIS line-of-sight / coverage planning toolkit.

Module 1 (CCTV) lives in :mod:`site_coverage_planner.optics`, a pure-Python,
QGIS-free module testable without QGIS on PATH. The plugin/Processing
wiring lives in :mod:`site_coverage_planner.plugin` and
:mod:`site_coverage_planner.algorithms`, which import the ``qgis`` package
and so only load lazily, inside :func:`classFactory`, when QGIS itself
loads this directory as a plugin.
"""

__version__ = "0.0.1"


def classFactory(iface):  # noqa: N802 - fixed QGIS plugin entry point name
    """QGIS plugin entry point (called by QGIS, not importable outside it)."""
    from .plugin import SiteCoveragePlannerPlugin

    return SiteCoveragePlannerPlugin(iface)
