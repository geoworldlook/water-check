"""Eksperyment W2: wybór okna wygładzania i rodzaju krzywej dla metody v2, tylko na latach kalibracji (2022–2023).

Dopasowanie na jednym roku, ocena na drugim, w obie strony (2022 -> 2023 i 2023 -> 2022); wynik to średnia z obu.
Lata testowe 2024–2025 i rok 2026 NIE są tu czytane.

Uruchomienie:  conda run -n watercheck python notebooks/experiments/W2_wybor_metody.py
Wynik:         docs/evidence/W2_wybor_metody.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from watercheck import config, pipeline, series  # noqa: E402

WINDOWS = (0, 7, 15, 30)
KINDS = ("lin", "quad")


def site_table(P, wid: str) -> pd.DataFrame:
    lev, sc = pipeline.read_levels(P, wid), pipeline.read_scenes(P, wid)
    ok = sc[sc["flag"] == "ok"].copy()
    ok["level_cm"] = ok["date"].map(lev)
    ok = ok.dropna(subset=["level_cm", "area_km2"])
    return ok[ok["date"] <= pd.Timestamp(config.CAL_END)]            # tylko lata kalibracji


def main() -> int:
    P = config.paths(ROOT)
    reg = pipeline.load_registry()
    rows = []
    for w in WINDOWS:
        for kind in KINDS:
            per_site = []
            for _, wb in reg.iterrows():
                x = site_table(P, wb["id"])
                a, b = x[x["date"].dt.year == 2022], x[x["date"].dt.year == 2023]
                folds = [series.evaluate(a, b, w, kind), series.evaluate(b, a, w, kind)]
                rho = [f["rho"] for f in folds if f["rho"] is not None]
                share = [f["rmse_share"] for f in folds if f["rmse_share"] is not None]
                cv = [f["cv_area"] for f in folds if f["cv_area"] is not None]
                per_site.append({"id": wb["id"], "expected": wb["expected"],
                                 "rho": float(np.mean(rho)) if rho else np.nan,
                                 "share": float(np.mean(share)) if share else np.nan,
                                 "cv": float(np.mean(cv)) if cv else np.nan})
            d = pd.DataFrame(per_site)
            sig, ctl = d[d["expected"] != "control"], d[d["expected"] == "control"]
            both = int(((sig["rho"] >= config.RHO_PASS) & (sig["share"] <= config.RMSE_SHARE_PASS)).sum())
            rows.append({"window_days": w, "curve": kind, "signal_sites": len(sig), "pass_both": both,
                         "pass_rho": int((sig["rho"] >= config.RHO_PASS).sum()),
                         "median_rho": round(float(sig["rho"].median()), 3),
                         "median_share": round(float(sig["share"].median()), 3),
                         "control_stable": int((ctl["cv"] <= config.CONTROL_CV_PASS).sum()), "control_sites": len(ctl),
                         "detail": "; ".join(f"{r.id} {r.rho:.2f}/{r.share:.2f}" for r in sig.itertuples())})
            print({k: v for k, v in rows[-1].items() if k != "detail"}, flush=True)
            print("   ", rows[-1]["detail"], flush=True)
    out = pd.DataFrame(rows).sort_values(["pass_both", "pass_rho", "median_rho"], ascending=False)
    out.to_csv(ROOT / "docs" / "evidence" / "W2_wybor_metody.csv", index=False, lineterminator="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
