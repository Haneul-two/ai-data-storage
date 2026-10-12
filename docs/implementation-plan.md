# AI 기회 보드 구현 계획

**Goal:** 국내/한국 참가 가능 해외 온라인 AI 행사·공모전·해커톤을 비교·저장하고 원문으로 이동한다.
**Architecture:** 정적 ES modules UI와 Python 공개 수집 파이프라인. 상호 계약은 schemaVersion2 JSON.
**Spec:** `docs/spec.md`, `docs/spec-ui.md`, `docs/spec-ingest.md`.
**Execution:** make-it과 사용자 규칙에 따라 추가 질문 없이 실행한다. 기존 파일 구현은 Claude, 조사/새 문서/독립 검증은 Codex.

## 공통 제약과 리뷰 중점

- 기존 파일/브랜치를 삭제하지 않고 원격 변경·운영 활성화를 하지 않는다.
- 원본 events.json은 수정하지 않고 신규 opportunities.json을 사용한다.
- 사용자가 마감을 놓치게 하는 timezone/당일/시간 미확정 혼동, 접수 마감과 개최일 혼동, source 실패의 성공 표기, 일반 AI 키워드 오탐, 해외 참가 자격 오판을 우선 검증한다.
- UI 외부 HTML 주입과 저장 실패의 성공 표시를 금지한다.

## 1. 독립 사양서 점검

- [x] 독립 사양서 리뷰 수행(Codex가 사양서를 읽고 6개 수정 반영).
- [x] 모순/빈칸/검증 불가/숨은 가정을 수정하고, 변경 이유를 HISTORY에 기록한다. (6개 수정 반영 완료)

## 2. 데이터 파이프라인 (Claude 담당)

- [x] 먼저 `tests/test_opportunities.py`와 최소 source fixtures(필요한 public markup만, capturedAt/URL 주석, synthetic 추가, 연락처 마스킹, raw 전체 페이지 금지)를 작성한다. ingest-status.json 분리·전체 실패 시 opportunities.json 바이트 불변 테스트 포함. 기대값: chair/paid 불일치, AI hackathon 일치, 해외 현장 제외, invalid date 거부, 실패 시 이전 파일 보존.
- [x] `.venv/Scripts/python.exe -m unittest discover -s tests -v` 실행하여 구현 부재에 따른 RED 출력을 기록한다.
- [x] `collectors/opportunities/{rules,sources,pipeline,cli}.py` 및 얇은 entrypoint를 만든다. 예: `is_ai_related(title, tags, description) -> bool`, `normalize_item(raw, source_id) -> dict|None`, `collect(output_path, dry_run=False) -> report`.
- [x] 같은 명령 GREEN 확인. 네트워크 없이 파서 fixture 테스트.
- [x] 실제 `--dry-run` 결과/출처 대조 후 `data/opportunities.json` 생성.
- [x] update/test workflow를 신규 검증과 승인 게이트로 바꾸고, 요구 의존성을 requirements.txt에 반영한다.

## 3. 웹 탐색 UI (Claude 담당, 2와 파일 소유권 독립)

- [x] `tests/domain.test.mjs`, `tests/storage.test.mjs`부터 작성. 고정 now의 마감 당일/시간대/유형·저장 필터/unknown date 정렬/잘못된 localStorage 테스트.
- [x] `node --test tests/*.test.mjs`로 RED 확인 후 domain/storage 모듈을 구현해 GREEN 확인.
- [x] 기존 index.html을 새로운 모듈 entry로 바꾸고 tokens.css, assets/styles.css, app/render 모듈을 만든다. 데이터는 `data/opportunities.json` 상대 fetch.
- [x] 검색·필터·상세·저장·달력·소스 상태·4종 상태와 debug 재현을 완성한다.
- [x] design.md/CLAUDE.md/README.md를 실제 구조로 정리한다. 이전 카테고리 파일은 그대로 둔다.
- [x] design-lab 경량 비교 자료를 작성하되 사용자 추가 승인은 묻지 않는다. 배포 root에 남는 기본 비노출 개발 자료이며 '미배포'로 쓰지 않는다.

## 4. 통합 검증과 리뷰 (Codex 담당)

- [x] Python/Node tests, 실제 수집 dry-run, git diff --check, schema 대조.
- [x] HTTP server port8012로 기동. Playwright로 1440×900/390×844 screenshot을 직접 보고, 320/375/414/768px overflow와 키보드/검색/저장/달력/오류 상태 확인.
- [x] Claude 구현을 Codex가 읽기 리뷰. 지적은 Claude에 좁은 변경 범위로 전달하고 재검증한다.
- [x] 작성자와 다른 모델 교차 리뷰: Claude 구현/Codex 리뷰, Codex 보조도구/Claude 리뷰 완료. (이전 '독립 Claude 최종 리뷰 미실행'은 Codex가 제품을 직접 구현하는 경우의 계획상 가정이었다. 추가 리뷰 없음.)
- [x] AGENTS 현재 상태, HISTORY 검증표, 실행법을 실제 증거로 갱신한다. 실제 실패를 고쳐 확인한 재사용 규칙만 make-it rules에 반영할 후보로 기록한다.
- [x] 로컬 결과/운영 미시작/리뷰 상태와 남은 운영 승인만 보고한다.
