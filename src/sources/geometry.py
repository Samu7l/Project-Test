"""R2 / R3: département and commune outlines (GeoJSON), simplified so the app stays light."""
from __future__ import annotations

import json
from pathlib import Path

DEPARTEMENTS_URL = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
)
COMMUNES_URL = "https://geo.api.gouv.fr/departements/{dep}/communes?format=geojson&geometry=contour"

TOLERANCE = 0.0005  # degrees (~40-50 m): enough detail for a département-wide commune map
DECIMALS = 4        # ~10 m


def _point_line_distance(p: list[float], a: list[float], b: list[float]) -> float:
    """Distance from point p to segment a-b (planar, in degrees)."""
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def simplify_line(points: list[list[float]], tol: float) -> list[list[float]]:
    """Douglas-Peucker: keep only the points that move the line by more than `tol`."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        dist, k = max((_point_line_distance(points[m], points[i], points[j]), m) for m in range(i + 1, j))
        if dist > tol:
            keep[k] = True
            stack += [(i, k), (k, j)]
    return [p for p, kept in zip(points, keep) if kept]


def simplify_ring(ring: list[list[float]], tol: float = TOLERANCE) -> list[list[float]]:
    """Simplify a closed polygon ring, round coordinates, and keep at least a triangle."""
    out = [[round(x, DECIMALS), round(y, DECIMALS)] for x, y in simplify_line(ring, tol)]
    if len(out) < 4:  # too small after simplification: keep the original (rounded) ring
        out = [[round(x, DECIMALS), round(y, DECIMALS)] for x, y in ring]
    return out


def simplify_geometry(geom: dict, tol: float = TOLERANCE) -> dict:
    """Simplify a Polygon or MultiPolygon GeoJSON geometry."""
    if geom["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [simplify_ring(r, tol) for r in geom["coordinates"]]}
    if geom["type"] == "MultiPolygon":
        return {"type": "MultiPolygon",
                "coordinates": [[simplify_ring(r, tol) for r in poly] for poly in geom["coordinates"]]}
    raise ValueError(f"unexpected geometry type {geom['type']}")


def simplify_communes(raw: dict) -> dict:
    """Commune FeatureCollection with simplified outlines and only the `code` and `nom` properties."""
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature",
         "properties": {"code": f["properties"]["code"], "nom": f["properties"]["nom"]},
         "geometry": simplify_geometry(f["geometry"])}
        for f in raw["features"] if f.get("geometry")
    ]}


def read_geojson(path: Path) -> dict:
    """Load a GeoJSON file."""
    return json.loads(path.read_text())


def write_geojson(data: dict, path: Path) -> None:
    """Write compact GeoJSON (no spaces)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
