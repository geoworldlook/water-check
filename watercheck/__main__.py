"""
Polecenia Water Check:

    python -m watercheck run        [--root DIR] [--date RRRR-MM-DD] [--only ID ...]   przebieg: poziomy, nowe sceny, panel
    python -m watercheck backfill   [--root DIR] [--only ID ...]     rekonstrukcja od 2022 od zera (sieć, około godziny)
    python -m watercheck render     [--root DIR]                     panel z zapisanych plików (bez sieci)
    python -m watercheck publish    [--message TEKST] [--no-push]    commit i push data/ oraz docs/showcase/
    python -m watercheck selftest                                    testy bez sieci (tak samo w CI)
    python -m watercheck settings                                    ustawienia i stan ostatniego przebiegu

`run` jest przyrostowy: liczy tylko sceny, których jeszcze nie ma w data/scenes/. Pierwszy `run` na pustym
katalogu robi to samo co `backfill`. Kody wyjścia: 0 = opublikowano, 2 = bramka jakości, 1 = błąd.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys

from . import __version__, config


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(config.ROOT), *args], capture_output=True, text=True, encoding="utf-8")


def publish(message: str | None, push: bool) -> int:
    """Commit zmian w data/ i docs/showcase/ (autor z ustawień repozytorium) i wypchnięcie na GitHub."""
    _git("add", "data", "docs/showcase")
    if not _git("diff", "--cached", "--name-only").stdout.strip():
        print("publish: brak zmian")
        return 0
    msg = message or f"auto: przebieg tygodniowy {dt.datetime.now(dt.timezone.utc).date()}"
    c = _git("commit", "-m", msg)
    if c.returncode:
        print(c.stdout, c.stderr)
        return 1
    print(f"publish: commit „{msg}”")
    if push:
        p = _git("push")
        print((p.stdout + p.stderr).strip())
        return p.returncode
    return 0


def settings() -> int:
    P = config.paths()
    info = {"version": __version__, "root": str(P.root), "start": config.START, "calibration_end": config.CAL_END,
            "test_end": config.TEST_END, "water_db": config.WATER_DB, "min_contrast_db": config.MIN_CONTRAST_DB,
            "rules": {"rho": config.RHO_PASS, "rmse_share": config.RMSE_SHARE_PASS, "control_cv": config.CONTROL_CV_PASS},
            "protocol": str(config.PROTOCOL), "protocol_sha256": config.PROTOCOL_SHA256}
    last = P.logs / "last_run.json"
    if last.exists():
        info["last_run"] = json.loads(last.read_text(encoding="utf-8"))
    print(json.dumps(info, ensure_ascii=False, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m watercheck", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "backfill", "render"):
        p = sub.add_parser(name)
        p.add_argument("--root")
        p.add_argument("--date")
        p.add_argument("--only", nargs="*")
    p = sub.add_parser("publish")
    p.add_argument("--message")
    p.add_argument("--no-push", action="store_true")
    sub.add_parser("selftest")
    sub.add_parser("settings")
    a = ap.parse_args(argv)

    if a.cmd in ("run", "backfill", "render"):
        from . import pipeline
        day = dt.date.fromisoformat(a.date) if a.date else None
        if a.cmd == "render":
            return pipeline.render(a.root, day)
        return pipeline.run(a.root, day, only=a.only, rebuild=(a.cmd == "backfill"))
    if a.cmd == "publish":
        return publish(a.message, not a.no_push)
    if a.cmd == "selftest":
        from . import selftest
        return selftest.main()
    if a.cmd == "settings":
        return settings()
    return 1


if __name__ == "__main__":
    sys.exit(main())
