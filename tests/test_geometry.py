"""Unit tests for outline simplification (src/sources/geometry.py)."""
from src.sources import geometry


def test_collinear_points_are_removed():
    line = [[0, 0], [1, 0.00001], [2, 0], [3, 0]]
    assert geometry.simplify_line(line, tol=0.001) == [[0, 0], [3, 0]]


def test_ring_stays_closed_and_valid():
    square = [[0, 0], [0.5, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    ring = geometry.simplify_ring(square, tol=0.001)
    assert ring[0] == ring[-1] and len(ring) >= 4


def test_tiny_ring_is_kept():
    tiny = [[0, 0], [0.0001, 0], [0.0001, 0.0001], [0, 0]]
    assert len(geometry.simplify_ring(tiny, tol=0.01)) == 4
