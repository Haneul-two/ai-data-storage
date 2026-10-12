# HISTORY

## 2026-10-02 — AI 기회 보드 전면 개편

- 요청: AI 행사·공모전·해커톤만 탐색하도록 UI/UX와 수집 구조 전체 개편.
- 인테이크: 개인용, 국내+한국 참가 가능한 해외 온라인, 공개 무료/일1회/로그인 제외, 밝은 탐색 보드. 사용자 승인 `추천안으로 진행`.
- 기준: Haneul-two 저장소 최신 HEAD `ee68ae6442f3980fea6d55b2621d5e11c5c141bc`. 기존 bsky2327-oss checkout 및 CLAUDE.md 미커밋 변경은 보존. 새 checkout `C:/Users/caring/Projects/ai-data-storage-events`, branch `feat/ai-opportunity-board`.
- 조사: 기존 수집기는 유형/접수 마감이 없고 전체 소스 실패에도 updatedAt을 바꿈. workflow는 unrelated 카테고리 수집을 포함. 실제 테스트 workflow는 echo뿐.
- 환경: Node24.15.0, Python3.11.15, Claude Code2.1.287. Claude `READY` 호출 성공. 첫 shell 네트워크 차단은 읽기 호출 권한 확장으로 해결. 한글 stdin 깨짐은 UTF-8 파일 기반 인계로 예방한다.
- 출처 확인: Devpost robots 읽기 허용, 공개 목록 API 200 및 hackathons/meta 구조 확인. 위비티/데이콘 공개 목록·robots 200. 온오프믹스는 일반 수집 User-agent 차단으로 제외.
- 병렬 조사 에이전트는 사용량 제한으로 실패. 직접 조사로 전환.
- 문서: spec, UI/ingest 하위 사양서, implementation-plan 작성.

| 검증 | 상태 | 증거 |
|---|---|---|
| 최신 원격 HEAD | 통과 | git ls-remote: ee68ae6 |
| 별도 checkout/branch | 통과 | git clone, switch; 기존 checkout 보존 |
| Claude 응답 | 통과 | READY, exit0 |
| Devpost 공개 구조 | 통과 | HTTP200, hackathons/meta 및 2개 실제 항목 |
| 독립 사양서 점검 | 통과 | 6개 수정 반영(문서) |
| Python/Node 회귀 테스트 | 통과 | RED 후 GREEN. 최종 Python 97 OK · Node 106 pass (`docs/evidence/final-checks.txt`) |
| 실제 수집/실데이터 | 통과 | 4개 출처 ok(devpost 6·dacon 11·wevity 15·aisummit 1), 전체 33건. 최종 통합에서는 네트워크 재수집 안 함 |
| 화면/동작/반응형 | 통과 | `tools/browser_check.py` 35/35(Edge, 새 profile). 캡처 `docs/evidence/*-desktop.png`, `*-mobile.png` |
| 다른 모델 구현 교차 리뷰 | 통과 | Claude 구현 → Codex 독립 리뷰. 1차 7건·2차 4건 보완 |
| 원격 push/scheduled run/Pages 운영 | 미실행·미확인 | 통과로 쓰지 않음. 별도 사람 승인 필요 |

### 최종 통합 (2차 리뷰 4건 보완)

