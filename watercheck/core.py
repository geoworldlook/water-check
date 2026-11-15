"""Metoda Water Check: strefa akwenu, powierzchnia wody w scenie, powierzchnia -> poziom, miary zgodności.

Woda w paśmie VH jest ciemna (gładka tafla odbija sygnał radaru w bok), ląd jest jasny.
1. Strefa akwenu: piksele, które w latach kalibracji bywały ciemne, plus pas brzegu. Wyznaczana raz.
2. Scena: w strefie dzielimy piksele na ciemne i jasne progiem Otsu; ciemne to woda.
3. Wiatr rozjaśnia wodę. Gdy różnica woda–ląd jest mała, scena dostaje flagę i nie wchodzi do miar.
4. Tor orbity zmienia kąt patrzenia, więc powierzchnię przeliczamy na poziom osobno dla każdego toru.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

from . import config


def otsu(values_db: np.ndarray) -> float:
    """Próg Otsu (dB): podział histogramu na dwie grupy o największej różnicy między grupami."""
    h, e = np.histogram(values_db, bins=96, range=(-32.0, -8.0))
    c = (e[:-1] + e[1:]) / 2
    w0 = np.cumsum(h)
    w1 = w0[-1] - w0
    s = np.cumsum(h * c)
    m0 = s / np.maximum(w0, 1)
    m1 = (s[-1] - s) / np.maximum(w1, 1)
    return float(c[int(np.argmax(w0 * w1 * (m0 - m1) ** 2))])


def build_zone(stack_db: np.ndarray, res_m: float) -> Tuple[np.ndarray, np.ndarray]:
    """Strefa akwenu i rdzeń wody ze stosu scen [n, wiersze, kolumny] (dB).
    Strefa: 10. percentyl w czasie poniżej WATER_DB, trzy największe spójne obszary, powiększone o pas brzegu.
    Rdzeń: mediana w czasie poniżej WATER_DB (woda przez większość czasu)."""
    p10 = np.nanpercentile(stack_db, 10, axis=0)
    p50 = np.nanpercentile(stack_db, 50, axis=0)
    ever = p10 < config.WATER_DB
    lab, n = ndi.label(ever)
    if n > 3:
        sizes = ndi.sum(ever, lab, index=np.arange(1, n + 1))
        ever = np.isin(lab, 1 + np.argsort(sizes)[-3:])
    steps = max(1, int(round(config.ZONE_BUFFER_M / res_m)))
    zone = ndi.binary_dilation(ever, iterations=steps)
    core = (p50 < config.WATER_DB) & zone
    return zone, core


def scene_area(db: np.ndarray, zone: np.ndarray, core: np.ndarray, pixel_km2: float) -> Dict[str, float]:
    """Powierzchnia wody w scenie i miary jakości sceny."""
    valid = float(np.isfinite(db).mean())
    v = db[zone]
    v = v[np.isfinite(v)]
    if v.size < 50:
        return {"valid": valid, "area_km2": np.nan, "thr_db": np.nan, "contrast_db": np.nan, "core_db": np.nan}
    thr = otsu(v)
    water, land = v[v < thr], v[v >= thr]
    contrast = float(land.mean() - water.mean()) if water.size and land.size else 0.0
    c = db[core]
    c = c[np.isfinite(c)]
    return {"valid": round(valid, 3), "area_km2": round(float(water.size * pixel_km2), 3), "thr_db": round(thr, 2),
            "contrast_db": round(contrast, 2), "core_db": round(float(np.median(c)), 2) if c.size else np.nan}


def flag(m: Dict[str, float]) -> str:
    """ok / partial (scena nie pokrywa akwenu) / low_contrast (wiatr, lód, deszcz) / no_zone."""
    if not np.isfinite(m.get("area_km2", np.nan)):
        return "no_zone"
    if m["valid"] < config.MIN_VALID:
        return "partial"
    if m["contrast_db"] < config.MIN_CONTRAST_DB:
        return "low_contrast"
    return "ok"


def period(date: pd.Timestamp) -> str:
    """calibration (2022-2023) / test (2024-2025) / live (od 2026)."""
    if date <= pd.Timestamp(config.CAL_END):
        return "calibration"
    return "test" if date <= pd.Timestamp(config.TEST_END) else "live"


def _spearman(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    if len(a) < 3:
        return None
    ra, rb = pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy()
    if np.std(ra) == 0 or np.std(rb) == 0:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


def calibrate(x: pd.DataFrame) -> Dict[int, Tuple[float, float]]:
    """Prosta level = a + b * area dla każdego toru orbity, z lat kalibracji (sceny ok, z poziomem)."""
    fits = {}
    for orbit, g in x.groupby("orbit"):
        if len(g) >= config.MIN_ORBIT_SCENES and g["area_km2"].std() > 0:
            b, a = np.polyfit(g["area_km2"].to_numpy(float), g["level_cm"].to_numpy(float), 1)
            fits[int(orbit)] = (float(a), float(b))
    return fits


def predict(x: pd.DataFrame, fits: Dict[int, Tuple[float, float]]) -> pd.Series:
    """Poziom odtworzony z powierzchni (cm); brak wartości dla torów bez kalibracji."""
    a = x["orbit"].map(lambda o: fits.get(int(o), (np.nan, np.nan))[0])
    b = x["orbit"].map(lambda o: fits.get(int(o), (np.nan, np.nan))[1])
    return a + b * x["area_km2"]


def evaluate(x: pd.DataFrame, fits: Dict[int, Tuple[float, float]]) -> Dict[str, Optional[float]]:
    """Miary dla jednego okresu (sceny ok, w sezonie, z poziomem wodowskazu).
    rho: mediana korelacji Spearmana po torach orbity; rmse_cm: błąd poziomu odtworzonego z powierzchni;
    range_cm: zakres poziomu (5.–95. percentyl) w dniach scen; cv_area: zmienność powierzchni (mediana po torach)."""
    out: Dict[str, Optional[float]] = {"n": int(len(x)), "orbits": 0, "rho": None, "rmse_cm": None, "range_cm": None,
                                       "rmse_share": None, "cv_area": None, "area_min": None, "area_max": None}
    if x.empty:
        return out
    rhos, cvs = [], []
    for _, g in x.groupby("orbit"):
        if len(g) < config.MIN_ORBIT_SCENES:
            continue
        r = _spearman(g["area_km2"].to_numpy(float), g["level_cm"].to_numpy(float))
        if r is not None:
            rhos.append(r)
        if g["area_km2"].mean() > 0:
            cvs.append(float(g["area_km2"].std() / g["area_km2"].mean()))
    out["orbits"] = len(rhos)
    out["rho"] = round(float(np.median(rhos)), 3) if rhos else None
    out["cv_area"] = round(float(np.median(cvs)), 4) if cvs else None
    out["area_min"], out["area_max"] = round(float(x["area_km2"].min()), 2), round(float(x["area_km2"].max()), 2)
    rng = float(x["level_cm"].quantile(0.95) - x["level_cm"].quantile(0.05))
    out["range_cm"] = round(rng, 1)
    err = (predict(x, fits) - x["level_cm"]).dropna()
    if len(err) >= config.MIN_ORBIT_SCENES:
        out["rmse_cm"] = round(float(np.sqrt((err ** 2).mean())), 1)
        out["rmse_share"] = round(out["rmse_cm"] / rng, 3) if rng > 0 else None
    return out


def verdict(expected: str, m: Dict[str, Optional[float]]) -> str:
    """Akweny z oczekiwanym sygnałem: confirmed (H-W1 i H-W2) / partly (jedna z dwóch) / not confirmed.
    Akweny kontrolne: stable / unstable (H-W3). Za mało danych: insufficient."""
    if expected == "control":
        if m.get("cv_area") is None:
            return "insufficient"
        return "stable" if m["cv_area"] <= config.CONTROL_CV_PASS else "unstable"
    if m.get("rho") is None or m.get("rmse_share") is None:
        return "insufficient"
    passed = int(m["rho"] >= config.RHO_PASS) + int(m["rmse_share"] <= config.RMSE_SHARE_PASS)
    return ("not confirmed", "partly", "confirmed")[passed]
