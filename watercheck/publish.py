"""Publikacja wyniku do docs/showcase/: panel (jeden plik HTML z danymi w środku), dane JSON, punkty mapy, stan.

Panel działa bez serwera. Leaflet 1.9.4: skrypt z unpkg, arkusz stylów wbudowany (watercheck/assets/).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from . import config

ASSETS = Path(__file__).resolve().parent / "assets"
PANEL_URL = "https://geoworldlook.github.io/water-check/showcase/watercheck_panel.html"
WORDS = {"confirmed": "radar water area follows the gauge level", "partly": "radar water area follows the gauge level only partly",
         "not confirmed": "radar water area does not follow the gauge level", "stable": "control lake: area stays stable, as expected",
         "unstable": "control lake: area changes more than expected", "insufficient": "too few scenes for a verdict"}


def panel_html(result: Dict) -> str:
    tpl = (ASSETS / "panel_template.html").read_text(encoding="utf-8")
    css = (ASSETS / "leaflet-1.9.4.css").read_text(encoding="utf-8") if (ASSETS / "leaflet-1.9.4.css").exists() else ""
    data = json.dumps(result, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return tpl.replace("/*LEAFLET_CSS*/", css).replace("/*DATA*/", data)


def map_points(result: Dict) -> Dict:
    """Punkty dla mapy monitorowania na stronie (GeoJSON; title i description trafiają do dymka)."""
    feats = []
    for w in result["waterbodies"]:
        t = w["metrics"]["test"]
        extra = ""
        if w["expected"] != "control" and t.get("rho") is not None:
            extra = f" Test years 2024–2025: rank correlation {t['rho']}"
            extra += f", level error {t['rmse_cm']} cm of a {t['range_cm']} cm range." if t.get("rmse_cm") is not None else "."
        elif t.get("cv_area") is not None:
            extra = f" Area variation in 2024–2025: {round(100 * t['cv_area'], 1)}%."
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [w["lon"], w["lat"]]},
                      "properties": {"project": "water-check", "id": w["id"], "title": f"Water Check · {w['name']}",
                                     "description": WORDS[w["verdict"]].capitalize() + "." + extra,
                                     "status": w["verdict"], "updated": result["run_date"], "url": PANEL_URL}})
    return {"type": "FeatureCollection", "features": feats}


def status(result: Dict) -> Dict:
    return {k: result[k] for k in ("project", "updated", "run_date", "rules", "summary", "errors")}


def write_all(P: config.Paths, result: Dict) -> None:
    P.showcase.mkdir(parents=True, exist_ok=True)

    def dump(name: str, obj: Dict, indent=None) -> None:
        (P.showcase / name).write_text(json.dumps(obj, ensure_ascii=False, indent=indent), encoding="utf-8")

    dump("watercheck_data.json", result)
    dump("map_points.geojson", map_points(result), indent=1)
    dump("status.json", status(result), indent=1)
    if (ASSETS / "panel_template.html").exists():
        (P.showcase / "watercheck_panel.html").write_text(panel_html(result), encoding="utf-8")
