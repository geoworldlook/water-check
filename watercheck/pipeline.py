"""Potok Water Check: poziomy z wodowskazów -> sceny radarowe -> strefa akwenu -> powierzchnia wody -> miary -> publikacja.

Stan potoku to małe pliki w data/ (jeden zestaw na akwen), więc przebieg w GitHub Actions nie potrzebuje dysku
poza repozytorium:
  data/levels/<id>.csv   date, level_cm
  data/scenes/<id>.csv   scene, date, orbit, platform, valid, area_km2, thr_db, contrast_db, core_db, flag
  data/zones/<id>.npz    strefa akwenu i rdzeń wody na stałej siatce (wyznaczone raz z lat kalibracji)
Przebieg jest przyrostowy: scena policzona raz nie jest pobierana ponownie.
"""

from __future__ import annotations

import datetime as dt
import json
import traceback
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from . import config, core, publish, series
from .sources import gauge_daily, s1

REGISTRY = Path(__file__).resolve().parent / "waterbodies.csv"
SCENE_COLS = ["scene", "date", "orbit", "platform", "valid", "area_km2", "thr_db", "contrast_db", "core_db", "flag"]


def load_registry(path: Path | None = None) -> pd.DataFrame:
    d = pd.read_csv(path or REGISTRY, encoding="utf-8")
    return d[d["status"] == "active"].reset_index(drop=True)


class Sources:
    """Dostęp do sieci. Test bez sieci podstawia własny obiekt z tymi samymi metodami."""

    def levels(self, wb: pd.Series, start: dt.date, end: dt.date) -> pd.Series:
        return gauge_daily(wb["gauge_source"], str(wb["gauge_id"]), start, end)

    def grid(self, wb: pd.Series) -> s1.Grid:
        return s1.grid_for((wb["min_lon"], wb["min_lat"], wb["max_lon"], wb["max_lat"]), float(wb["res_m"]))

    def scenes(self, wb: pd.Series, start: dt.date, end: dt.date) -> List[Dict]:
        return s1.search((wb["min_lon"], wb["min_lat"], wb["max_lon"], wb["max_lat"]), start, end)

    def read(self, scene: Dict, grid: s1.Grid) -> np.ndarray:
        return s1.read_db(scene["href"], grid)


# ---------------------------------------------------------------- pliki stanu

def read_levels(P: config.Paths, wid: str) -> pd.Series:
    f = P.levels / f"{wid}.csv"
    if not f.exists():
        return pd.Series(dtype=float)
    d = pd.read_csv(f, parse_dates=["date"])
    return pd.Series(d["level_cm"].values, index=d["date"])


def write_levels(P: config.Paths, wid: str, s: pd.Series) -> None:
    d = pd.DataFrame({"date": s.index.strftime("%Y-%m-%d"), "level_cm": s.round(1).values})
    d.to_csv(P.levels / f"{wid}.csv", index=False, lineterminator="\n")


def read_scenes(P: config.Paths, wid: str) -> pd.DataFrame:
    f = P.scenes / f"{wid}.csv"
    if not f.exists():
        return pd.DataFrame(columns=SCENE_COLS)
    return pd.read_csv(f, parse_dates=["date"])


def write_scenes(P: config.Paths, wid: str, d: pd.DataFrame) -> None:
    d = d.sort_values(["date", "scene"]).copy()
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    d[SCENE_COLS].to_csv(P.scenes / f"{wid}.csv", index=False, lineterminator="\n")


def save_zone(P: config.Paths, wid: str, zone: np.ndarray, corem: np.ndarray, grid: s1.Grid, n: int) -> None:
    np.savez_compressed(P.zones / f"{wid}.npz", zone=np.packbits(zone), core=np.packbits(corem),
                        shape=np.array(zone.shape), grid=np.array([grid.epsg, grid.west, grid.north, grid.res]),
                        scenes=np.array([n]))


def load_zone(P: config.Paths, wid: str):
    f = P.zones / f"{wid}.npz"
    if not f.exists():
        return None
    z = np.load(f)
    shape = tuple(int(v) for v in z["shape"])
    n = shape[0] * shape[1]
    zone = np.unpackbits(z["zone"])[:n].reshape(shape).astype(bool)
    corem = np.unpackbits(z["core"])[:n].reshape(shape).astype(bool)
    return zone, corem, int(z["scenes"][0])


