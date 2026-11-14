"""Wodowskazy SMHI (Szwecja): otwarte dane hydrologiczne, parametr 3 „Vattenstånd” (poziom wody, cm), plik CSV."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import requests

URL = "https://opendata-download-hydroobs.smhi.se/api/version/latest/parameter/3/station/{sid}/period/corrected-archive/data.csv"


def parse(text: str) -> pd.Series:
    """Wiersze danych zaczynają się od daty RRRR-MM-DD; pola rozdziela średnik: data; wartość; jakość."""
    dates, vals = [], []
    for line in text.splitlines():
        p = line.split(";")
        if len(p) >= 2 and len(p[0]) == 10 and p[0][4] == "-" and p[0][7] == "-" and p[0][:4].isdigit():
            try:
                vals.append(float(p[1]))
                dates.append(p[0])
            except ValueError:
                continue
    return pd.Series(vals, index=pd.to_datetime(dates)) if dates else pd.Series(dtype=float)


def daily(station_id: str, start: dt.date, end: dt.date) -> pd.Series:
    r = requests.get(URL.format(sid=int(station_id)), timeout=180)
    r.raise_for_status()
    s = parse(r.content.decode("utf-8", "replace"))
    return s[(s.index >= pd.Timestamp(start)) & (s.index <= pd.Timestamp(end))]
