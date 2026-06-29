"""15스타일 NotebookLM '비주얼원고' 프롬프트 생성기.

흐름(PPTX 초안과 같은 페이지):
  마스터 대본의 슬라이드(제목 + 화면 텍스트) → 슬라이드마다 NotebookLM 흰 화면에
  붙여넣을 '이미지 프롬프트'를 생성. 사용자는 NotebookLM에서 비주얼을 대량 생성 →
  캡처 → PPTX 슬라이드에 수동으로 붙인다(텍스트는 PPTX에 이미 있으므로 이미지엔 글자 X).

원칙:
  - 흰 배경(white background) 강제 — 슬라이드에 얹기 좋게.
  - 삽화/메타포/인포그래픽 등 '개념을 한 장으로' 표현.
  - 저작권: 기법·질감·조명·구도만 차용. 특정 작품의 캐릭터·로고·고유 디자인 재현 금지.
  - 이미지 안에 글자(텍스트)는 넣지 않는다(또는 최소화) — 텍스트는 PPTX 담당.

데이터: data/visual_styles.json (260626-prompt-builder 카탈로그 이식).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.vodstudio.master_script import parse_master_script

_STYLES_FILE = Path(__file__).resolve().parents[2] / "data" / "visual_styles.json"


@lru_cache(maxsize=1)
def _catalog() -> Dict[str, Any]:
    return json.loads(_STYLES_FILE.read_text(encoding="utf-8"))


def deck_design_system(style: Dict[str, Any], intensity: Dict[str, Any]) -> str:
    """NotebookLM 렌더 코드용 '디자인 시스템' 스티어링(영문). 15스타일 카탈로그가
    슬라이드덱 전체 룩도 '규정'하도록 — 스타일 선택 하나로 덱·비주얼원고가 같은 톤."""
    kws = ", ".join(style.get("keywords", []))
    return (
        f"Style: {style.get('name','')} - {style.get('def','')}. "
        "Pure white background (#FFFFFF).\n"
        f"NotebookLM visual style: {style.get('nlm_style','Custom')}.\n"
        f"Technique keywords: {kws}.\n"
        "Typography: clean sans-serif (Title: Bold, Body: Regular).\n"
        "Layout: spacious; max 5 bullet points per slide.\n"
        "Tone: professional, scholarly, organized.\n"
        "Consistency: maintain strict visual consistency across all parts/chunks.\n"
        "Copyright: borrow technique/texture/lighting/composition only; do NOT "
        "reproduce any specific work's characters, logos, or unique designs.\n"
        f"Intensity: {intensity.get('directive','')}"
    )


def list_styles() -> Dict[str, Any]:
    """UI 노출용 — 스타일 15종(+덱 디자인시스템) + 강도 3단계.

    각 스타일에 design_system(영문, 강도=medium 기준)을 함께 실어, ② 화면의 단일
    스타일 선택이 비주얼원고 프롬프트와 NotebookLM 렌더코드 디자인을 동시에 규정한다."""
    c = _catalog()
    medium = _find_intensity("medium")
    styles = []
    for s in c.get("styles", []):
        if not s.get("notebooklm", True):
            continue   # NotebookLM 부적합(제외) 스타일은 UI에 노출 안 함 → 13종
        s2 = dict(s)
        s2["design_system"] = deck_design_system(s, medium)
        styles.append(s2)
    return {"styles": styles, "intensities": c.get("intensities", [])}


def _find_style(style_id: Any) -> Dict[str, Any]:
    styles = _catalog().get("styles", [])
    for s in styles:
        if str(s.get("id")) == str(style_id):
            return s
    return styles[0] if styles else {"id": 0, "name": "기본", "keywords": []}


def _find_intensity(intensity_id: str) -> Dict[str, Any]:
    items = _catalog().get("intensities", [])
    for it in items:
        if it.get("id") == intensity_id:
            return it
    # 기본값: 적당히(medium)
    for it in items:
        if it.get("id") == "medium":
            return it
    return items[0] if items else {"id": "medium", "label": "적당히", "directive": ""}


def build_slide_prompt(title: str, screen_text: str, *, style: Dict[str, Any],
                       intensity: Dict[str, Any]) -> str:
    """슬라이드 1장 → NotebookLM 흰 배경 비주얼 프롬프트(한국어 + 영어 키워드)."""
    kws = ", ".join(style.get("keywords", []))
    concept = (title or "").strip()
    # 화면 텍스트의 글머리 기호/순번 마커를 떼고 ' · ' 로 합친다(본문 숫자는 보존).
    import re as _re
    _bul: List[str] = []
    for _ln in (screen_text or "").splitlines():
        _s = _re.sub(r"^(?:[\-–—•·*]\s*|\d+[.)]\s+)", "", _ln.strip()).strip()
        if _s:
            _bul.append(_s)
    detail = " · ".join(_bul)
    return (
        f"[비주얼원고 · {style.get('name','')} · {intensity.get('label','')}]\n"
        f"주제(개념): {concept}\n"
        + (f"핵심 내용: {detail}\n" if detail else "")
        + f"스타일: {style.get('name','')} — {style.get('def','')}\n"
        f"스타일 키워드: {kws}\n"
        f"강도: {intensity.get('label','')} — {intensity.get('desc','')}\n"
        "요구사항:\n"
        "- 위 개념을 한 장의 삽화/메타포/인포그래픽으로 표현.\n"
        "- 배경은 순백(white background). 슬라이드에 얹기 좋게 여백을 넉넉히.\n"
        "- 이미지 안에 글자(텍스트)는 넣지 말 것(텍스트는 슬라이드가 담당).\n"
        "- 기법·질감·조명·구도만 스타일을 차용하고, 특정 작품의 캐릭터·로고·"
        "고유 디자인은 재현하지 말 것.\n"
        f"- {intensity.get('directive','')}\n"
    )


def build_prompts_from_script(script_text: str, *, style_id: Any = 4,
                              intensity_id: str = "medium") -> Dict[str, Any]:
    """마스터 대본 → 슬라이드별 비주얼 프롬프트 목록."""
    style = _find_style(style_id)
    intensity = _find_intensity(intensity_id)
    slides = parse_master_script(script_text or "")
    items: List[Dict[str, Any]] = []
    for s in slides:
        items.append({
            "number": s.number,
            "title": s.title,
            "prompt": build_slide_prompt(s.title, s.screen_text, style=style, intensity=intensity),
        })
    return {
        "style": {"id": style.get("id"), "name": style.get("name")},
        "intensity": {"id": intensity.get("id"), "label": intensity.get("label")},
        "count": len(items),
        "items": items,
    }
