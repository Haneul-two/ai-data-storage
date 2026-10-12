# AI 기회 보드 — Claude Code 개발 가이드 (현재 상태·규칙)

경과·검증·사고 기록은 `docs/HISTORY.md`, 사양은 `docs/spec*.md`, 작업 규칙 요약은 `AGENTS.md`.
현재 상태(2026-10-12): **운영 활성화 승인됨, 원격 반영(push·Pages·매일 09시 갱신) 진행 중** — 완료 전까지 완료로 쓰지 않는다. 원격 master의 자동 데이터 갱신 3건은 보존하며 병합한다. `docs/tasks/`·`tools/run_claude.py`는 내부용이라 git 제외(로컬 보관).
이전 상태(역사): 로컬 구현·검증 완료(데이터 전체33 = 활성23 + 종료9 + 마감1), 원격(push·workflow·Pages·예약) 미실행. 증거는 `docs/evidence/final-checks.txt`, 통과표는 `docs/verification.md`.

## 프로젝트 개요

국내 + 한국 참가 가능 해외 온라인 AI 행사·공모전·해커톤 탐색 보드(개인용). 정적 `index.html` + ES modules가 `data/opportunities.json`(+`data/ingest-status.json` overlay)을 fetch해 렌더링한다. 서버 없음, GitHub Pages 동작. 이전 5탭 대시보드(`ai-events.html`, 카테고리 JSON, 뉴스/논문/채용/도구 수집기)는 보관만 하고 쓰지 않는다.

## 아키텍처

```
index.html ─ tokens.css + assets/styles/*.css
           └ assets/app.js ─ render.js ─ view-*.js ─ item-parts.js ─ dom.js/icons.js
                     └ 순수 로직(.mjs, Node 테스트 대상): time · status · filters · calendar · storage · data · notices · format · safe-url · debug
data/opportunities.json, ingest-status.json  ←  collectors/opportunities/ (백엔드 영역)
```

- 로직(`.mjs`)은 DOM을 만지지 않고 `now`를 인자로 받는다. DOM 코드(`.js`)에는 판정 로직을 넣지 않는다.
- 화면 갱신: 선택 그룹·검색 입력·헤더 버튼은 한 번 만들고 값만 바꾼다(포커스·캐럿 유지). 결과 영역만 다시 그린다.

## 작업 규칙

- 한 파일에 몰아넣지 않는다. 새 기능은 해당 모듈에 넣거나 새 모듈로 분리한다. (design-lab 시안만 1파일 HTML 예외)
- 색·글꼴·간격·반경은 `tokens.css` 토큰만 쓴다. 컴포넌트 CSS에 리터럴 색을 쓰지 않는다.
- **외부/출처 문자열은 `h()`(text node)·`textContent`로만 넣는다. `innerHTML`·`insertAdjacentHTML` 금지** — 출처 콘텐츠가 스크립트를 실행하지 못하게 하기 위해서다.
- 외부 링크는 `safeHttpsUrl()`을 통과한 https만, `target="_blank" rel="noopener noreferrer"`. 집계 사이트 URL을 '공식 신청'이라 부르지 않는다('안내 페이지 열기', '출처 확인').
- 확인하지 않은 날짜·참가비·자격을 만들지 않는다. 없으면 '미확인'/'확인 필요'로 쓴다. 마감 날짜와 개최 날짜를 섞지 않는다.
- 사용자에게 API·스키마·오류 원문을 보이지 않는다(출처, 마지막 확인, 수집 지연만).
- 저장 기록 쓰기가 실패하면 저장됐다고 말하지 않는다(세션 한정 안내). 저장 id는 데이터에서 사라져도 지우지 않는다.
- `?debug`/`?now`와 `window.__boardDebug`는 localhost/127.0.0.1에서만. production에서 무시.
- `data/*.json`은 수집기 산출물이다. 화면 작업 중 수동 수정·가짜 데이터 작성 금지. 화면 검증은 repo 밖 합성 데이터로 한다.
- `fetch()` URL은 `data/` 하위 상대 경로로 고정.
- 문서 3종(README/CLAUDE/design)은 구현과 함께 갱신한다.

## 사고에서 얻은 규칙

- 읽기가 끝나지 않은 로딩/오류 중에 '아직 수집된 기회가 없어요'를 띄운 적이 있다 → 데이터 상태 알림(미수집·지연·출처)은 `phase === 'ready'`에서만, 브라우저 저장 경고는 항상.
- root가 소유한 서버(8012)는 소유하지 않은 구현자가 끝내지 않는다 → 이전에 종료돼 브라우저 연결이 끊겼다.
- 수집기 전체 실패(종료 코드 1)도 `ingest-status.json`을 commit해야 사이트에 실패가 전달된다 → workflow는 collector를 `continue-on-error`로 두고 tests 뒤 commit, 마지막에 실패 표시. 종료 코드 2(손상)는 commit하지 않는다.
- 표준 예외 문구는 괄호 안 실제 국가명이 있어야 한국 참가로 승인한다(`(see rules)`는 거부). curated·신선 결과·저장 항목 모두 `rules.meets_contract`를 거친다.

- 목록 재렌더가 검색 입력을 다시 만들면 포커스·캐럿이 사라진다 → 입력과 필터 버튼은 재생성하지 않는다.
- 저장 토글이 목록 전체를 다시 그리면 키보드 포커스를 잃는다 → 버튼 상태만 동기화하고, 저장 보기에서만 다시 그린 뒤 포커스를 복원한다.
- 좁은 화면의 달력 칸은 마커 버튼이 44px을 못 만든다 → 칸에는 점만, 클릭은 월 일정 목록(agenda)에서 받는다.
- 모바일 보조 버튼(`calc(--control - …)`)이 36px로 줄어든 적이 있다 → 터치 목표는 `--control`(모바일 44px) 미만으로 줄이지 않는다.
- 검증할 때 브라우저 대기 조건을 `.opp`만 쓰면 달력 화면에서 시간초과가 난다 → `.opp, .state, .cal`.

## 명령

```bash
.venv/Scripts/python.exe -m http.server 8012 --bind 127.0.0.1
node --test tests/*.test.mjs
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe collectors/collect_events.py --dry-run
.venv/Scripts/python.exe collectors/collect_events.py --offline
.venv/Scripts/python.exe tools/browser_check.py   # 선택: playwright==1.63.0 + installed Edge, 서버 8012 필요
```

예약 수집(`update.yml`)은 변수 `ENABLE_OPPORTUNITY_UPDATES=true`가 있어야만 동작한다. 켜는 것은 사용자 승인 사항.

## 디자인

`design.md`와 `tokens.css` 참고. 탐색 시안과 조절판은 `design-lab/`(메인에서 링크하지 않음).
