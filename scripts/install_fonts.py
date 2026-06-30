"""assets/fonts/ 의 .ttf 폰트를 현재 사용자 계정에 설치(관리자 권한 불필요).

setup.bat / setup.sh 에서 호출. PPTX 제목/본문 폰트(Black Han Sans, Do Hyeon)가
PC에 있어야 PPTX·PDF 가 의도한 글씨로 렌더된다.

- Windows: %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts 로 복사 + HKCU 폰트 레지스트리 등록
- macOS:   ~/Library/Fonts 로 복사
- Linux:   ~/.local/share/fonts 로 복사 + (가능하면) fc-cache 갱신
재실행해도 안전(이미 있으면 건너뜀). 적용은 보통 다음 앱/오피스 재시작부터.
"""
from __future__ import annotations

import os
import shutil
import struct
import sys
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"


def _font_name(ttf: Path) -> str:
    """TTF 'name' 테이블에서 가족명(nameID 1)/전체명(4)을 읽는다. 실패 시 파일명."""
    try:
        data = ttf.read_bytes()
        num_tables = struct.unpack(">H", data[4:6])[0]
        off = 12
        name_off = 0
        for _ in range(num_tables):
            tag = data[off:off + 4]
            if tag == b"name":
                name_off = struct.unpack(">I", data[off + 8:off + 12])[0]
                break
            off += 16
        if not name_off:
            return ttf.stem
        count = struct.unpack(">H", data[name_off + 2:name_off + 4])[0]
        str_off = name_off + struct.unpack(">H", data[name_off + 4:name_off + 6])[0]
        best = {}
        rec = name_off + 6
        for _ in range(count):
            pid, eid, lid, nid, ln, oo = struct.unpack(">HHHHHH", data[rec:rec + 12])
            rec += 12
            if nid not in (1, 4):
                continue
            raw = data[str_off + oo:str_off + oo + ln]
            try:
                s = raw.decode("utf-16-be") if (pid == 3 or pid == 0) else raw.decode("latin-1")
            except Exception:
                continue
            if s.strip():
                best[nid] = s.strip()
        return best.get(1) or best.get(4) or ttf.stem
    except Exception:
        return ttf.stem


def _install_windows(ttf: Path) -> str:
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
    dest_dir = local / "Microsoft" / "Windows" / "Fonts"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / ttf.name
    if not dest.exists():
        shutil.copy2(ttf, dest)
    try:
        import winreg  # type: ignore
        name = _font_name(ttf) + " (TrueType)"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(dest))
        winreg.CloseKey(key)
        return f"installed (HKCU): {name}"
    except Exception as e:
        return f"copied to user Fonts (registry skip: {e})"


def _install_unix(ttf: Path) -> str:
    if sys.platform == "darwin":
        dest_dir = Path.home() / "Library" / "Fonts"
    else:
        dest_dir = Path.home() / ".local" / "share" / "fonts"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / ttf.name
    if not dest.exists():
        shutil.copy2(ttf, dest)
    return f"copied: {dest}"


def main() -> int:
    if not FONTS_DIR.is_dir():
        print(f"[fonts] no folder: {FONTS_DIR}")
        return 0
    ttfs = sorted(FONTS_DIR.glob("*.ttf")) + sorted(FONTS_DIR.glob("*.otf"))
    if not ttfs:
        print("[fonts] no .ttf/.otf in assets/fonts/ (skip)")
        return 0
    for ttf in ttfs:
        try:
            msg = _install_windows(ttf) if os.name == "nt" else _install_unix(ttf)
            print(f"[fonts] {ttf.name}: {msg}")
        except Exception as e:
            print(f"[fonts] {ttf.name}: FAILED — {e}")
    if os.name != "nt" and shutil.which("fc-cache"):
        os.system("fc-cache -f >/dev/null 2>&1")
    print("[fonts] done (effective after restarting the app / PowerPoint).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
