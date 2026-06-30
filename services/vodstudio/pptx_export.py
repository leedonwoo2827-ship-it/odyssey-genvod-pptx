"""마스터 대본 → 회사 양식 PPTX 초안.

흐름(딥리서치/RAG → PPTX 초안 40/60장):
  1) 기존 마스터 대본 텍스트(슬라이드 번호/제목/화면 텍스트/상세 대본 블록)를
     master_script.parse_master_script 로 Slide 리스트로 파싱.
  2) Slide → {title, subtitle, slides:[{title, bullets[]}]} 페이로드로 변환.
     - 슬라이드 제목  → slide.title
     - 화면 텍스트    → bullets (줄 단위)  ※ 비주얼원고가 붙기 전 '텍스트 초안'
     - 상세 대본      → 샘플영상 TTS 원천(여기선 사용 안 함)
  3) studio.generators.render('pptx', ...) 로 회사 양식(_context/pptx_template.pptx)에 채움.

회사 '보고서' 양식을 슬라이드로 재사용하지만, pptx_gen 이 placeholder 를 '유형'으로
채우고 폰트 상한을 슬라이드용으로 덮으므로 마스터 변경 없이 동작한다.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.vodstudio.master_script import parse_master_script

# 회사 양식 PPTX 템플릿. 깃허브에 함께 올라가는 assets/templates/ 에 둔다.
# (구버전 _context/ 위치는 하위호환 폴백) · 환경변수 VOD_PPTX_TEMPLATE 로 재정의 가능.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE_CANDIDATES = (
    _REPO_ROOT / "assets" / "templates" / "pptx_template.pptx",
    _REPO_ROOT / "_context" / "pptx_template.pptx",   # 하위호환
)


def company_template_path() -> Optional[str]:
    """회사 양식 경로. 환경변수 VOD_PPTX_TEMPLATE > assets/templates > _context.
    없으면 None(빈 16:9 템플릿으로 폴백)."""
    env = (os.environ.get("VOD_PPTX_TEMPLATE") or "").strip()
    if env:
        return env if Path(env).is_file() else None
    for cand in _TEMPLATE_CANDIDATES:
        if cand.is_file():
            return str(cand)
    return None


def _bullets_from_screen_text(screen_text: str) -> List[str]:
    """화면 텍스트를 슬라이드 불릿 줄 목록으로. 글머리 기호/공백 정리."""
    lines: List[str] = []
    for raw in (screen_text or "").splitlines():
        s = raw.strip()
        if not s:
            continue
        # 글머리 기호(-, –, —, •, ·, *)나 '1.'/'1)' 식 순번 마커만 제거.
        # 본문에 포함된 숫자(예: '1960년대')는 보존한다.
        s = re.sub(r"^(?:[\-–—•·*]\s*|\d+[.)]\s+)", "", s).strip()
        if s:
            lines.append(s)
    return lines


def slides_payload_from_script(script_text: str, title: str = "",
                               subtitle: str = "") -> Dict[str, Any]:
    """마스터 대본 텍스트 → pptx_gen 페이로드. 화면 텍스트가 비면 제목만 둔다."""
    slides_in = parse_master_script(script_text or "")
    slides_out: List[Dict[str, Any]] = []
    for s in slides_in:
        # 본문 = 화면 텍스트(슬라이드용). 없으면 상세 대본으로라도 채워 본문이 비지 않게.
        bullets = _bullets_from_screen_text(s.screen_text)
        if not bullets:
            bullets = _bullets_from_screen_text(s.narration)
        slides_out.append({"title": (s.title or "").strip() or f"슬라이드 {s.number}",
                           "bullets": bullets})
    if not slides_out:
        slides_out = [{"title": title or "내용", "bullets": []}]
    return {"title": (title or "").strip() or "제목",
            "subtitle": (subtitle or "").strip(),
            "slides": slides_out}


def slides_payload_from_images(image_paths: List[str], title: str = "",
                               subtitle: str = "") -> Dict[str, Any]:
    """NotebookLM 슬라이드 이미지들 → OCR → pptx_gen 페이로드.

    이미지마다 OCR한 줄에서 **첫 줄=제목, 나머지=본문**으로 둔다(제목 구분이 틀리면
    PPTX에서 수작업으로 옮기는 것을 전제). 그림 속 글자가 섞여도 무방(대강 추출).
    OCR 엔진이 없으면 ocr.OcrUnavailable 이 올라온다(호출부에서 안내/폴백)."""
    from services.vodstudio import ocr
    slides_out: List[Dict[str, Any]] = []
    for p in image_paths:
        lines = ocr.ocr_lines(p)
        t = lines[0] if lines else ""
        bullets = lines[1:] if len(lines) > 1 else []
        slides_out.append({"title": t, "bullets": bullets})
    if not slides_out:
        slides_out = [{"title": title or "내용", "bullets": []}]
    return {"title": (title or "").strip() or "제목",
            "subtitle": (subtitle or "").strip(),
            "slides": slides_out}


def render_company_pptx(payload: Dict[str, Any], out_path: str,
                        mode: str = "basic") -> str:
    """페이로드를 회사 양식 PPTX 로 렌더. 회사 양식 1개 고정 · **표지 없음**
    (NotebookLM과 1:1 본문 슬라이드만). mode 인자는 하위호환용(무시)."""
    from services.studio.generators import pptx_gen
    return pptx_gen.render(payload, out_path,
                           template=company_template_path(), include_cover=False)


def script_to_pptx(script_text: str, out_path: str, *, title: str = "",
                   subtitle: str = "", mode: str = "basic") -> str:
    """편의 함수: 대본 텍스트 → 회사 양식 PPTX 파일."""
    payload = slides_payload_from_script(script_text, title=title, subtitle=subtitle)
    return render_company_pptx(payload, out_path, mode=mode)