# ---------------------------------------------------------------- jeden akwen

def _in_season(date: str, wb: pd.Series) -> bool:
    return int(wb["season_from"]) <= int(date[5:7]) <= int(wb["season_to"])


def _read_many(src: Sources, scenes: List[Dict], grid: s1.Grid, log: Callable) -> Dict[str, np.ndarray]:
    out: Dict[str, np.ndarray] = {}

    # Odczyt po kolei: jedna scena to ok. 0,5 s; równoległe wątki spowalniały odczyt przez /vsicurl kilkukrotnie.
    for sc in scenes:
        err: Optional[Exception] = None
        for _attempt in range(2):
            try:
                out[sc["scene"]] = src.read(sc, grid)
                err = None
                break
            except Exception as e:
                err = e
        if err is not None:
            log(f"    scena {sc['scene'][:44]}: odczyt nieudany ({type(err).__name__})")
    return out


def process(wb: pd.Series, P: config.Paths, src: Sources, today: dt.date, log: Callable, rebuild: bool = False) -> None:
    """Aktualizuje pliki stanu jednego akwenu: poziomy, strefę (jeśli jej nie ma) i powierzchnię dla nowych scen."""
    wid, start = wb["id"], dt.date.fromisoformat(config.START)
    old = pd.Series(dtype=float) if rebuild else read_levels(P, wid)
    # przy kolejnych przebiegach pobieramy tylko ostatnie 30 dni poziomów (starsze już są w pliku)
    since = max(start, old.index.max().date() - dt.timedelta(days=30)) if len(old) else start
    new = src.levels(wb, since, today)
    lev = pd.concat([new, old]) if len(old) else new
    lev = lev[~lev.index.duplicated(keep="first")].sort_index()
    write_levels(P, wid, lev)

    grid = src.grid(wb)
    table = pd.DataFrame(columns=SCENE_COLS) if rebuild else read_scenes(P, wid)
    done = set(table["scene"])
    found = [s for s in src.scenes(wb, start, today) if _in_season(s["date"], wb)]
    todo = [s for s in found if s["scene"] not in done]
    cache: Dict[str, np.ndarray] = {}
    z = None if rebuild else load_zone(P, wid)
    if z is None:
        cal = [s for s in found if s["date"] <= config.CAL_END]
        step = max(1, int(np.ceil(len(cal) / config.ZONE_MAX_SCENES)))
        cache = _read_many(src, cal[::step], grid, log)
        full = [a for a in cache.values() if np.isfinite(a).mean() >= config.MIN_VALID]
        if len(full) < 5:
            raise RuntimeError(f"za mało scen do wyznaczenia strefy ({len(full)})")
        zone, corem = core.build_zone(np.stack(full), grid.res)
        save_zone(P, wid, zone, corem, grid, len(full))
        log(f"  {wid}: strefa z {len(full)} scen, {zone.sum() * grid.pixel_km2:.1f} km2")
    else:
        zone, corem, _ = z
    rows = []
    for i in range(0, len(todo), 40):                       # partiami, żeby nie trzymać wszystkich scen w pamięci
        part = todo[i:i + 40]
        arrs = {s["scene"]: cache[s["scene"]] for s in part if s["scene"] in cache}
        arrs.update(_read_many(src, [s for s in part if s["scene"] not in arrs], grid, log))
        for s in part:
            if s["scene"] not in arrs:
                continue
            m = core.scene_area(arrs[s["scene"]], zone, corem, grid.pixel_km2)
            rows.append({"scene": s["scene"], "date": s["date"], "orbit": s["orbit"], "platform": s["platform"], **m,
                         "flag": core.flag(m)})
        if len(todo) > 40:
            log(f"    {wid}: {min(i + 40, len(todo))} z {len(todo)} scen")
    if rows:
        add = pd.DataFrame(rows)
        table = add if table.empty else pd.concat([table, add], ignore_index=True)
        table = table.drop_duplicates("scene", keep="last")
    write_scenes(P, wid, table)
    log(f"  {wid}: poziomy {len(lev)} dni, scen w sezonie {len(found)}, nowych {len(rows)}, razem {len(table)}")


# ---------------------------------------------------------------- miary

