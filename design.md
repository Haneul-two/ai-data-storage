# Design System — AI Radar

갱신 2026-10-12. 세부 명세·대안 비교는 [`design-lab/radar/DESIGN.md`](design-lab/radar/DESIGN.md). 이전 "Cobalt 카드 + 3열 레일" 디자인은 폐기했다.

## 방향

**마감 중심 비교 목록.** 무채색 바탕에 짙은 forest 단일 강조, 임박 마감에만 amber. 장식(히어로, 그라디언트, 유리, 큰 그림자, 유형별 색 배지)을 두지 않고 열 정렬·구분선·숫자로 비교한다. 유형·상태는 색이 아니라 글자로 구분한다. 외부 폰트·이미지 요청 없음. 모든 값은 루트 `tokens.css`의 토큰이다.

## 토큰 요약 (`tokens.css` 실제 값)

| 구분 | 토큰 | 값 |
|---|---|---|
| 바탕 / 표면 | `--color-page` / `--color-surface` | `#f6f7f5` / `#ffffff` |
| 본문 / 보조 | `--color-ink` / `--color-muted` | `#202622` / `#66706a` |
| 강조 | `--color-accent` / `-strong` / `-soft` | `#16604a` / `#0f4a39` / `#e6efea` (선택 상태·주요 행동만) |
| 임박·경고 | `--color-urgent` / `--color-warn` (+`-soft`) | `#8a5a00` / `#fff4dc` |
| 오류 | `--color-danger` (+`-soft`) | `#a8261c` / `#fdecea` |
| 선 | `--color-line` / `-strong` | `#dde2de` / `#c5ccc7` |
| 글꼴 | `--font-body`, `--font-display` | `'Malgun Gothic','Apple SD Gothic Neo',system-ui,sans-serif` |
| 간격 | `--space-1…8` | 4·8·12·16·24·32·48·64px |
| 반경 | `--radius-sm/md/lg/pill` | 4·6·6·999px (pill은 쓰지 않음) |
| 레이아웃 | `--rail-filter`, `--topbar`, `--drawer`, `--layout-max` | 200 · 60 · 540 · 1360px |
| 터치 | `--tap`, `--control` | 44px, 데스크톱 40px / 모바일 44px |
| 모션 | `--transition`, `--transition-drawer` | 120ms, 160ms. reduced-motion 시 제거 |

## 레이아웃과 반응형

상단 바(브랜드·탐색/저장·갱신 시각·새로고침) → 검색 → 도구줄(유형 탭·건수·정렬·목록/달력) → 필터 | 비교 목록. 오른쪽 마감 임박 레일은 없다(마감순 정렬과 중복). 마감 임박·출처 상태는 필터 하단 접힌 details.

| 폭 | 필터 | 목록 행 |
|---|---|---|
| 1280 이상 | 왼쪽 200px 고정(sticky) | 제목·마감·개최·참가/상금·저장 5열 + 열 머리글 |
| 960~1279 | 접힘(토글), 목록 전폭 | 제목·마감·개최·저장 4열, 참가/상금은 둘째 줄 |
| 960 미만 | 접힘(토글) | 라벨 있는 세로 행: 제목 전체 너비 → 마감·개최 2열 → 참가/상금 → 저장(별도 행) |
| 360 미만 | 접힘 | 위 구성에서 마감·개최도 한 줄씩 |

- 좁은 화면에서 4고정열과 사이드바를 겹쳐 두지 않는다. 제목은 항상 200px 이상(회귀 검사 `tools/check_radar_ui.py`가 320~1440 8개 폭에서 확인).
- 행 전체를 버튼으로 만들지 않는다. 제목 버튼이 상세 열기, 저장은 별도 버튼. 긴 제목·URL은 `overflow-wrap: anywhere`.
- `html, body { overflow-x: clip }`, 320px까지 가로 넘침 없음.

## 컴포넌트 규칙

- **행**: 제목·주최·유형·상태·출처·마지막 확인 / 마감(D-day·"시각 미확인") / 개최 / 방식·자격·상금 / 저장. 마감과 개최는 별도 필드.
- **노출**: `assets/visibility.mjs`의 `isListed(item, now)`가 목록·검색·건수·저장 보기·달력·마감 임박·상세 진입을 결정. 마감(exact 시각 이후, 날짜만 있으면 그날 이후, 출처 closed)은 목록에서 제외하고 상태 필터에 마감 옵션을 두지 않는다. 마감 미확정 미래 행사는 유지.
- 날짜 표기: 정확 시각 `2026.10.27 (화) 06:00` + 서울 기준, 날짜만이면 "마감 시각 미확인", 없으면 "미확인".
- **상세**: 네이티브 `<dialog>`. 데스크톱 오른쪽 540px 드로어, 모바일 전체 화면. 초기 포커스는 닫기 버튼, 닫으면 연 제목으로 복귀.
- **달력**: 마감=원, 개최=마름모(모양으로도 구분). 960 미만에서는 칸에 점만, 아래 "이번 달 일정" 목록이 클릭 대상.
- **상태 화면**: 로딩 skeleton, 빈 결과(필터 초기화), 오류(다시 시도), 새로고침 중(버튼 disabled).
- 접근성: `:focus-visible` 2px 링, 본문 바로가기, `aria-pressed` 토글, 터치 목표 44px(모바일), 색만으로 상태를 구분하지 않음.

## 정보 정직성

모르는 값은 추측하지 않는다 — "확인 필요", "미확인". 오래된 데이터와 실패한 출처는 숨기지 않고 알림으로 표시한다.

## 참고 출처 (구조만 참고, 복제하지 않음)

- Linear 필터·피크: https://linear.app/docs/filters · https://linear.app/docs/peek — 목록을 유지한 채 조건을 좁히고 맥락을 잃지 않는 상세(드로어).
- Carbon 데이터 테이블 가이드: https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines — 열 머리글 정렬·밀도·좁은 화면 변환.
- 그 외 Devpost·Kaggle·Luma·component.gallery 참조는 `design-lab/radar/DESIGN.md`.

## 디자인 탐색 자료

`design-lab/`(메인에서 링크하지 않는 개발 자료, Pages가 branch root 배포라 배포물에 포함). 채택안 근거는 `design-lab/radar/`.
