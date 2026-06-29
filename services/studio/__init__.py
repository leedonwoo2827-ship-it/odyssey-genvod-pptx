"""PPTX 생성 서브패키지 (문서공방 generators 에서 이식한 슬림 버전).

회사 양식 PPTX 를 견고하게 채우는 렌더러만 가져왔다. docx/hwpx/xlsx 등
이 제품에서 안 쓰는 포맷과 pipeline/llm/recipes 는 의존성을 줄이려 제외했다.

사용:
    from services.studio.generators import render
    render("pptx", payload, out_path, template=..., mode="design_deck")
"""
