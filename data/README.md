# Data in this folder

Small derived files that are the state of the pipeline. Raw files are not stored here.

| File | Content | Source |
|---|---|---|
| `levels/<id>.csv` | daily water level at the gauge (cm, gauge datum) | national gauge networks (below) |
| `scenes/<id>.csv` | one row per Sentinel-1 scene: water area inside the zone, threshold, contrast, flag | Copernicus Sentinel-1 (RTC), read from the Microsoft Planetary Computer |
| `zones/<id>.npz` | water zone and water core on the fixed grid of the water body, built once from 2022-2023 scenes | same |

## Attribution

- **Radar:** contains modified Copernicus Sentinel data (Sentinel-1).
- **Poland:** Instytut Meteorologii i Gospodarki Wodnej - Panstwowy Instytut Badawczy (IMGW-PIB), public data;
  the data were processed.
- **Finland:** Finnish Environment Institute (SYKE), open hydrological data.
- **Sweden:** Swedish Meteorological and Hydrological Institute (SMHI), open data.
- **France:** Hub'Eau, hydrometrie (Eaufrance).
- **Italy:** ARPA Lombardia, open data of Regione Lombardia.

The values in these files are computed by Water Check (`watercheck/sources/`, `watercheck/core.py`), so they are modified data.
