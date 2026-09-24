import math

import pytest

from site_coverage_planner.optics import Camera, DORI_PX_PER_M, viewshed_visible


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


def test_fov_polygon_closed_and_sized():
    poly = CAM.fov_polygon(origin=(100.0, 200.0), heading_deg=90.0, distance_m=20.0, segments=8)
    assert poly[0] == (100.0, 200.0)
    assert poly[-1] == (100.0, 200.0)
    # origin + (segments + 1) arc points + closing origin
    assert len(poly) == 8 + 3
    for x, y in poly:
        assert math.hypot(x - 100.0, y - 200.0) <= 20.0 + 1e-9


def test_fov_polygon_arc_spans_h_fov():
    h_fov, _ = CAM.fov_deg()
    poly = CAM.fov_polygon(origin=(0.0, 0.0), heading_deg=0.0, distance_m=10.0, segments=2)
    first_arc, last_arc = poly[1], poly[-2]
    bearing_first = math.degrees(math.atan2(first_arc[0], first_arc[1]))
    bearing_last = math.degrees(math.atan2(last_arc[0], last_arc[1]))
    assert bearing_last - bearing_first == pytest.approx(h_fov, rel=1e-6)


def test_fov_polygon_rejects_bad_segments():
    with pytest.raises(ValueError):
        CAM.fov_polygon(origin=(0.0, 0.0), heading_deg=0.0, distance_m=10.0, segments=0)


def test_viewshed_flat_terrain_visible():
    profile = [(10.0, 0.0), (20.0, 0.0), (30.0, 0.0)]
    assert viewshed_visible(0.0, 4.0, 0.0, 1.6, 40.0, profile) is True


def test_viewshed_blocked_by_ridge():
    profile = [(20.0, 10.0)]
    assert viewshed_visible(0.0, 4.0, 0.0, 1.6, 40.0, profile) is False


def test_viewshed_ridge_below_sightline():
    profile = [(20.0, 1.0)]
    assert viewshed_visible(0.0, 4.0, 0.0, 1.6, 40.0, profile) is True


def test_viewshed_ignores_samples_outside_range():
    profile = [(0.0, 100.0), (40.0, 100.0), (50.0, 100.0)]
    assert viewshed_visible(0.0, 4.0, 0.0, 1.6, 40.0, profile) is True


def test_viewshed_rejects_nonpositive_distance():
    with pytest.raises(ValueError):
        viewshed_visible(0.0, 4.0, 0.0, 1.6, 0.0, [])
