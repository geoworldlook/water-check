"""Sceny Sentinel-1 RTC (radar, pasmo VH, skorygowane o teren) z Microsoft Planetary Computer.

Katalog STAC wskazuje sceny nad akwenem; z każdej czytamy tylko prostokąt akwenu (pliki COG pozwalają pobrać fragment).
Odczyt wymaga krótkotrwałego żetonu SAS, który serwis wydaje bez konta. Wartości przeliczamy na decybele.
Zawiera zmodyfikowane dane Copernicus Sentinel.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import requests

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
TOKEN = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-1-rtc"
COLLECTION = "sentinel-1-rtc"
_tok: Dict[str, object] = {}
_lock = threading.Lock()


@dataclass(frozen=True)
class Grid:
    """Stała siatka akwenu: układ UTM, rozdzielczość i narożnik. Wszystkie sceny czytamy na tę samą siatkę."""
    epsg: int
    west: float
    north: float
    res: float
    width: int
    height: int

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return self.west, self.north - self.height * self.res, self.west + self.width * self.res, self.north

    @property
    def pixel_km2(self) -> float:
        return self.res * self.res / 1e6


def grid_for(bbox: Tuple[float, float, float, float], res: float) -> Grid:
    """Siatka UTM dla prostokąta (min_lon, min_lat, max_lon, max_lat), wyrównana do wielokrotności rozdzielczości."""
    from rasterio.warp import transform_bounds
    lon, lat = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    epsg = (32600 if lat >= 0 else 32700) + int((lon + 180) // 6) + 1
    w, s, e, n = transform_bounds("EPSG:4326", f"EPSG:{epsg}", *bbox)
    west, north = np.floor(w / res) * res, np.ceil(n / res) * res
    return Grid(epsg, float(west), float(north), float(res), int(np.ceil((e - west) / res)), int(np.ceil((north - s) / res)))


def token() -> str:
    with _lock:
        if not _tok or time.time() > float(_tok.get("until", 0)):
            j = requests.get(TOKEN, timeout=60).json()
            _tok["value"] = j["token"]
            _tok["until"] = time.time() + 30 * 60
        return str(_tok["value"])


def search(bbox: Tuple[float, float, float, float], start: dt.date, end: dt.date) -> List[Dict]:
    """Sceny nad akwenem w okresie [start, end]. Zwraca: id, datetime, date, orbit, platform, href (VH)."""
    out, seen = [], set()
    for year in range(start.year, end.year + 1):
        a, b = max(start, dt.date(year, 1, 1)), min(end, dt.date(year, 12, 31))
        body = {"collections": [COLLECTION], "bbox": list(bbox), "limit": 250,
                "datetime": f"{a}T00:00:00Z/{b}T23:59:59Z"}
        url, method = STAC, "POST"
        while url:
            r = (requests.post(url, json=body, timeout=120) if method == "POST" else requests.get(url, timeout=120))
            r.raise_for_status()
            j = r.json()
            for f in j.get("features", []):
                if f["id"] in seen or "vh" not in f["assets"]:
                    continue
                seen.add(f["id"])
                p = f["properties"]
                out.append({"scene": f["id"], "datetime": p["datetime"], "date": p["datetime"][:10],
                            "orbit": int(p.get("sat:relative_orbit", -1)), "platform": p.get("platform", ""),
                            "href": f["assets"]["vh"]["href"]})
            nxt = [link for link in j.get("links", []) if link.get("rel") == "next"]
            if nxt and nxt[0].get("method", "GET").upper() == "POST":
                url, method, body = nxt[0]["href"], "POST", nxt[0].get("body", body)
            elif nxt:
                url, method = nxt[0]["href"], "GET"
            else:
                url = None
    return sorted(out, key=lambda x: x["datetime"])


def read_db(href: str, grid: Grid) -> np.ndarray:
    """Pasmo VH sceny na siatce akwenu, w decybelach (NaN tam, gdzie scena nie ma danych)."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.vrt import WarpedVRT
    from rasterio.windows import from_bounds

    env = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2",
               GDAL_HTTP_TIMEOUT="60")
    with rasterio.Env(**env), rasterio.open(f"{href}?{token()}") as src:
        if src.crs and src.crs.to_epsg() == grid.epsg:
            win = from_bounds(*grid.bounds, transform=src.transform)
            a = src.read(1, window=win, out_shape=(grid.height, grid.width), boundless=True, fill_value=0)
        else:                                               # scena w sąsiedniej strefie UTM: przeliczamy na siatkę akwenu
            with WarpedVRT(src, crs=f"EPSG:{grid.epsg}", transform=from_origin(grid.west, grid.north, grid.res, grid.res),
                           width=grid.width, height=grid.height, resampling=Resampling.bilinear) as vrt:
                a = vrt.read(1)
    a = a.astype("float32")
    db = np.full(a.shape, np.nan, dtype="float32")
    ok = np.isfinite(a) & (a > 0)
    db[ok] = 10.0 * np.log10(a[ok])
    return db


def describe(scene: Dict) -> str:
    return json.dumps({k: scene[k] for k in ("scene", "date", "orbit", "platform")})
