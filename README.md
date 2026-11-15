# Water Check: does radar see the water level change in a lake or reservoir?

[![selftest](https://github.com/geoworldlook/water-check/actions/workflows/selftest.yml/badge.svg)](https://github.com/geoworldlook/water-check/actions/workflows/selftest.yml)
[![monitor](https://github.com/geoworldlook/water-check/actions/workflows/monitor.yml/badge.svg)](https://github.com/geoworldlook/water-check/actions/workflows/monitor.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Version](https://img.shields.io/badge/version-1.0.0-green)

Water Check compares the water area seen by the Copernicus Sentinel-1 radar satellites with the water level measured
by gauges on the ground, for 10 lakes and reservoirs in Poland, Finland, Sweden, France and Italy. Radar works through
clouds and at night, so it gives a regular measurement. But radar does not measure the level. It sees the water
surface: smooth water is dark in a radar image. The question is where this is enough to follow the level, and where
it is not.

**[Live panel](https://geoworldlook.github.io/water-check/showcase/watercheck_panel.html)** (updated automatically every day)

**Checked against the ground (test years 2024–2025, rules written before these years were computed):** the radar
water area follows the gauge level on 2 of 7 water bodies where a signal was expected: the two large shallow
reservoirs in Lapland, Lokka and Porttipahta (rank correlation 0.92 and 0.97, level error 20 and 15 cm of a range of
about 1 m). One reservoir is confirmed only partly (Siemianówka) and four are not confirmed. On all 3 control lakes,
where the area should not change, the radar correctly shows an almost constant area.

## Product card

| | |
|---|---|
| **Problem** | Many lakes and reservoirs have no public gauge, and optical satellites are blocked by clouds. Radar is always available, but it is not clear where its water area can stand in for a level measurement. |
| **User** | People who watch water resources and reservoirs (water management, hydropower, drought monitoring) and people who build such services from satellite data. |
| **Solution** | A small pipeline that runs every day without a person: gauge levels + new Sentinel-1 scenes → water area inside a fixed water zone → scores → public panel and map points. Only a small window of each scene is read from the cloud. The state is a few small files in this repository, so the run needs only GitHub Actions. |
| **Evidence** | 5,691 radar scenes since 2022, gauges from five national networks. Test years 2024–2025: 2 of 7 water bodies confirmed, 1 partly, 4 not confirmed; 3 of 3 control lakes stable. The rules were registered before the test years were computed (protocol W1). |
| **Status** | Runs every day without manual work. Self-assessed technology readiness: TRL 4 (validated on real data at 10 sites; not yet tested with users). |
| **Limits** | Works where the shores are flat and the water area really changes (large shallow reservoirs). No result in the ice season. Wind brightens the water. Reeds look like land. Small water bodies and steep or forested shores give a weak signal. A straight line from area to level fails when later years go outside the calibrated range. |
| **Next** | A better area-to-level curve (shape of the shore from a terrain model); more shallow reservoirs; gauges for Switzerland and Norway; own radar processing as a backup source. |

## Results

Test years 2024–2025. Rank correlation: Spearman, median over satellite tracks. Level error: RMSE of the level
estimated from the radar area with a line fitted on 2022–2023. Level range: 5th to 95th percentile on scene days.

| Water body | Country | Expected | Scenes | Rank corr. | Level error | Level range | Error / range | Verdict |
|---|---|---|---|---|---|---|---|---|
| Lokka | FI | high | 96 | 0.92 | 20 cm | 111 cm | 18% | confirmed |
| Porttipahta | FI | high | 131 | 0.97 | 15 cm | 102 cm | 15% | confirmed |
| Zbiornik Siemianówka | PL | medium | 123 | 0.96 | 104 cm | 193 cm | 54% | partly |
| Vombsjön | SE | high | 205 | 0.51 | 52 cm | 195 cm | 27% | not confirmed |
| Ringsjön | SE | medium | 197 | 0.65 | 26 cm | 85 cm | 31% | not confirmed |
| Retenue de la Haute-Vilaine | FR | medium | 94 | 0.49 | 133 cm | 418 cm | 32% | not confirmed |
| Lago d'Idro | IT | medium | 50 | 0.50 | 44 cm | 109 cm | 40% | not confirmed |

Control lakes (the area should stay constant): Jezioro Gopło (area variation 3.1%), Hjälmaren (0.3%),
Lac du Bourget (0.4%). All three are stable (rule: at most 5%).

All numbers and charts for every water body are in the
[panel](https://geoworldlook.github.io/water-check/showcase/watercheck_panel.html) and in
[`docs/showcase/watercheck_data.json`](docs/showcase/watercheck_data.json).

### Negative and inconclusive results

- **Four of seven water bodies are not confirmed.** Vombsjön was expected to give a strong signal (level range of
  2 m), but its shores are too steep for a 20 m grid: the area changes little.
- **Siemianówka is confirmed only partly.** The radar area follows the level very well (0.96), but the level
  estimated from the area is wrong by about 1 m. In 2022–2023 the level moved little, and in 2024–2025 it moved much
  more. The fitted line does not hold outside the range it was fitted on.
- **Live year 2026 is weaker in Lapland** (rank correlation 0.47 and 0.51). It is reported as measured; one season
  is not enough to say why.
- **Jezioro Łebsko was removed after the run.** Its rectangle also covered the Baltic Sea (water zone 134 km² for a
  71 km² lake). The removal is based on the zone area, not on its result (it had the verdict "stable").
- **Polish gauges have no 2026 archive yet,** so there is no live result for Poland. Lago d'Idro has gauge data only
  to the end of 2024.
- **The simplest method failed** in a first trial (one fixed threshold on the whole rectangle, rank correlation about 0.2)
  and was replaced before the protocol was written.

## Method

1. **Scenes.** All Sentinel-1 RTC scenes (VH band, terrain-corrected) over the water body in its ice-free months,
   from a STAC catalogue. Only the window of the water body is read, onto a fixed UTM grid (10, 20 or 40 m).
2. **Water zone.** From up to 60 scenes of 2022–2023: pixels that are dark in at least 10% of the scenes
   (below −22 dB), the three largest connected areas, plus a 160 m shore belt. Fixed once.
3. **Water in a scene.** An Otsu threshold splits the zone into dark (water) and bright (land) pixels.
   A scene is dropped when it covers less than 98% of the grid or when water and land differ by less than 6 dB (wind).
4. **Area to level.** For each satellite track, a line `level = a + b · area`, fitted on 2022–2023 only.
5. **Scores.** Rank correlation, level error and level range on the test years 2024–2025; area variation for
   control lakes.
6. **Protocol.** [W1](docs/evidence/W1_protokol_powierzchnia_poziom.md) (in Polish) fixes the periods, the scores
   and the decision rules. It was committed before the test years were computed; its SHA-256 is checked in CI.
   Results and deviations: [W1 results](docs/evidence/W1_wyniki.md).

## Code

| Path | Content |
|---|---|
| [`watercheck/`](watercheck/) | package: `sources/` (Sentinel-1, five gauge networks), `core.py` (method and scores), `pipeline.py`, `publish.py`, `selftest.py` |
| [`watercheck/waterbodies.csv`](watercheck/waterbodies.csv) | registry: rectangle, grid, season, gauge and expected class of each water body |
| [`data/`](data/) | pipeline state: gauge levels, one row per radar scene, water zones |
| [`docs/showcase/`](docs/showcase/) | published result: panel, data, map points, run status |
| [`docs/`](docs/) | documentation in Polish: status and plan, architecture, how to run, step-by-step guide, protocol and results |
| [`.github/workflows/`](.github/workflows/) | `monitor.yml` (the daily run), `selftest.yml` (linter, offline test, container build) |

## How to run

```bash
pip install -e .
```

```bash
python -m watercheck selftest
```

```bash
python -m watercheck run
```

`selftest` needs no network (about a minute). `run` is incremental: it computes only scenes that are not yet in
`data/scenes/`. Other commands: `backfill` (rebuild everything since 2022), `render`, `publish`, `settings`.
With Docker: `docker build -t water-check .` and
`docker run --rm -v "$PWD:/work" -e WATERCHECK_ROOT=/work water-check run`.
A conda environment file is included (`environment.yml`).

## Data and attribution

- **Radar:** contains modified Copernicus Sentinel data (Sentinel-1, 2022–2026). Radiometrically terrain-corrected
  scenes (RTC) are read from the Microsoft Planetary Computer.
- **Gauge levels:**
  - Poland: Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy (IMGW-PIB), public data;
    the data were processed.
  - Finland: Finnish Environment Institute (SYKE), open hydrological data.
  - Sweden: Swedish Meteorological and Hydrological Institute (SMHI), open data.
  - France: Hub'Eau, hydrométrie (Eaufrance).
  - Italy: ARPA Lombardia, open data of Regione Lombardia.
- **Map in the panel:** © OpenStreetMap contributors; Leaflet 1.9.4 (BSD-2-Clause, style sheet embedded).

The files in `data/` are derived tables (daily levels, one row per scene), not copies of the source data.

## How it is built

I build this project with help from Claude, an AI assistant made by Anthropic. Claude helps with code, analysis runs
and documentation. I set the goals and the methods, review the results and make the decisions. Every result is
checked against ground measurements, as described above.

## License

Code: [MIT](LICENSE). Data remain under their providers' licences (above). Documentation in [`docs/`](docs/) is in
Polish.
