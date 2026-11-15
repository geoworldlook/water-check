"""Test bez sieci i bez kluczy: syntetyczne jezioro, cały potok (rekonstrukcja i przebieg przyrostowy),
testy jednostkowe modułów. To samo uruchamia CI przy każdej zmianie kodu.

    python -m watercheck selftest
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, core, pipeline
from .sources import clean, imgw, s1, smhi

TODAY = dt.date(2026, 11, 14)
GRID = s1.Grid(epsg=32633, west=500000.0, north=5802400.0, res=20.0, width=120, height=120)
REG = pd.DataFrame([
    dict(id="T-SIG", country="PL", name="Test reservoir", kind="reservoir", expected="high", gauge_source="fake",
         gauge_id="1", gauge_name="Fake gauge", gauge_lat=52.0, gauge_lon=15.0, min_lon=15.0, min_lat=52.0, max_lon=15.03,
         max_lat=52.02, res_m=20, season_from=4, season_to=10, status="active"),
    dict(id="T-CTL", country="SE", name="Test control lake", kind="lake", expected="control", gauge_source="fake",
         gauge_id="2", gauge_name="Fake gauge", gauge_lat=58.0, gauge_lon=14.0, min_lon=14.0, min_lat=58.0, max_lon=14.03,
         max_lat=58.02, res_m=20, season_from=4, season_to=10, status="active"),
])


def _level(days: pd.DatetimeIndex) -> np.ndarray:
    """Syntetyczny poziom (cm): sezon i powolne wahania."""
    n = days.to_julian_date().to_numpy()
    return 300 + 70 * np.sin(2 * np.pi * days.dayofyear.to_numpy() / 365.25) + 25 * np.sin(n / 37.0)


class FakeSources(pipeline.Sources):
    """Atrapa źródeł: jezioro w kształcie koła, którego promień rośnie z poziomem (akwen kontrolny ma stały promień)."""

    def __init__(self):
        self.reads = 0

    def levels(self, wb, start, end):
        days = pd.date_range(start, end)
        return pd.Series(_level(days), index=days)

    def grid(self, wb):
        return GRID

    def scenes(self, wb, start, end):
        out = []
        for i, day in enumerate(pd.date_range(start, end, freq="6D")):
            for orbit, shift in ((22, 0), (95, 3)):
                d = day + pd.Timedelta(days=shift)
                if d.date() > end:
                    continue
                out.append({"scene": f"{wb['id']}_{d:%Y%m%d}_{orbit}", "datetime": f"{d:%Y-%m-%d}T05:00:00Z",
                            "date": f"{d:%Y-%m-%d}", "orbit": orbit, "platform": "sentinel-1a", "href": "fake", "i": i})
        return out

    def read(self, scene, grid):
        self.reads += 1
        day = pd.DatetimeIndex([scene["date"]])
        seed = int(hashlib.sha256(scene["scene"].encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        radius_m = 700.0 if scene["scene"].startswith("T-CTL") else 500.0 + 3.0 * (float(_level(day)[0]) - 200.0)
        yy, xx = np.mgrid[0:grid.height, 0:grid.width]
        dist = np.hypot((xx - grid.width / 2) * grid.res, (yy - grid.height / 2) * grid.res)
        water = dist < radius_m
        windy = scene["i"] % 9 == 4
        db = rng.normal(-13.0, 1.5, water.shape).astype("float32")
        db[water] = rng.normal(-16.5 if windy else (-26.0 if scene["orbit"] == 22 else -24.5), 1.5, int(water.sum()))
        if scene["i"] % 11 == 7:
            db[:, : grid.width // 3] = np.nan                    # scena pokrywa tylko część akwenu
        return db


def check(cond: bool, what: str) -> None:
    if not cond:
        raise AssertionError(what)
    print("  ok:", what)


def unit_tests() -> None:
    print("testy jednostkowe")
    rng = np.random.default_rng(1)
    v = np.r_[rng.normal(-26, 1.2, 4000), rng.normal(-13, 1.5, 6000)]
    check(-22 < core.otsu(v) < -17, "próg Otsu rozdziela wodę i ląd")
    check(core.flag({"area_km2": 1.0, "valid": 0.9, "contrast_db": 9.0}) == "partial"
          and core.flag({"area_km2": 1.0, "valid": 1.0, "contrast_db": 3.0}) == "low_contrast"
          and core.flag({"area_km2": 1.0, "valid": 1.0, "contrast_db": 9.0}) == "ok"
          and core.flag({"area_km2": np.nan, "valid": 1.0, "contrast_db": 9.0}) == "no_zone", "flagi scen")
    check([core.period(pd.Timestamp(d)) for d in ("2023-12-31", "2024-01-01", "2025-12-31", "2026-01-01")] ==
          ["calibration", "test", "test", "live"], "okresy: kalibracja, test, na żywo")
    x = pd.DataFrame({"orbit": [1] * 10 + [2] * 10, "area_km2": list(np.arange(10.0)) * 2,
                      "level_cm": list(100 + 5 * np.arange(10.0)) + list(120 + 5 * np.arange(10.0))})
    fits = core.calibrate(x)
    check(abs(fits[1][1] - 5) < 1e-6 and abs(fits[2][0] - 120) < 1e-6, "kalibracja osobno dla każdego toru")
    m = core.evaluate(x, fits)
    check(m["rho"] == 1.0 and m["rmse_cm"] == 0.0 and m["orbits"] == 2, "miary: zgodność doskonała")
    check(core.verdict("high", {"rho": 0.8, "rmse_share": 0.2}) == "confirmed"
          and core.verdict("high", {"rho": 0.8, "rmse_share": 0.4}) == "partly"
          and core.verdict("medium", {"rho": 0.3, "rmse_share": 0.4}) == "not confirmed"
          and core.verdict("control", {"cv_area": 0.02}) == "stable"
          and core.verdict("control", {"cv_area": 0.2}) == "unstable"
          and core.verdict("high", {"rho": None, "rmse_share": None}) == "insufficient", "werdykty według protokołu")
    stack = np.full((12, 60, 60), -13.0, dtype="float32")
    stack[:, 20:40, 20:40] = -26.0
    zone, corem = core.build_zone(stack, 20.0)
    check(corem.sum() == 400 and zone.sum() > 400 and zone[20:40, 20:40].all(), "strefa akwenu z pasem brzegu")
    # IMGW: cztery układy pliku archiwum
    rows = {"2022": ' 152230120,"SIEMIANÓWKA","Zb.","2022","07","01",333,1.0,99.9,"05"\n',
            "2023": "﻿152230120;SIEMIANÓWKA;Zb.;2023;01;02;280;;;11\n",
            "2024": '"152230120,SIEMIANÓWKA,Zb.,""2024"",""02"",""03"",290,,,""12"""\n',
            "2025": '"152230120",SIEMIANÓWKA,Zb.,"2025","03","04",9999,,,"01"\n'}
    got = [imgw.parse(imgw.parse_text(t.encode("utf-8")), "152230120") for t in rows.values()]
    check(str(got[0].index[0].date()) == "2022-05-01" and got[0].iloc[0] == 333, "IMGW 2022: przecinki")
    check(str(got[1].index[0].date()) == "2022-11-02", "IMGW 2023: średniki; listopad należy do poprzedniego roku")
    check(str(got[2].index[0].date()) == "2023-12-03", "IMGW 2024: wiersz w cudzysłowie")
    check(len(got[3]) == 0, "IMGW: 9999 to brak danych")
    s = smhi.parse("Stationsnamn;x\nDatum;Vattenstånd;Kvalitet\n2024-05-01;2180.0;G\n2024-05-02;;G\n2024-05-03;2181.5;G\n")
    check(len(s) == 2 and s.iloc[1] == 2181.5, "SMHI: wiersze danych z pliku CSV")
    c = clean(pd.Series([5400.0] * 20 + [0.0, 5405.0], index=pd.date_range("2024-01-01", periods=22)))
    check(len(c) == 21 and c.min() > 5000, "kontrola jakości poziomu: zero odrzucone")


