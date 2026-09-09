"""CCTV optics + DORI pixel-density model.

Sources (see ProjectVault [[QGIS CCTV Coverage Plugin]] steal-list):
- FoV from focal length + sensor size: pinhole model, same as PanoptiCity.
- DORI bands: IEC 62676-4 — 25 / 62 / 125 / 250 px/m for
  Detect / Observe / Recognise / Identify.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# IEC 62676-4 pixel density thresholds (pixels per metre), min at the target.
DORI_PX_PER_M = {
    "detect": 25.0,
    "observe": 62.0,
    "recognise": 125.0,
    "identify": 250.0,
}


@dataclass(frozen=True)
class Camera:
    """A fixed camera. Distances in mm, resolution in px, angles in degrees."""

    focal_length_mm: float
    sensor_width_mm: float
    sensor_height_mm: float
    h_resolution_px: int
    v_resolution_px: int

    def fov_deg(self) -> tuple[float, float]:
        """Horizontal and vertical field of view, in degrees."""
        h = 2.0 * math.degrees(
            math.atan(self.sensor_width_mm / (2.0 * self.focal_length_mm))
        )
        v = 2.0 * math.degrees(
            math.atan(self.sensor_height_mm / (2.0 * self.focal_length_mm))
        )
        return h, v

    def horizontal_extent_m(self, distance_m: float) -> float:
        """Width of the scene captured at ``distance_m`` from the camera."""
        h_fov, _ = self.fov_deg()
        return 2.0 * distance_m * math.tan(math.radians(h_fov / 2.0))

    def px_per_m(self, distance_m: float) -> float:
        """Horizontal pixel density (px/m) on a target at ``distance_m``."""
        extent = self.horizontal_extent_m(distance_m)
        if extent <= 0:
            return float("inf")
        return self.h_resolution_px / extent

    def dori_range_m(self, level: str) -> float:
        """Max distance at which ``level`` (detect/observe/recognise/identify) holds."""
        try:
            threshold = DORI_PX_PER_M[level.lower()]
        except KeyError as exc:  # pragma: no cover - guard
            raise ValueError(f"unknown DORI level: {level!r}") from exc
        h_fov, _ = self.fov_deg()
        # px_per_m(d) = h_res / (2 d tan(hfov/2)); solve for d at threshold.
        return self.h_resolution_px / (
            2.0 * threshold * math.tan(math.radians(h_fov / 2.0))
        )
