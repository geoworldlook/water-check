"""Wodowskazy SYKE (Finlandia): otwarte API hydrologiczne (OData), wielkość „Vedenkorkeus” (poziom wody, cm)."""

from __future__ import annotations

import datetime as dt
from urllib.parse import quote

import pandas as pd
import requests

URL = "https://rajapinnat.ymparisto.fi/api/Hydrologiarajapinta/1.1/odata/Vedenkorkeus"


def daily(station_id: str, start: dt.date, end: dt.date) -> pd.Series:
    rows = []
    for year in range(start.year, end.year + 1):
        a = max(start, dt.date(year, 1, 1))
        b = min(end, dt.date(year, 12, 31))
        flt = (f"Paikka_Id eq {int(station_id)} and Aika ge datetime'{a}T00:00:00' "
               f"and Aika le datetime'{b}T23:59:59'")
        url = URL + "?" + quote(f"$filter={flt}&$select=Aika,Arvo&$top=500", safe="=&$'")
        r = requests.get(url, timeout=120, headers={"Accept": "application/json"})
        r.raise_for_status()
        rows += r.json().get("value", [])
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series([float(x["Arvo"]) for x in rows], index=pd.to_datetime([x["Aika"][:10] for x in rows]))
    return s
