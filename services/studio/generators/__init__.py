"""출력 렌더러 디스패치 (슬림 — pptx 계열만).

render(fmt, payload, out_path, template=None, mode=None) → 실제 파일 생성.
payload(slides 모드): {"title","subtitle","slides":[{"title","bullets":[...]}]}
또는 Markdown 문자열(자동 변환).
"""
from __future__ import annotations

from typing import Any, Optional


def render(fmt: str, payload: Any, out_path: str, template: Optional[str] = None,
           mode: Optional[str] = None) -> str:
    fmt = (fmt or "pptx").lower()
    if fmt == "md":
        from . import md_gen
        return md_gen.render(payload, out_path)
    if fmt == "pptx":
        m = (mode or "").lower()
        if m == "mckinsey_deck":
            from . import mckinsey_pptx_gen
            return mckinsey_pptx_gen.render(payload, out_path, template=template)
        if m == "design_deck":
            from . import design_pptx_gen
            return design_pptx_gen.render(payload, out_path, template=template)
        from . import pptx_gen
        return pptx_gen.render(payload, out_path, template=template)
    raise ValueError(f"지원하지 않는 출력 형식: {fmt}")
