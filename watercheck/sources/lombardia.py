"""Wodowskazy ARPA Lombardia (Włochy): otwarte dane regionu (Socrata), zbiór „Livello idrometrico dal 2021”.

Pomiary co 10 minut; średnią dobową liczy serwer (zapytanie SoQL). Wartości poniżej -900 to kod braku danych.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import requests

URL = "https://www.dati.lombardia.it/resource/3e8b-w7ay.json"


def daily(station_id: str, start: dt.date, end: dt.date) -> pd.Series:
    dates, vals = [], []
    for year in range(start.year, end.year + 1):
        a = max(start, dt.date(year, 1, 1))
        b = min(end, dt.date(year, 12, 31)) + dt.timedelta(days=1)
        params = {"$select": "date_trunc_ymd(data) as d, avg(valore) as v", "$group": "d", "$order": "d", "$limit": 1000,
                  "$where": f"idsensore = '{station_id}' AND data >= '{a}T00:00:00' AND data < '{b}T00:00:00' "
                            f"AND valore > -900"}
        r = requests.get(URL, params=params, timeout=180)
        r.raise_for_status()
        for x in r.json():
            if x.get("v") is not None:
                dates.append(x["d"][:10])
                vals.append(float(x["v"]))
    return pd.Series(vals, index=pd.to_datetime(dates)) if dates else pd.Series(dtype=float)
