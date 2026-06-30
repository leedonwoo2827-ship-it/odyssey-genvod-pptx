# PPTX 폰트 (Google Fonts · OFL)

PPTX 생성에 쓰는 글꼴. 이 폴더에 아래 두 .ttf 파일을 넣어두면 setup 단계에서 PC에 설치됩니다.

| 용도 | 폰트 | 파일명 | 받는 곳 |
|---|---|---|---|
| 제목 | **Black Han Sans** | `BlackHanSans-Regular.ttf` | https://fonts.google.com/specimen/Black+Han+Sans |
| 본문 | **Do Hyeon** | `DoHyeon-Regular.ttf` | https://fonts.google.com/specimen/Do+Hyeon |

## 넣는 법
1. 위 링크에서 **Download / 다운로드** → 압축 해제
2. `BlackHanSans-Regular.ttf`, `DoHyeon-Regular.ttf` 두 파일을 **이 폴더(assets/fonts/)** 에 복사
3. (각 폰트의 `OFL.txt` 라이선스 파일도 같이 두기 — 재배포 시 동봉 필요)

## 설치
- **Windows**: `.ttf` 우클릭 → 설치 / 또는 setup 스크립트가 자동 복사
- **macOS/Linux**: `~/Library/Fonts` 또는 `~/.fonts` 로 복사 / setup 스크립트가 처리

## 코드 연동
`services/studio/generators/pptx_gen.py`:
- 제목 `_TITLE_FONT = "Black Han Sans"`
- 본문 `_BODY_FONT = "Do Hyeon"` (불릿 점 제거)

폰트가 PC에 설치돼 있지 않으면 PPTX/PDF에서 대체 글꼴로 보입니다 — 반드시 설치하세요.

## 라이선스
두 폰트 모두 **SIL Open Font License 1.1 (OFL)** — 상업적 사용·재배포 자유. repo 동봉 시 각 `OFL.txt`를 함께 두세요.