def evaluate_site(wb: pd.Series, P: config.Paths) -> Dict:
    wid = wb["id"]
    lev, sc = read_levels(P, wid), read_scenes(P, wid)
    z = load_zone(P, wid)
    flags = sc["flag"].value_counts().to_dict() if len(sc) else {}
    ok = sc[sc["flag"] == "ok"].copy()
    ok["level_cm"] = ok["date"].map(lev) if len(ok) else np.nan
    ok["period"] = ok["date"].map(core.period) if len(ok) else ""
    x = ok.dropna(subset=["level_cm", "area_km2"])
    fits = core.calibrate(x[x["period"] == "calibration"])
    metrics = {p: core.evaluate(x[x["period"] == p], fits) for p in ("calibration", "test", "live")}
    x = x.assign(pred_cm=core.predict(x, fits)) if len(x) else x.assign(pred_cm=[])
    # metoda v2 (protokół W2): wygładzanie, wspólna skala torów, krzywa, coroczna rekalibracja
    first = pd.Timestamp(config.CAL_END).year + 1
    if len(x):
        w2 = series.walk_forward(x, config.V2_WINDOW_DAYS, config.V2_CURVE, first)
    else:
        w2 = x.assign(z=[], pred_cm=[])
    live_year = pd.Timestamp(config.TEST_END).year + 1
    yr = pd.to_datetime(w2["date"]).dt.year if len(w2) else pd.Series(dtype=int)
    v2_retest = series.period_scores(w2[(yr >= first) & (yr < live_year)]) if len(w2) else series.period_scores(w2)
    v2_confirm = series.period_scores(w2[yr >= live_year]) if len(w2) else series.period_scores(w2)
    week = lev.resample("W").mean().dropna() if len(lev) else lev
    return {
        "id": wid, "country": wb["country"], "name": wb["name"], "kind": wb["kind"], "expected": wb["expected"],
        "gauge": {"source": wb["gauge_source"], "id": str(wb["gauge_id"]), "name": wb["gauge_name"],
                  "lat": float(wb["gauge_lat"]), "lon": float(wb["gauge_lon"])},
        "lat": round(float(wb["min_lat"] + wb["max_lat"]) / 2, 4), "lon": round(float(wb["min_lon"] + wb["max_lon"]) / 2, 4),
        "season": [int(wb["season_from"]), int(wb["season_to"])], "res_m": float(wb["res_m"]),
        "zone_km2": round(float(z[0].sum()) * float(wb["res_m"]) ** 2 / 1e6, 1) if z else None,
        "zone_scenes": z[2] if z else 0, "scenes": int(len(sc)), "flags": {k: int(v) for k, v in flags.items()},
        "orbits_calibrated": sorted(fits), "metrics": metrics, "verdict": core.verdict(wb["expected"], metrics["test"]),
        "v2": {"retest": v2_retest, "confirm": v2_confirm,
               "verdict_retest": core.verdict(wb["expected"], v2_retest),
               "verdict_confirm": core.verdict(wb["expected"], v2_confirm)},
        "last_scene": sc["date"].max().strftime("%Y-%m-%d") if len(sc) else None,
        "last_level": lev.index.max().strftime("%Y-%m-%d") if len(lev) else None,
        "latest": {"level_cm": round(float(lev.iloc[-1]), 1) if len(lev) else None,
                   "level_date": lev.index.max().strftime("%Y-%m-%d") if len(lev) else None,
                   "area_km2": round(float(ok.sort_values("date")["area_km2"].iloc[-1]), 2) if len(ok) else None,
                   "area_date": ok["date"].max().strftime("%Y-%m-%d") if len(ok) else None},
        "series": {"date": [d.strftime("%Y-%m-%d") for d in x["date"]], "area": [round(float(v), 2) for v in x["area_km2"]],
                   "level": [round(float(v), 1) for v in x["level_cm"]],
                   "pred": [None if pd.isna(v) else round(float(v), 1) for v in x["pred_cm"]],
                   "orbit": [int(v) for v in x["orbit"]], "period": list(x["period"]),
                   "pred_v2": [None if pd.isna(v) else round(float(v), 1) for v in w2["pred_cm"]] if len(w2) else []},
        "level_weekly": {"date": [d.strftime("%Y-%m-%d") for d in week.index], "level": [round(float(v), 1) for v in week]},
    }


