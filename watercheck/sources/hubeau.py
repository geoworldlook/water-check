"""Wodowskazy Hub'Eau (Francja): API hydrométrie, wielkość HIXnJ (najwyższy stan w dobie, mm) przeliczona na cm."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import requests

URL = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab"


def daily(station_id: str, start: dt.date, end: dt.date) -> pd.Series:
    dates, vals = [], []
    for year in range(start.year, end.year + 1):
        a = max(start, dt.date(year, 1, 1))
        b = min(end, dt.date(year, 12, 31))
        url = URL
        params = dict(code_entite=station_id, grandeur_hydro_elab="HIXnJ", date_debut_obs_elab=a.isoformat(),
                      date_fin_obs_elab=b.isoformat(), size=1000, fields="date_obs_elab,resultat_obs_elab")
        while url:
            r = requests.get(url, params=params, timeout=120)
            r.raise_for_status()
            j = r.json()
            for x in j.get("data", []):
                if x.get("resultat_obs_elab") is not None:
                    dates.append(x["date_obs_elab"][:10])
                    vals.append(float(x["resultat_obs_elab"]) / 10.0)
            url, params = j.get("next"), None
    return pd.Series(vals, index=pd.to_datetime(dates)) if dates else pd.Series(dtype=float)
