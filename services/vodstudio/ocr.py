"""슬라이드 이미지 → 텍스트 줄(OCR). 플랫폼별 엔진 자동 선택.

NotebookLM 슬라이드덱 PDF/이미지는 글자가 이미지에 박혀 복사가 안 되므로(긁히지 않음),
OCR로 '얼추' 추출해 회사 양식 PPTX 텍스트로 재배치한다(우리 폰트). 정확도는 100%가
아니므로 PPTX에서 가볍게 손보는 것을 전제로 한다.

엔진 우선순위(자동 감지):
  1) Windows 내장 OCR(winsdk) — Windows + 한국어 OCR 언어팩(추가 설치 0)
  2) Tesseract(pytesseract) — mac/linux/win 공통, 'kor' 데이터 필요
  3) EasyOCR — pip 설치만으로 동작(무겁)
없으면 OcrUnavailable 을 던져 호출부가 '대본 텍스트' 등으로 폴백하게 한다.
"""
from __future__ import annotations

import os
from typing import List


class OcrUnavailable(RuntimeError):
    """사용 가능한 OCR 엔진이 없을 때."""


# ── 노이즈 줄 필터(회사 로고/워터마크/페이지번호) ─────────────────────
_NOISE = {"ubion", "notebooklm", "notebook lm"}


def _clean_lines(lines: List[str]) -> List[str]:
    import re
    out: List[str] = []
    for raw in lines:
        s = (raw or "").strip()
        if not s:
            continue
        low = s.lower().replace(" ", "")
        if low in {n.replace(" ", "") for n in _NOISE}:
            continue
        if re.fullmatch(r"[\d\s.\-/]+", s):  # 페이지번호 등 숫자만
            continue
        # 글머리 기호 제거(본문 숫자는 보존)
        s = re.sub(r"^(?:[\-–—•·*▪◦‣]\s*|\d+[.)]\s+)", "", s).strip()
        if s:
            out.append(s)
    return out


# ── 1) Windows 내장 OCR ──────────────────────────────────────────────
def _ocr_winsdk(path: str) -> List[str]:
    import asyncio

    async def _run():
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.globalization import Language
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage import StorageFile, FileAccessMode
        engine = OcrEngine.try_create_from_language(Language("ko")) or OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            raise OcrUnavailable("winsdk: 한국어 OCR 엔진 없음")
        f = await StorageFile.get_file_from_path_async(os.path.abspath(path))
        s = await f.open_async(FileAccessMode.READ)
        dec = await BitmapDecoder.create_async(s)
        bmp = await dec.get_software_bitmap_async()
        res = await engine.recognize_async(bmp)
        return [l.text for l in res.lines]

    return asyncio.run(_run())


# ── 2) Tesseract ─────────────────────────────────────────────────────
def _ocr_tesseract(path: str) -> List[str]:
    import pytesseract
    from PIL import Image
    txt = pytesseract.image_to_string(Image.open(path), lang="kor+eng")
    return txt.splitlines()


# ── 3) EasyOCR ───────────────────────────────────────────────────────
_EASY = None


def _ocr_easyocr(path: str) -> List[str]:
    global _EASY
    import easyocr
    if _EASY is None:
        _EASY = easyocr.Reader(["ko", "en"], gpu=False)
    return _EASY.readtext(path, detail=0, paragraph=True)


def _engine_chain():
    if os.name == "nt":
        yield "winsdk", _ocr_winsdk
    yield "tesseract", _ocr_tesseract
    yield "easyocr", _ocr_easyocr
    if os.name != "nt":
        yield "winsdk", _ocr_winsdk  # 혹시 모를 환경


_ACTIVE = None  # 한 번 성공한 엔진을 기억(이미지마다 탐색 비용 절감)


def ocr_lines(path: str) -> List[str]:
    """이미지 1장 → 정리된 텍스트 줄 목록. 엔진 없으면 OcrUnavailable."""
    global _ACTIVE
    if not os.path.isfile(path):
        return []
    candidates = [(_ACTIVE_NAME, _ACTIVE)] if _ACTIVE else list(_engine_chain())
    errors = []
    for name, fn in candidates:
        try:
            lines = fn(path)
            _remember(name, fn)
            return _clean_lines(lines)
        except OcrUnavailable as e:
            errors.append(f"{name}: {e}")
        except ImportError:
            errors.append(f"{name}: 미설치")
        except Exception as e:  # 엔진별 런타임 오류 → 다음 엔진 시도
            errors.append(f"{name}: {type(e).__name__}")
    raise OcrUnavailable(
        "사용 가능한 OCR 엔진이 없습니다. Windows는 '한국어' OCR 언어팩, "
        "mac/linux는 Tesseract(kor) 또는 'pip install easyocr' 가 필요합니다. "
        f"(시도: {'; '.join(errors)})"
    )


_ACTIVE_NAME = None


def _remember(name, fn):
    global _ACTIVE, _ACTIVE_NAME
    _ACTIVE, _ACTIVE_NAME = fn, name


def available() -> bool:
    """OCR 엔진이 하나라도 동작하는지(가벼운 import 검사)."""
    if os.name == "nt":
        try:
            import winsdk  # noqa: F401
            return True
        except Exception:
            pass
    for mod in ("pytesseract", "easyocr"):
        try:
            __import__(mod)
            return True
        except Exception:
            pass
    return False
