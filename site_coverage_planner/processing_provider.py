"""Processing provider registration for the Site Coverage Planner group."""

from __future__ import annotations

from qgis.core import QgsProcessingProvider

from .algorithms.fov_dori import CameraFovDoriAlgorithm


class SiteCoveragePlannerProvider(QgsProcessingProvider):
    def id(self) -> str:  # noqa: A003 - QGIS API name
        return "site_coverage_planner"

    def name(self) -> str:
        return "Site Coverage Planner"

    def loadAlgorithms(self) -> None:
        self.addAlgorithm(CameraFovDoriAlgorithm())
