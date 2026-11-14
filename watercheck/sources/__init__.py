"""Jeden mały moduł na jedno źródło: s1 (sceny radarowe) oraz wodowskazy: imgw, syke, smhi, hubeau, lombardia.

Każdy moduł wodowskazu ma funkcję daily(station_id, start, end) -> pd.Series (indeks: data, wartość: poziom w cm).
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from . import hubeau, imgw, lombardia, smhi, syke

GAUGES = {"imgw": imgw, "syke": syke, "smhi": smhi, "hubeau": hubeau, "lombardia": lombardia}


def clean(s: pd.Series) -> pd.Series:
    """Kontrola jakości poziomu: odrzuca wartości oddalone od mediany o więcej niż 6 rozstępów ćwiartkowych
    (nie mniej niż 100 cm), np. zera wpisane zamiast braku danych."""
    s = s[~s.index.duplicated()].sort_index().dropna().astype(float)
    if len(s) < 10:
        return s
    med, iqr = s.median(), s.quantile(0.75) - s.quantile(0.25)
    return s[(s - med).abs() <= max(6 * iqr, 100.0)]


def gauge_daily(source: str, station_id: str, start: dt.date, end: dt.date) -> pd.Series:
    """Dobowy poziom wody w cm dla wodowskazu z podanego źródła, po kontroli jakości."""
    s = clean(GAUGES[source].daily(str(station_id), start, end))
    s.index.name = "date"
    return s
