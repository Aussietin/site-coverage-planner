"""QGIS plugin entry point — thin wiring around ``optics.py``.

No dialogs or menu actions yet; this just registers the Processing
provider so the "Camera FoV + DORI bands" algorithm shows up under
Processing Toolbox → Site Coverage Planner. All the actual FoV/DORI/
viewshed maths lives in :mod:`site_coverage_planner.optics`, which stays
QGIS-free and unit-tested outside this file.
"""

from __future__ import annotations

from qgis.core import QgsApplication


class SiteCoveragePlannerPlugin:
    """Registers the Site Coverage Planner Processing provider with QGIS."""

    def __init__(self, iface) -> None:
        self.iface = iface
        self.provider = None

    def initGui(self) -> None:
        from .processing_provider import SiteCoveragePlannerProvider

        self.provider = SiteCoveragePlannerProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self) -> None:
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
