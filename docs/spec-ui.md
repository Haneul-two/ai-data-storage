# 웹 탐색 UI

상위 계약: `spec.md`. 구현 파일: 기존 `index.html`(Claude 편집), 신규 `tokens.css`, `assets/styles.css`, `assets/app.js`, `assets/domain.mjs`, `assets/storage.mjs`, `assets/render.js` 등 기능별 모듈.

- 메인 구조: wordmark/오늘 날짜/저장 목록 → 제목과 실데이터 건수 → 검색과 유형 탭 → 왼쪽 참가 조건 필터 + 중앙 목록 + 오른쪽 마감 임박 영역. 모바일은 필터를 접고 1열로 만든다.
- Theme Cobalt, modern-minimal, Workbench. 장식용 히어로·가짜 통계·gradient·포스터 없는 카드 placeholder는 만들지 않는다. 흰색/쿨그레이 바탕, 잉크색 본문, 코발트 블루로 활성 필터와 주 행동만 강조. 한글은 시스템 한국어 sans, 표시용 Latin은 system sans로 외부 폰트 요청 없이 구현한다.
- 목록에서 제목·유형·주최·마감·개최·참가 방식·조건을 비교할 수 있다. 상세 패널에서 출처 확인 시각, 기간, 자격, 비용, 상금, 원문 안내 링크를 보여준다.
- 필터: 유형(event/contest/hackathon), 상태(활성[closed/ended 제외]/모집중/예정/진행중/마감·종료/미정; 판정은 spec.md §3), 방식(전체/온라인/오프라인/혼합), 텍스트 검색. `내 저장`은 동일 결과를 saved id로 거른다. 필터 수와 결과 수는 일치한다.
- 목록/월별 달력 전환. 일정이 없는 항목은 목록에서 확인 가능하고 달력에서는 일정 미정 건수를 안내한다. 마감(출처의 신청·제출 마감 날짜)과 개최일은 다른 마커다.
- 필터 복원은 URL filter가 있으면 URL 우선, 없으면 localStorage, 잘못된 값은 기본값. loader는 ingest-status.json의 sources를 opportunities.sources에 id 기준 overlay해 소스 상태를 표시한다. stale 항목은 '출처 재확인 필요', date-only 마감은 '시간 확인 필요', 국내 eligibilityVerified=false는 '참가 조건 확인 필요'를 표시한다. 저장 id가 데이터에서 사라지면 id를 보존하고 저장 목록에 사라진 건수와 안내를 표시한다. 목록 재렌더가 검색 포커스를 빼앗지 않는다. 저장 버튼은 aria-pressed, 상세는 dialog semantics, Escape/닫기/초기 포커스/복귀 구현.
- `?debug=empty|error|loading`과 고정 `?now=2026-10-02T03:00:00Z`로 검사 상태를 재현한다. debug와 now는 localhost/127.0.0.1에서만 작동하고 테스트 모드 배너를 표시한다. GitHub Pages production은 무시한다. debug 값을 원격 수집에 사용하지 않는다.
- design-lab 경량 3시안과 조절 미리보기는 메인에서 링크하지 않는 기본 비노출 개발 자료. Pages branch root 구조라 배포 root에 남으며 '미배포'로 약속하지 않는다(완전 제외는 이후 Pages artifact workflow 도입 시 가능). 사용자 선택 라운드는 이미 확정했으므로 추가 승인 게이트는 없다.
- 검증: Node 회귀 테스트, 브라우저 화면·상태·동작, 6개 폭과 키보드. 실제 통과 내역만 HISTORY에 기록.
