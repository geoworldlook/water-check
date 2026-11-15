# Published result

Files in this folder are written by the scheduled run (`python -m watercheck run`) and served by GitHub Pages.

| File | Content |
|---|---|
| `watercheck_panel.html` | the public panel (one file, data embedded; also opens from disk) |
| `watercheck_data.json` | the same data for notebooks |
| `map_points.geojson` | one point per water body for the monitoring map on geoworldlook.vercel.app |
| `status.json` | last run and the summary of verdicts |

Live panel: https://geoworldlook.github.io/water-check/showcase/watercheck_panel.html

Do not edit these files by hand: the next run overwrites them.
