"""PPTX → PDF → 슬라이드별 PNG (샘플영상 '이미지화' 단계).

비주얼원고가 붙기 전 회사 PPTX 초안을 이미지로 만들어, 기존 파이프라인
(이미지 → 음성/자막 → mp4)에 그대로 태우기 위한 다리.

변환기 우선순위(Windows):
  1) PowerPoint COM (win32com) — 이 PC에 Office 설치됨. PPTX→PDF 가 가장 정확.
  2) LibreOffice soffice --headless --convert-to pdf — PATH/일반 설치 경로 탐색.
PDF 가 나오면 기존 pdf_tools.render_pages 로 페이지별 PNG + 텍스트를 뽑는다.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from services.vodstudio import pdf_tools


# ── PPTX → PDF ────────────────────────────────────────────────────────
def _pptx_to_pdf_powerpoint(src: str, dst: str) -> bool:
    """PowerPoint COM 으로 PPTX→PDF. 성공 시 True. Office 미설치/실패 시 False."""
    try:
        import pythoncom  # noqa: F401  (pywin32)
        import win32com.client as win32
    except Exception:
        return False
    src = str(Path(src).resolve())
    dst = str(Path(dst).resolve())
    pythoncom.CoInitialize()
    ppt = None
    prs = None
    try:
        ppt = win32.Dispatch("PowerPoint.Application")
        # 일부 버전은 Visible=False 를 거부 → WithWindow=False 로 창 없이 연다.
        prs = ppt.Presentations.Open(src, ReadOnly=True, WithWindow=False)
        prs.SaveAs(dst, 32)  # ppSaveAsPDF = 32
        return os.path.exists(dst)
    except Exception:
        return False
    finally:
        try:
            if prs is not None:
                prs.Close()
        except Exception:
            pass
        try:
            if ppt is not None:
                ppt.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()


def _soffice_path() -> Optional[str]:
    env = (os.environ.get("SOFFICE_BIN") or "").strip()
    if env and shutil.which(env):
        return shutil.which(env)
    for name in ("soffice", "soffice.exe", "soffice.com"):
        found = shutil.which(name)
        if found:
            return found
    for p in (r"C:\Program Files\LibreOffice\program\soffice.exe",
              r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
        if os.path.exists(p):
            return p
    return None


def _pptx_to_pdf_soffice(src: str, dst: str) -> bool:
    soffice = _soffice_path()
    if not soffice:
        return False
    out_dir = str(Path(dst).resolve().parent)
    try:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                        "--outdir", out_dir, str(Path(src).resolve())],
                       check=True, timeout=180,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        return False
    produced = Path(out_dir) / (Path(src).stem + ".pdf")
    if produced.exists():
        if str(produced) != str(Path(dst).resolve()):
            shutil.move(str(produced), dst)
        return os.path.exists(dst)
    return False


def pptx_to_pdf(pptx_path: str, pdf_path: str) -> str:
    """PPTX→PDF. PowerPoint 우선, 실패 시 LibreOffice. 둘 다 없으면 예외."""
    if _pptx_to_pdf_powerpoint(pptx_path, pdf_path):
        return pdf_path
    if _pptx_to_pdf_soffice(pptx_path, pdf_path):
        return pdf_path
    raise RuntimeError(
        "PPTX→PDF 변환기를 찾지 못했습니다. PowerPoint(Office) 또는 LibreOffice 가 필요합니다."
    )


def pptx_to_images(pptx_path: str, out_dir: str, *, dpi: int = 150,
                   prefix: str = "slide") -> List[pdf_tools.PageRender]:
    """PPTX → (PDF) → 슬라이드별 PNG + 텍스트. 기존 pdf_tools.render_pages 재사용."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    pdf_path = str(Path(out_dir) / (Path(pptx_path).stem + ".pdf"))
    pptx_to_pdf(pptx_path, pdf_path)
    return pdf_tools.render_pages(pdf_path, out_dir, dpi=dpi, prefix=prefix)