def repo_checks() -> None:
    print("pliki repozytorium")
    reg = pipeline.load_registry()
    check(len(reg) >= 8 and reg["id"].is_unique, f"rejestr: {len(reg)} akwenów, identyfikatory unikalne")
    check(set(reg["expected"]) <= {"high", "medium", "control"} and set(reg["gauge_source"]) <= set(
        ("imgw", "syke", "smhi", "hubeau", "lombardia")), "rejestr: klasy i źródła wodowskazów")
    check((reg["max_lon"] > reg["min_lon"]).all() and (reg["max_lat"] > reg["min_lat"]).all()
          and reg["res_m"].isin([10, 20, 40]).all(), "rejestr: prostokąty i rozdzielczość")
    sha = hashlib.sha256((config.ROOT / config.PROTOCOL).read_bytes()).hexdigest()
    check(sha == config.PROTOCOL_SHA256, "protokół W1 niezmieniony od zapisania (SHA-256)")


def pipeline_test(work: Path) -> None:
    print("potok na danych syntetycznych:", work)
    quiet = lambda *_: None  # noqa: E731
    src = FakeSources()
    rc = pipeline.run(work, TODAY, sources=src, waterbodies=REG, log=quiet)
    check(rc == 0, "przebieg 1 (rekonstrukcja): kod 0")
    P = config.paths(work)
    for name in ("watercheck_panel.html", "watercheck_data.json", "map_points.geojson", "status.json"):
        check((P.showcase / name).exists(), f"plik {name}")
    data = json.loads((P.showcase / "watercheck_data.json").read_text(encoding="utf-8"))
    by = {w["id"]: w for w in data["waterbodies"]}
    sig, ctl = by["T-SIG"], by["T-CTL"]
    check(sig["flags"].get("low_contrast", 0) > 5 and sig["flags"].get("partial", 0) > 5 and sig["flags"]["ok"] > 100,
          "flagi: wiatr i niepełne sceny odrzucone")
    t = sig["metrics"]["test"]
    check(t["rho"] >= 0.9 and t["rmse_share"] <= 0.25 and t["orbits"] == 2, "akwen z sygnałem: ρ i błąd poziomu w normie")
    check(sig["verdict"] == "confirmed" and ctl["verdict"] == "stable", "werdykty: confirmed i stable")
    check(sig["orbits_calibrated"] == [22, 95] and sig["zone_km2"] > 1.0, "kalibracja dwóch torów, strefa wyznaczona")
    check(sig["metrics"]["live"]["n"] > 10 and sig["latest"]["area_km2"] is not None, "okres na żywo i ostatnie odczyty")
    check(all(4 <= int(d[5:7]) <= 10 for d in sig["series"]["date"]), "tylko sceny z sezonu")
    geo = json.loads((P.showcase / "map_points.geojson").read_text(encoding="utf-8"))
    check(len(geo["features"]) == 2 and "Gauge level" in geo["features"][0]["properties"]["description"], "punkty mapy z odczytami")
    html = (P.showcase / "watercheck_panel.html").read_text(encoding="utf-8")
    check("T-SIG" in html and "/*DATA*/" not in html, "panel zawiera dane")
    # przebieg przyrostowy: tydzień później liczone są tylko nowe sceny
    before = src.reads
    later = TODAY + dt.timedelta(days=7)
    rc = pipeline.run(work, later, sources=src, waterbodies=REG, log=quiet)
    scenes = pipeline.read_scenes(P, "T-SIG")
    check(rc == 0 and src.reads == before, "przebieg 2 poza sezonem: żadna scena nie jest czytana ponownie")
    check(not scenes["scene"].duplicated().any(), "tabela scen bez duplikatów")
    check(pipeline.render(work, later, waterbodies=REG, log=quiet) == 0, "render z zapisanych plików")
    # bramka: błąd we wszystkich akwenach zatrzymuje publikację

    class Broken(FakeSources):
        def levels(self, wb, start, end):
            raise RuntimeError("brak sieci")

    stamp = (P.showcase / "watercheck_data.json").read_bytes()
    rc = pipeline.run(work, later, sources=Broken(), waterbodies=REG, log=quiet)
    check(rc == 2 and (P.showcase / "watercheck_data.json").read_bytes() == stamp, "bramka jakości zatrzymała publikację")


def main() -> int:
    try:
        unit_tests()
        repo_checks()
        with tempfile.TemporaryDirectory(prefix="watercheck_selftest_") as tmp:
            pipeline_test(Path(tmp))
    except AssertionError as e:
        print("SELFTEST: BŁĄD:", e)
        return 1
    print("SELFTEST: OK")
    return 0
