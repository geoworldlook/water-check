"""Metoda v2: szereg powierzchni wygładzony w czasie i krzywa powierzchnia -> poziom (protokół W2).

v1 liczyło każdą scenę osobno i każdemu torowi orbity dopasowywało prostą. Dwie słabości:
  - pojedyncza scena jest zaszumiona (wiatr, plamka radarowa), a literatura pokazuje, że uśrednianie w oknie
    kilkunastu dni wyraźnie poprawia zgodność z pomiarem (np. porównanie Sentinel-1/2 na 29 zbiornikach, Remote Sensing 2021);
  - zależność powierzchni od poziomu to krzywa hipsometryczna zbiornika, zwykle nieliniowa
    (krzywe poziom–powierzchnia: Busker i in. 2019; Water Resources Research 2023, doi:10.1029/2023WR036450).

v2:
  1. normalizacja torów: powierzchnię z każdego toru sprowadzamy do wspólnej skali (średnia i odchylenie toru
     z lat kalibracji), więc sceny z różnych torów można łączyć;
  2. wygładzanie przyczynowe: mediana znormalizowanej powierzchni z ostatnich `window_days` dni (wszystkie tory);
  3. krzywa: wielomian 2. stopnia poziom = f(powierzchnia), a gdy nie jest rosnący w zakresie danych — prosta.
Wszystko korzysta tylko ze scen wcześniejszych lub z dnia sceny (bez zaglądania w przyszłość).
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

import numpy as np
import pandas as pd

MIN_ORBIT = 8
MIN_FIT = 12


def orbit_stats(x: pd.DataFrame) -> Dict[int, Tuple[float, float]]:
    """Średnia i odchylenie powierzchni dla każdego toru (z okresu dopasowania)."""
    out = {}
    for orbit, g in x.groupby("orbit"):
        if len(g) >= MIN_ORBIT and g["area_km2"].std() > 0:
            out[int(orbit)] = (float(g["area_km2"].mean()), float(g["area_km2"].std()))
    return out


def normalise(x: pd.DataFrame, stats: Dict[int, Tuple[float, float]]) -> pd.Series:
    """Powierzchnia w skali wspólnej dla torów (odchylenia standardowe od średniej toru); NaN dla torów bez statystyk."""
    m = x["orbit"].map(lambda o: stats.get(int(o), (np.nan, np.nan))[0])
    s = x["orbit"].map(lambda o: stats.get(int(o), (np.nan, np.nan))[1])
    return (x["area_km2"] - m) / s


def smooth(x: pd.DataFrame, z: pd.Series, window_days: int) -> pd.Series:
    """Mediana znormalizowanej powierzchni ze scen z ostatnich `window_days` dni (łącznie z bieżącą). Przyczynowe."""
    if window_days <= 0:
        return z
    d = pd.DataFrame({"date": pd.to_datetime(x["date"]).values, "z": z.values}, index=x.index).dropna()
    d = d.sort_values("date", kind="stable")
    if d.empty:
        return z
    s = d.set_index("date")["z"].rolling(f"{int(window_days)}D", min_periods=1).median()
    out = pd.Series(np.nan, index=x.index)
    out.loc[d.index] = s.values                  # d.index to etykiety wierszy x w kolejności dat
    return out


def fit_curve(z: np.ndarray, level: np.ndarray, kind: str = "quad") -> Optional[Callable[[np.ndarray], np.ndarray]]:
    """Krzywa poziom = f(z). `quad`: wielomian 2. stopnia, o ile rośnie w zakresie danych; inaczej prosta.
    Poza zakresem danych krzywą przedłużamy prostą o nachyleniu z brzegu zakresu (bez ekstrapolacji paraboli)."""
    ok = np.isfinite(z) & np.isfinite(level)
    z, level = z[ok], level[ok]
    if len(z) < MIN_FIT or np.std(z) == 0:
        return None
    lo, hi = float(z.min()), float(z.max())
    lin = np.polyfit(z, level, 1)
    coef = lin
    if kind == "quad":
        q = np.polyfit(z, level, 2)
        d_lo, d_hi = 2 * q[0] * lo + q[1], 2 * q[0] * hi + q[1]
        if d_lo > 0 and d_hi > 0:
            coef = q
    der = np.polyder(coef)

    def f(v: np.ndarray) -> np.ndarray:
        v = np.asarray(v, dtype=float)
        inside = np.clip(v, lo, hi)
        y = np.polyval(coef, inside)
        y = y + np.where(v < lo, (v - lo) * np.polyval(der, lo), 0.0) + np.where(v > hi, (v - hi) * np.polyval(der, hi), 0.0)
        return y

    return f


def spearman(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    if len(a) < MIN_ORBIT:
        return None
    ra, rb = pd.Series(a).rank().to_numpy(), pd.Series(b).rank().to_numpy()
    if np.std(ra) == 0 or np.std(rb) == 0:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


def evaluate(fit: pd.DataFrame, test: pd.DataFrame, window_days: int, kind: str) -> Dict[str, Optional[float]]:
    """Miary v2 na okresie `test` przy dopasowaniu (statystyki torów i krzywa) na okresie `fit`.
    rho: korelacja rang między wygładzoną powierzchnią a poziomem (wszystkie tory razem);
    rmse_cm: błąd poziomu odtworzonego z krzywej; range_cm: zakres poziomu 5.–95. percentyl w dniach scen;
    cv_area: zmienność wygładzonej powierzchni przeliczona na km² i odniesiona do średniej powierzchni."""
    out: Dict[str, Optional[float]] = {"n": int(len(test)), "rho": None, "rmse_cm": None, "range_cm": None,
                                       "rmse_share": None, "cv_area": None}
    if len(fit) < MIN_FIT or len(test) < MIN_ORBIT:
        return out
    stats = orbit_stats(fit)
    zf = smooth(fit, normalise(fit, stats), window_days)
    zt = smooth(test, normalise(test, stats), window_days)
    ok = zt.notna() & test["level_cm"].notna()
    if ok.sum() < MIN_ORBIT:
        return out
    lvl = test.loc[ok, "level_cm"].to_numpy(float)
    out["n"] = int(ok.sum())
    r = spearman(zt[ok].to_numpy(float), lvl)
    out["rho"] = round(r, 3) if r is not None else None
    rng = float(np.percentile(lvl, 95) - np.percentile(lvl, 5))
    out["range_cm"] = round(rng, 1)
    curve = fit_curve(zf.to_numpy(float), fit["level_cm"].to_numpy(float), kind)
    if curve is not None:
        err = curve(zt[ok].to_numpy(float)) - lvl
        out["rmse_cm"] = round(float(np.sqrt(np.mean(err ** 2))), 1)
        out["rmse_share"] = round(out["rmse_cm"] / rng, 3) if rng > 0 else None
    # zmienność powierzchni: odchylenie wygładzonego z razy typowe odchylenie toru, przez średnią powierzchnię
    if stats:
        sd = float(np.median([s for _, s in stats.values()]))
        mean = float(np.median([m for m, _ in stats.values()]))
        out["cv_area"] = round(float(np.nanstd(zt[ok].to_numpy(float)) * sd / mean), 4) if mean > 0 else None
    return out
