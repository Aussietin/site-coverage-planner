import math

import pytest

from site_coverage_planner.optics import Camera, DORI_PX_PER_M


# A 1/2.8" sensor (~5.4 x 3.0 mm), 4 mm lens, 1920x1080 — a common bullet cam.
CAM = Camera(
    focal_length_mm=4.0,
    sensor_width_mm=5.37,
    sensor_height_mm=3.02,
    h_resolution_px=1920,
    v_resolution_px=1080,
)


def test_fov_reasonable():
    h, v = CAM.fov_deg()
    assert 65 < h < 78
    assert 40 < v < 48


def test_px_per_m_falls_with_distance():
    assert CAM.px_per_m(5) > CAM.px_per_m(20)


def test_dori_range_consistent_with_px_per_m():
    for level, threshold in DORI_PX_PER_M.items():
        d = CAM.dori_range_m(level)
        assert CAM.px_per_m(d) == pytest.approx(threshold, rel=1e-6)


def test_dori_ordering():
    r = {lvl: CAM.dori_range_m(lvl) for lvl in DORI_PX_PER_M}
    assert r["detect"] > r["observe"] > r["recognise"] > r["identify"]


def test_unknown_level():
    with pytest.raises(ValueError):
        CAM.dori_range_m("teleport")
