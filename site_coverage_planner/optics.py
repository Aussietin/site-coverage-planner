"""CCTV optics + DORI pixel-density model.

Sources (see ProjectVault [[QGIS CCTV Coverage Plugin]] steal-list):
- FoV from focal length + sensor size: pinhole model, same as PanoptiCity.
- DORI bands: IEC 62676-4 — 25 / 62 / 125 / 250 px/m for
  Detect / Observe / Recognise / Identify.
- Viewshed: straight-line-of-sight check against a terrain profile (no DEM
  sampling/raster IO here — that's the PyQGIS layer's job to feed this a
  profile).
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

    def _arc_points(
        self,
        origin: tuple[float, float],
        heading_deg: float,
        radius_m: float,
        segments: int,
    ) -> list[tuple[float, float]]:
        h_fov, _ = self.fov_deg()
        ox, oy = origin
        start = heading_deg - h_fov / 2.0
        step = h_fov / segments
        points = []
        for i in range(segments + 1):
            bearing = math.radians(start + step * i)
            points.append(
                (ox + radius_m * math.sin(bearing), oy + radius_m * math.cos(bearing))
            )
        return points

    def fov_polygon(
        self,
        origin: tuple[float, float],
        heading_deg: float,
        distance_m: float,
        segments: int = 16,
    ) -> list[tuple[float, float]]:
        """FoV footprint as a closed polygon (pie slice) in map coordinates.

        ``heading_deg`` is the camera's look direction as a compass bearing
        (0 = north, clockwise-positive), matching QGIS/GIS convention.
        ``distance_m`` is the radius of the slice, e.g. a DORI range from
        :meth:`dori_range_m`. Returns ``[origin, arc points..., origin]``.
        """
        if segments < 1:
            raise ValueError("segments must be >= 1")
        arc = self._arc_points(origin, heading_deg, distance_m, segments)
        return [origin, *arc, origin]

    def dori_band_polygons(
        self,
        origin: tuple[float, float],
        heading_deg: float,
        segments: int = 16,
    ) -> dict[str, list[tuple[float, float]]]:
        """Closed ring-sector polygon per DORI level, nearest to farthest.

        Levels partition the FoV footprint into non-overlapping zones:
        identify (0..identify range), recognise, observe, detect (outermost).
        Each polygon is ``[*inner arc, *outer arc reversed, inner arc[0]]``,
        or a plain pie slice for the innermost (identify) band.
        """
        if segments < 1:
            raise ValueError("segments must be >= 1")
        order = ("identify", "recognise", "observe", "detect")
        bands: dict[str, list[tuple[float, float]]] = {}
        inner_radius = 0.0
        for level in order:
            outer_radius = self.dori_range_m(level)
            if inner_radius <= 0.0:
                outer_arc = self._arc_points(origin, heading_deg, outer_radius, segments)
                bands[level] = [origin, *outer_arc, origin]
            else:
                inner_arc = self._arc_points(origin, heading_deg, inner_radius, segments)
                outer_arc = self._arc_points(origin, heading_deg, outer_radius, segments)
                bands[level] = [*inner_arc, *reversed(outer_arc), inner_arc[0]]
            inner_radius = outer_radius
        return bands


def viewshed_visible(
    camera_elev_m: float,
    camera_height_m: float,
    target_elev_m: float,
    target_height_m: float,
    target_distance_m: float,
    profile: list[tuple[float, float]] = (),
) -> bool:
    """Straight line-of-sight check between camera and target over terrain.

    ``profile`` is a sequence of ``(distance_from_camera_m, ground_elev_m)``
    samples strictly between camera and target (any order). Returns False if
    any sample's ground elevation rises above the camera-target sightline at
    that distance.
    """
    if target_distance_m <= 0:
        raise ValueError("target_distance_m must be > 0")
    sight_start = camera_elev_m + camera_height_m
    sight_end = target_elev_m + target_height_m
    rise = sight_end - sight_start
    for distance, ground_elev in profile:
        if not (0.0 < distance < target_distance_m):
            continue
        sightline_elev = sight_start + rise * (distance / target_distance_m)
        if ground_elev > sightline_elev:
            return False
    return True
