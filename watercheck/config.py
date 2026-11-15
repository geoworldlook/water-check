"""Ustawienia Water Check w jednym miejscu. Wartości metody pochodzą z protokołu W1 (zmiana = nowa wersja protokołu)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

START = "2022-01-01"                 # początek rekonstrukcji (D-097)
CAL_END = "2023-12-31"               # lata kalibracji: strefa akwenu i krzywa powierzchnia -> poziom
TEST_END = "2025-12-31"              # lata testu: 2024-2025; od 2026 przebieg na żywo
WATER_DB = -22.0                     # dB (VH): piksel „bywa wodą”, gdy 10. percentyl w czasie jest poniżej tej wartości
ZONE_BUFFER_M = 160.0                # pas brzegu doliczany do strefy akwenu
ZONE_MAX_SCENES = 60                 # najwyżej tyle scen z lat kalibracji buduje strefę
MIN_CONTRAST_DB = 6.0                # scena odpada, gdy średnia lądu i wody w strefie różnią się o mniej
MIN_VALID = 0.98                     # scena odpada, gdy pokrywa mniej niż 98% siatki akwenu
MIN_ORBIT_SCENES = 8                 # tor orbity liczy się przy co najmniej 8 scenach w okresie
RHO_PASS = 0.7                       # H-W1
RMSE_SHARE_PASS = 0.25               # H-W2: błąd poziomu najwyżej 25% zakresu poziomu
CONTROL_CV_PASS = 0.05               # H-W3: zmienność powierzchni akwenu kontrolnego najwyżej 5%

PROTOCOL = Path("docs") / "evidence" / "W1_protokol_powierzchnia_poziom.md"
PROTOCOL_SHA256 = "3f9bf6c0a53d8d70eeea7616237f2cad99199c58a9dba3f6ed2df45117124640"


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def levels(self) -> Path:
        return self.root / "data" / "levels"

    @property
    def scenes(self) -> Path:
        return self.root / "data" / "scenes"

    @property
    def zones(self) -> Path:
        return self.root / "data" / "zones"

    @property
    def logs(self) -> Path:
        return self.root / "data" / "logs"

    @property
    def showcase(self) -> Path:
        return self.root / "docs" / "showcase"

    def ensure(self) -> "Paths":
        for p in (self.levels, self.scenes, self.zones, self.logs, self.showcase):
            p.mkdir(parents=True, exist_ok=True)
        return self


def paths(root: str | os.PathLike | None = None) -> Paths:
    """Katalog roboczy: argument, zmienna WATERCHECK_ROOT albo katalog repozytorium."""
    return Paths(Path(root or os.environ.get("WATERCHECK_ROOT") or ROOT)).ensure()
