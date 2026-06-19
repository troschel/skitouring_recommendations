"""
Read route geometries from GeoPackage files by fid.
Converts LV95 (EPSG:2056) coordinates to WGS84 [lon, lat].
"""

import sqlite3
import struct
import os

_DIR = os.path.dirname(__file__)
_SKI_GPKG  = os.path.join(_DIR, "data", "ski_routes_2056.gpkg")
_SNOW_GPKG = os.path.join(_DIR, "data", "schneeschuh_2056.gpkg")


def lv95_to_wgs84(e: float, n: float) -> list[float]:
    y = (e - 2_600_000) / 1_000_000
    x = (n - 1_200_000) / 1_000_000
    lon = (2.6779094 + 4.728982*y + 0.791484*y*x + 0.1306*y*x**2 - 0.0436*y**3) * 100/36
    lat = (16.9023892 + 3.238272*x - 0.270978*y**2 - 0.002528*x**2 - 0.0447*y**2*x - 0.0140*x**3) * 100/36
    return [round(lon, 5), round(lat, 5)]


def _parse_wkb(blob: bytes, step: int = 4) -> list[list[float]]:
    """Parse GeoPackage WKB MultiLineString/LineString (2D or 3D) → [[lon,lat], ...]"""
    flags    = blob[3]
    env_type = (flags >> 1) & 0x07
    wkb_off  = 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[env_type]

    off      = wkb_off + 1                                     # skip byte order
    wkb_type = struct.unpack_from("<i", blob, off)[0]; off += 4

    # WKB types ≥ 1000 are 3D (XYZ) — 3 doubles per point instead of 2
    is_3d   = wkb_type >= 1000
    base    = wkb_type - 1000 if is_3d else wkb_type
    n_dim   = 3 if is_3d else 2

    coords: list[list[float]] = []

    def read_linestring(off):
        n_pts = struct.unpack_from("<i", blob, off)[0]; off += 4
        pts   = struct.unpack_from(f"<{n_pts * n_dim}d", blob, off)
        for i in range(0, n_pts, step):
            coords.append(lv95_to_wgs84(pts[i * n_dim], pts[i * n_dim + 1]))
        return off + n_pts * n_dim * 8

    if base == 5:  # MultiLineString
        n_ls = struct.unpack_from("<i", blob, off)[0]; off += 4
        for _ in range(n_ls):
            off += 5  # byte order + type
            off = read_linestring(off)
    elif base == 2:  # LineString
        read_linestring(off)

    return coords


def get_ski_geometries(fids: list[int]) -> dict[int, list[list[float]]]:
    if not fids:
        return {}
    placeholders = ",".join("?" * len(fids))
    con = sqlite3.connect(_SKI_GPKG)
    rows = con.execute(
        f"SELECT fid, geom FROM ski_routes_2056 WHERE fid IN ({placeholders})", fids
    ).fetchall()
    con.close()
    return {fid: _parse_wkb(geom) for fid, geom in rows if geom}


def get_snow_geometries(fids: list[int]) -> dict[int, list[list[float]]]:
    if not fids:
        return {}
    placeholders = ",".join("?" * len(fids))
    con = sqlite3.connect(_SNOW_GPKG)
    rows = con.execute(
        f"SELECT fid, geom FROM Schneeschuhwanderwege WHERE fid IN ({placeholders})", fids
    ).fetchall()
    con.close()
    return {fid: _parse_wkb(geom) for fid, geom in rows if geom}
