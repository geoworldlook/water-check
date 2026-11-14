"""Wodowskazy IMGW-PIB (Polska): archiwum dobowe (pliki zip dla roku hydrologicznego) i bieżący stan z API.

Rok hydrologiczny zaczyna się 1 listopada: listopad i grudzień roku hydrologicznego R należą do roku kalendarzowego R-1.
Archiwum bieżącego roku pojawia się z opóźnieniem; do tego czasu dopisujemy codzienny stan z API.
Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
import zipfile
from typing import Dict, List

import pandas as pd
import requests

BASE = "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_hydrologiczne/dobowe"
API = "https://danepubliczne.imgw.pl/api/data/hydro/"
_CACHE: Dict[str, pd.DataFrame] = {}


def _folder_files(year: int) -> List[str]:
    r = requests.get(f"{BASE}/{year}/", timeout=60)
    if r.status_code != 200:
        return []
    return sorted(set(re.findall(r'href="(codz_[0-9_]+\.zip)"', r.text)))


def parse_text(raw: bytes) -> pd.DataFrame:
    """Tabela (kolumny 0, 3, 5, 6, 9) z pliku archiwum. Układ pliku zmieniał się z roku na rok:
    2022: przecinki i cudzysłowy, cp1250; 2023: średniki, UTF-8 z BOM; 2024: cały wiersz w cudzysłowie; 2025: jak 2022."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1250", errors="replace")
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('"') and line.endswith('"') and '""' in line:
            line = line[1:-1].replace('""', '"')
        lines.append(line)
    if not lines:
        return pd.DataFrame(columns=[0, 3, 5, 6, 9])
    delim = ";" if lines[0].count(";") >= 9 else ","
    rows = [(r[0].strip(), r[3], r[5], r[6], r[9]) for r in csv.reader(lines, delimiter=delim) if len(r) >= 10]
    return pd.DataFrame(rows, columns=[0, 3, 5, 6, 9])


def _read_zip(url: str) -> pd.DataFrame:
    if url not in _CACHE:
        z = zipfile.ZipFile(io.BytesIO(requests.get(url, timeout=300).content))
        _CACHE[url] = parse_text(z.read(z.namelist()[0]))   # kod stacji, rok hydrologiczny, dzień, stan [cm], miesiąc
    return _CACHE[url]


def parse(d: pd.DataFrame, station_id: str) -> pd.Series:
    """Szereg dobowy jednej stacji z tabeli archiwum (kolumny: 0 kod, 3 rok hydrologiczny, 5 dzień, 6 stan, 9 miesiąc)."""
    d = d[d[0].astype(str).str.strip() == str(station_id)]
    if d.empty:
        return pd.Series(dtype=float)
    month = pd.to_numeric(d[9], errors="coerce").astype(int)
    year = pd.to_numeric(d[3], errors="coerce").astype(int) - month.isin([11, 12]).astype(int)
    dates = pd.to_datetime(dict(year=year, month=month, day=pd.to_numeric(d[5], errors="coerce").astype(int)),
                           errors="coerce")
    v = pd.to_numeric(d[6], errors="coerce")
    s = pd.Series(v.values, index=dates.values)
    return s[(s.index.notna()) & (s < 9000)].dropna()


def current(station_id: str) -> pd.Series:
    """Bieżący stan wody z API (jedna wartość z datą pomiaru)."""
    try:
        for x in requests.get(API, timeout=60).json():
            if str(x.get("id_stacji")) == str(station_id) and x.get("stan_wody") and x.get("stan_wody_data_pomiaru"):
                day = pd.Timestamp(x["stan_wody_data_pomiaru"]).normalize()
                return pd.Series([float(x["stan_wody"])], index=[day])
    except Exception:
        pass
    return pd.Series(dtype=float)


def daily(station_id: str, start: dt.date, end: dt.date) -> pd.Series:
    parts = []
    for hy in range(start.year, end.year + 2):               # rok hydrologiczny R obejmuje XI–XII roku R-1
        for name in _folder_files(hy):
            parts.append(parse(_read_zip(f"{BASE}/{hy}/{name}"), station_id))
    parts.append(current(station_id))
    s = pd.concat([p for p in parts if len(p)]) if any(len(p) for p in parts) else pd.Series(dtype=float)
    s = s[~s.index.duplicated()].sort_index()
    return s[(s.index >= pd.Timestamp(start)) & (s.index <= pd.Timestamp(end))]
