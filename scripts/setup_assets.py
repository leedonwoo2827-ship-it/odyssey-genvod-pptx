#!/usr/bin/env python3
"""Download the local TTS model (ONNX) from HuggingFace into assets/onnx/.

Cross-platform (stdlib urllib only — no extra deps), used by setup.sh on
Linux/macOS. Windows setup.bat uses scripts/setup_assets.ps1 (equivalent).
Skips files already present; pass --force to redownload. Downloads to a
.part file then renames, so an interrupted run never leaves a half-file.
"""
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONNX = ROOT / "assets" / "onnx"
BASE = "https://huggingface.co/Supertone/supertonic-3/resolve/main/onnx"
FILES = [
    "duration_predictor.onnx", "text_encoder.onnx", "vector_estimator.onnx",
    "vocoder.onnx", "tts.json", "unicode_indexer.json",
]


def main() -> int:
    force = "--force" in sys.argv
    ONNX.mkdir(parents=True, exist_ok=True)
    print(f"Downloading TTS model (Supertone/supertonic-3, ~380MB) -> {ONNX}")
    for f in FILES:
        dest = ONNX / f
        if dest.is_file() and not force:
            print(f"  skip (exists): {f}")
            continue
        tmp = dest.with_name(dest.name + ".part")
        print(f"  downloading: {f} ...")
        try:
            req = urllib.request.Request(f"{BASE}/{f}", headers={"User-Agent": "vodstudio-setup"})
            with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as out:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    out.write(chunk)
            tmp.replace(dest)
        except Exception as e:  # noqa: BLE001
            if tmp.exists():
                tmp.unlink()
            print(f"  [ERROR] {f}: {e}")
            print("  Check your internet connection and run setup again.")
            return 1
    print("TTS model ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