def summarise(sites: List[Dict], errors: Dict[str, str], today: dt.date) -> Dict:
    signal = [s for s in sites if s["expected"] != "control"]
    control = [s for s in sites if s["expected"] == "control"]
    count = lambda rows, v: sum(1 for s in rows if s["verdict"] == v)  # noqa: E731

    def tally(rows: List[Dict], key: str) -> Dict[str, int]:
        vals = [s["v2"][key] for s in rows]
        return {v.replace(" ", "_"): vals.count(v) for v in ("confirmed", "partly", "not confirmed", "stable", "unstable",
                                                            "insufficient") if vals.count(v)}

    return {"project": "water-check", "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "run_date": today.isoformat(),
            "rules": {"rho": config.RHO_PASS, "rmse_share": config.RMSE_SHARE_PASS, "control_cv": config.CONTROL_CV_PASS,
                      "calibration": [config.START, config.CAL_END], "test": ["2024-01-01", config.TEST_END]},
            "summary": {"waterbodies": len(sites), "countries": sorted({s["country"] for s in sites}),
                        "scenes": int(sum(s["scenes"] for s in sites)),
                        "signal": {"n": len(signal), "confirmed": count(signal, "confirmed"), "partly": count(signal, "partly"),
                                   "not_confirmed": count(signal, "not confirmed"), "insufficient": count(signal, "insufficient")},
                        "control": {"n": len(control), "stable": count(control, "stable"), "unstable": count(control, "unstable"),
                                    "insufficient": count(control, "insufficient")}},
            "v2": {"window_days": config.V2_WINDOW_DAYS, "curve": config.V2_CURVE,
                   "retest": {"signal": tally(signal, "verdict_retest"), "control": tally(control, "verdict_retest")},
                   "confirm": {"signal": tally(signal, "verdict_confirm"), "control": tally(control, "verdict_confirm")}},
            "errors": errors, "waterbodies": sites}


# ---------------------------------------------------------------- przebieg

def run(root: str | Path | None = None, today: dt.date | None = None, sources: Sources | None = None,
        waterbodies: pd.DataFrame | None = None, only: Optional[List[str]] = None, rebuild: bool = False,
        log: Callable = print) -> int:
    """Jeden przebieg. Zwraca 0 (opublikowano), 2 (bramka jakości zatrzymała publikację) albo 1 (błąd)."""
    P = config.paths(root)
    today = today or dt.datetime.now(dt.timezone.utc).date()
    src = sources or Sources()
    status = {"project": "water-check", "run_date": today.isoformat(),
              "started": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    code = 1
    try:
        reg = waterbodies if waterbodies is not None else load_registry()
        errors: Dict[str, str] = {}
        log(f"Water Check {today}: akwenów {len(reg)}")
        for _, wb in reg.iterrows():
            if only and wb["id"] not in only:
                continue
            try:
                process(wb, P, src, today, log, rebuild)
            except Exception as e:
                errors[wb["id"]] = f"{type(e).__name__}: {e}"
                log(f"  {wb['id']}: BŁĄD: {errors[wb['id']]}")
        sites = [evaluate_site(wb, P) for _, wb in reg.iterrows() if (P.scenes / f"{wb['id']}.csv").exists()]
        status["errors"] = errors
        if len(errors) > 0.4 * len(reg) or not sites:
            log(f"bramka jakości: NIE przeszła: błąd w {len(errors)} z {len(reg)} akwenów (panel bez zmian)")
            status["status"], code = "gate_failed", 2
        else:
            publish.write_all(P, summarise(sites, errors, today))
            status["status"], code = "ok", 0
            log(f"opublikowano: {P.showcase}")
    except Exception as e:
        status["status"], status["error"] = "error", f"{type(e).__name__}: {e}"
        log(traceback.format_exc())
    status["finished"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (P.logs / "last_run.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    return code


def render(root: str | Path | None = None, today: dt.date | None = None, waterbodies: pd.DataFrame | None = None,
           log: Callable = print) -> int:
    """Przelicza miary i panel z plików w data/ (bez sieci)."""
    P = config.paths(root)
    reg = waterbodies if waterbodies is not None else load_registry()
    sites = [evaluate_site(wb, P) for _, wb in reg.iterrows() if (P.scenes / f"{wb['id']}.csv").exists()]
    if not sites:
        log("brak plików w data/: najpierw `python -m watercheck run`")
        return 1
    publish.write_all(P, summarise(sites, {}, today or dt.datetime.now(dt.timezone.utc).date()))
    log(f"panel przeliczony: {P.showcase}")
    return 0
