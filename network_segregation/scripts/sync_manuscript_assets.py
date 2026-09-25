"""Copy figures and tables from outputs/ into manuscript/ (the manuscript never reads outputs/ directly)."""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ["figures", "tables"]:
    dst = ROOT / "manuscript" / sub
    dst.mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "outputs" / sub).glob("*"):
        if f.suffix in {".pdf", ".tex"}:
            shutil.copy2(f, dst / f.name)
print("synced")