- 구현은 Claude, 독립 리뷰는 Codex. 1차 7건(`docs/tasks/review-fixes.md`) 보완 후 2차 4건 보완.
- 2차 4건: ① 로딩/오류 캡처에 '아직 수집된 기회가 없어요'가 보임 → `buildNotices`에 `phase` 전달, ready에서만 데이터 알림. ② `korea_allowed('... standard exceptions (see rules)')`가 True → 괄호 안 실제 국가명 목록일 때만 승인. ③ `load_curated`·신선 결과가 모양만 검증 → `meets_contract` 재사용. ④ 수집기 exit 1이면 workflow가 commit 전에 멈춰 실패 상태가 사이트에 안 나감 → `continue-on-error`+tests 후 commit+마지막 실패 step, exit 2는 commit 제외.
- 검사 수: Python 90→97, Node 103→106, 브라우저 35/35. 실제 결과는 `docs/evidence/final-checks.txt`.
- 캡처 위치: `docs/evidence/` (loading/error/empty/no-results/after/calendar/detail × desktop·mobile). 갱신 캡처 12개(after-desktop/mobile, detail-desktop, calendar-desktop/mobile, empty·error·loading-desktop/mobile, no-results-desktop)는 root가 직접 열어 확인을 마쳤다. 로딩·오류의 '미수집' 알림 제거도 확인.
- 현재 데이터: 전체 33 = 활성23(모집중21 + 예정2) + 종료9 + 마감1. 앞서 쓴 '종료일 기준 아직 끝나지 않음 24'는 화면 활성 수가 아니다(이전 단계의 역사 수치 34/24는 당시 결과로 유지).
- 교차 리뷰 완료: Claude 구현 → Codex 리뷰, Codex 보조도구(browser_check/run_claude) → Claude 읽기 리뷰. `tools/run_claude.py`의 `.cmd` 위험은 이 환경 비해당(`shutil.which`·`Get-Command` 모두 `claude.EXE`), 내부 전용·승인된 고정 명세만 전달.
- root 독립 재실행 완료: Python 97 OK, Node 106 exit0, offline 33/0 계약 통과, browser 35/35 오류0, 모든 항목 meets_contract True, 마스킹 누락 0, diff --check exit0. 기존 데이터 diff 없음, 기존 checkout CLAUDE.md 사용자 수정 보존.
- 로컬 성능 1회: navigation 436.8ms, 리소스 28·128432 bytes, DOM 897, 외부 리소스 0. 배포/실기기 성능은 미확인.
- 환경 브라우저 zoom 때문에 도구 CSS 너비와 캡처가 엇갈렸다 → 깨끗한 Edge profile로 실측해 해결.
- 브라우저 QA 스크립트: Python API `.first()` 오류와 중복 필터 버튼 locator 수정.
- 규칙집 추가 없음: 일반화할 규칙은 테스트와 최종 코드에 이미 드러나 별도 추가가 필요 없다.
- 한계: update.yml 변경은 YAML 텍스트 회귀로만 확인했고 Actions에서 실행한 적이 없다. 원격 scheduled run과 Pages 운영은 미확인.

## 2026-10-02 — 독립 사양서 리뷰 반영 (independent spec review completed)

- 독립 리뷰 결과를 문서에 반영(문서만 수정). `docs/implementation-plan.md`는 이미 존재했으므로 리뷰의 '계획 부재' 지적은 수정사항에서 제외.
- 수정 1: 전체 실패 시 opportunities.json 바이트 불변, 시도 상태는 `data/ingest-status.json`에 원자 기록 후 UI overlay. 부분 실패·archived·stale(90일) 규칙. 이유: 실패를 성공 갱신으로 오인 방지.
- 수정 2: `sourceStatus`/`stale` 추가, 상태 판정 우선순위와 필터(활성/모집중/예정/진행중/마감·종료/미정), date-only 당일 포함+시간 확인 필요. 이유: 마감 오판 방지.
- 수정 3: 한국 참가 허용 증거 기준과 국내/해외 eligibilityVerified 처리, 연령/학생 조건 보존.
- 수정 4: 허용 네트워크 호스트와 URL 검증(공인 HTTPS/443/userinfo 없음/redirect), 외부 apply URL 비fetch, 구조 미확인 소스는 error/blocked.
- 수정 5: 저장 id 소실 안내, URL 우선→localStorage→기본값, debug/now는 localhost/127.0.0.1 한정+테스트 배너.
- 수정 6: design-lab은 배포 root에 남는 기본 비노출 자료('미배포' 약속 금지), fixtures 최소 markup·출처 주석·연락처 마스킹.

## 2026-10-12 — 운영 활성화 승인 및 원격 반영 진행

- 승인: 사용자가 '원격 반영·Pages 배포·매일 09시 갱신 활성화'를 '이어서 진행'으로 승인했다. 추가 승인 질문은 없다.
- 권한: 원격 `Haneul-two/ai-data-storage`의 관리자·push 권한 확인. master/루트 legacy Pages 활성, URL https://haneul-two.github.io/ai-data-storage/.
- 원격 변경 보존: 원격 master가 ee68ae6에서 aa04b7e까지 자동 데이터 갱신 3건만 앞서 있다. 다른 변경을 되돌리지 않고 그대로 보존하며 병합한다.
- 내부 명세 로컬 보관: `docs/tasks/`(실행 명세)와 `tools/run_claude.py`(로컬 오케스트레이터)는 이번 작업의 내부 도구라 배포 저장소에 공개하지 않으려고 `.gitignore`에 추가했다. 파일은 삭제하지 않고 로컬에 둔다. `tools/browser_check.py`·테스트·검증 결과는 공개 검증 자료로 유지한다.
- 상태: 반영 진행 중이며 푸시·배포 완료는 아직 아니다.
