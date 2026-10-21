"""R2 / R3: département and commune outlines (GeoJSON), simplified so the app stays light."""
from __future__ import annotations

import json
from pathlib import Path

DEPARTEMENTS_URL = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
)
COMMUNES_URL = "https://geo.api.gouv.fr/departements/{dep}/communes?format=geojson&geometry=contour"
# Mayotte is outside the licence scope and geo.api has no outline for it: same repository as DEPARTEMENTS_URL.
MAYOTTE_URL = ("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements/976-mayotte/"
               "departement-976-mayotte.geojson")

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


def _rings(geom: dict) -> list[list[list[float]]]:
    """All rings (outer and inner) of a Polygon or MultiPolygon."""
    polygons = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [ring for poly in polygons for ring in poly]


def dissolve(features: list[dict], tol: float = TOLERANCE) -> dict:
    """Merge commune polygons into one département outline (MultiPolygon), without a GIS library.

    Two neighbouring communes share their border, so that border appears twice among all the segments.
    Keeping the segments that appear only once leaves the outer boundary; we then chain them into rings.
    Works on the raw (unsimplified) outlines, where shared borders have identical vertices.
    """
    count: dict[frozenset, int] = {}
    for f in features:
        for ring in _rings(f["geometry"]):
            for a, b in zip(ring[:-1], ring[1:]):
                seg = frozenset([(round(a[0], 6), round(a[1], 6)), (round(b[0], 6), round(b[1], 6))])
                if len(seg) == 2:
                    count[seg] = count.get(seg, 0) + 1

    neighbours: dict[tuple, list[tuple]] = {}
    for seg, n in count.items():
        if n == 1:
            a, b = tuple(seg)
            neighbours.setdefault(a, []).append(b)
            neighbours.setdefault(b, []).append(a)

    rings = []
    while neighbours:
        start = next(iter(neighbours))
        ring, point = [start], start
        while True:
            nxt = neighbours[point].pop()
            neighbours[nxt].remove(point)
            for p in (point, nxt):
                if not neighbours[p]:
                    del neighbours[p]
            ring.append(nxt)
            point = nxt
            if point == start or point not in neighbours:
                break
        if len(ring) >= 4 and ring[0] == ring[-1]:
            rings.append(simplify_ring([list(p) for p in ring], tol))

    # Plotly reads a ring wound the "wrong" way as the whole globe minus the shape, so every ring gets the same
    # orientation as the source's outer rings.
    source_sign = _signed_area(features[0]["geometry"]["coordinates"][0] if features[0]["geometry"]["type"] == "Polygon"
                               else features[0]["geometry"]["coordinates"][0][0]) > 0
    rings = [r if (_signed_area(r) > 0) == source_sign else r[::-1] for r in rings]
    return {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}


def _signed_area(ring: list[list[float]]) -> float:
    """Shoelace formula: > 0 for counter-clockwise rings, < 0 for clockwise (planar approximation)."""
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring[:-1], ring[1:])) / 2


def read_geojson(path: Path) -> dict:
    """Load a GeoJSON file."""
    return json.loads(path.read_text())


def write_geojson(data: dict, path: Path) -> None:
    """Write compact GeoJSON (no spaces)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
