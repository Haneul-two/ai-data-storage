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

### 2026-10-12 — 데이터 갱신 뒤 Pages 재빌드 누락 수정 (실행 검증 전)

- 발견한 운영 경계: `GITHUB_TOKEN`으로 push한 commit은 branch 기반(legacy) Pages build를 자동 실행하지 않는다. 현재 Pages는 master/루트 legacy라, 매일 갱신 commit이 생겨도 사이트가 갱신되지 않을 수 있었다.
- 수정(`.github/workflows/update.yml`): job `permissions`에 `pages: write` 추가(`contents: write` 유지). `Commit changes` 직후·마지막 실패 표시 step 이전에 `Request Pages rebuild` step 추가. `gh api --method POST "repos/${GH_REPO}/pages/builds"`, `GH_TOKEN`·`GH_REPO`는 env로 전달(토큰 값 저장·출력 없음). 종료 코드 2(데이터 손상)에서는 실행하지 않고, 정상/전체 실패(1)는 tests 성공 후 새 상태 JSON이 반영된 최신 master를 재빌드한다.
- 공식 근거: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site , https://docs.github.com/en/rest/pages/pages#request-a-github-pages-build
- 상태: 실제 Actions runner에서 성공한 적 없다. 권한·재빌드 검증은 root가 실제 실행으로 한다. 작은 workflow 변경이라 YAML 텍스트 재현 테스트는 추가하지 않았다.

### 2026-10-12 — 운영 시작 (실제 배포·첫 수집·공개 사이트 검증 완료)

- 병합: PR https://github.com/Haneul-two/ai-data-storage/pull/1 MERGED(2026-10-12T01:09:52Z), master merge `d01cbf3f52424a7c5c6a39b9e215b6e02ec7bfba`. PR 최신 `0fb77d6`의 Python/Node GitHub 검사 모두 성공, 병합 master Test run 38190817171 success. 로컬 병합 후 Python 97 / Node 106 통과. 원격 최신 `aa04b7e`의 기존 데이터 갱신 3건은 그대로 보존 병합.
- 활성화: 저장소 변수 `ENABLE_OPPORTUNITY_UPDATES=true` 실제 설정. cron `0 0 * * *` = 매일 09:00 KST. **첫 실행은 수동 `workflow_dispatch`이며 예약 시각에 자동 발생한 실행이 아니다.**
- 첫 운영 수집: https://github.com/Haneul-two/ai-data-storage/actions/runs/38190817956 success. collect/tests/commit/Request Pages rebuild 전부 success. GitHub token `pages: write`로 Pages API 재빌드가 실제 작동함을 확인(이전 '실행 검증 전' 항목의 미확인 해소).
- 데이터 커밋: `24278837f43816a68e6f6a8912911bc8cdf45d05`. Pages latest status `built`, 동일 commit. 최신 배포 run 38190931779 success. 중복 Pages 실행 38190931297은 cancelled이며 최종 성공 빌드가 있으므로 오류가 아니다.
- 운영 화면: updatedAt 2026-10-12T01:10:08Z(10:10:08 KST). 전체 39건 / 활성 27(모집중 25 + 예정 2) / 종료 8 / 마감 4 / stale 5. Devpost 6 · DACON 10 · 위비티 22 · AI Summit 1, 네 출처 모두 ok. 출처 itemCount에는 보존된 예전 항목도 포함된다. stale 5는 화면에서 출처 재확인 표시로 보인다.
- 공개 사이트 검사: `docs/evidence/deployment-check.json` 10/10, 콘솔 오류 0. 최신 dataset timestamp·items가 remote master와 일치, production에서 debug/now 무시, 검색 포커스, 저장 후 재접속, 상세 HTTPS 링크·포커스 복귀, 달력, 모바일 390 가로 넘침 없음.
- 캡처: `docs/evidence/deployed-desktop.png`(1440×900), `deployed-mobile.png`(390×844)를 root가 직접 열어 확인.
- 루트 코드리뷰 Pages 보완: 데이터 갱신 commit 뒤 legacy Pages 자동 빌드가 없다는 점을 리뷰에서 짚어 workflow에 `pages: write`와 `Request Pages rebuild` step을 넣었고, 위 첫 실행으로 작동을 확인했다.
- 보존: 초기 `4dedda4`/`0fb77d6` PR 브랜치와 원본 checkout은 삭제하지 않았다. 로컬 `feat/ai-opportunity-board`는 master 운영 데이터까지 fast-forward 동기화했다. `docs/tasks/`·`tools/run_claude.py`는 gitignore로 로컬 보관, 공개 제외.
- 미확인: 예약 시각(cron)에 자동 발생한 첫 실행, 배포·실기기 성능 측정.
- 규칙집 추가 없음.

## 2026-10-12 — 공식 AI 행사 3종과 위비티 다중 페이지 수집 (로컬 구현, 원격 반영 전)

- 계기: 사용자가 "AI 행사 수집 범위가 너무 작다. 2026 서초 AI 페스타, 엔비디아 AI 데이 서울 2026 등 주요 행사도 수집해달라"고 요청. 조사 중 위비티 AI 검색 2페이지 10번째의 고용24 국민참여 AI 고용서비스 발굴 온라인 해커톤(ix111124)을 놓친 것도 확인(1페이지만 보고 소스당 20건 상한이라서).
- 구현(브랜치 feat/expanded-opportunity-sources, 기준 master cc4353f): 소스 `seocho`·`nvidia`·`aifesta` 추가와 공용 `sources/jsonld.py`(서초·AI Festa 2곳이 공유), `urlsafe` 허용 호스트 정확 일치 추가, `rules` 행사 정규식에 페스타·축제·festa·festival·AI Day 보완(해커톤>공모전>행사 우선과 강좌/채용 제외 유지), 위비티 최대 6페이지·상세 100건(`wevity.item_limit`/`page_url`). 기존 소스 우선순위는 그대로 두고 새 3종을 뒤에 등록.
- 기존 테스트 변경 1건: `test_opportunities.py`의 위비티 `collect` 테스트가 2페이지를 요청하게 되어 빈 2페이지 fixture(`wevity_empty.html`)를 추가.
- 검증: 새 `tests/test_expanded_sources.py` 43개를 먼저 작성해 RED(38 실패, `expanded-red.txt`) → 구현 후 Python 140 OK · Node 106 pass · `--offline` 통과(`expanded-green.txt`). 실제 수집 1회(약 4분): 7개 출처 모두 ok, 전체 39→109건(기존 39건 전부 보존). 위비티 89건(6페이지, 후보 89건, 상세 실패 0), 서초 AI 페스타(2026-10-17, 무료, 시민 누구나, 마감 null, sourceStatus unknown), NVIDIA AI Day Seoul 2026(2026-11-09~10 코엑스, 등록 CTA로 open, 마감·참가비 확인 필요), AI FESTA 26(2026-10-06~08, 종료), 고용24 해커톤(마감 2026-10-13) 모두 포함.
- 설계 선택 이유: 서브 프로그램 "오픈예정/마감"이 축제 전체 닫힘으로 읽히지 않게 sourceStatus unknown·deadline null. NVIDIA는 프로그램 탭의 11월 10일 시간이 아니라 연도 포함 hero 한 줄만 기간으로 읽고 title 연도와 대조. 이후 페이지 오류는 부분 성공으로 숨기지 않고 소스 실패로 처리해 기존 데이터를 보존. 사양 `docs/collection-expansion.md` 점검: 자격 근거는 FAQ 페이지가 아니라 메인 본문의 "시민 누구나" 문구를 쓴 것만 정정.
- 미실행(root 몫): 브라우저 검사, 원격 push·배포, Codex 독립 교차 리뷰. 이 항목은 완료로 기록하지 않았다.
- 규칙집 추가: CLAUDE.md '사고에서 얻은 규칙'에 2줄(위비티 전용 한도, 공식 행사 서브 프로그램 상태).

### 2026-10-12 — 확장 수집기 Codex 독립 리뷰 보완 (로컬, root 재리뷰·브라우저·배포 대기)

- Codex 읽기 리뷰 결과: 핵심 구현과 실수집 7개 출처는 정상. 좁은 보완 3건만 지적돼 Claude가 수정.
- ① 한국어 검색: NVIDIA 항목에 '엔비디아'·'데이'가 없어 "엔비디아 AI 데이 서울 2026"로 못 찾음 → 공식 영문 제목은 유지하고 tags에 `엔비디아`·`AI 데이`·`서울` 추가(총 6개). 회귀: `tests/filters.test.mjs`가 수집 데이터의 NVIDIA 항목을 실제 `applyFilters`(kind:event)로 검색.
- ② NVIDIA dateNote의 '공식 hero 표기'는 구현 용어라 '공식 안내의 개최 일정 기준'으로 교체(파서·함수명·코드 주석은 그대로).
- ③ 서초 fixture의 EventScheduled를 EventCancelled로 바꾸면 미래 취소 행사가 sourceStatus unknown(예정)으로 남던 문제 → `jsonld.read_event`가 schema `eventStatus`의 EventCancelled만 읽어 `closed` + dateNote '행사 취소'. EventPostponed 등 다른 값과 하위 프로그램 상태는 전체 행사에 적용하지 않음. RED(취소 회귀 1건·NVIDIA 문구 검사 실패 확인) 후 GREEN.
- 데이터 반영: 전체 재수집(90개 위비티 등)을 피하고 seocho·nvidia·aifesta 3개만 해당 수집 모듈로 다시 읽어 기존 문서에 병합(다른 4개 출처·항목·상태 보존, 해당 3개 출처 status/itemCount/checkedAt만 갱신, 원자적 쓰기). 결과 109건, sources 7개 유지, itemCount 합 109 = items 109. 서초 AI 페스타는 현재 취소 아님(unknown 유지).
- 검증: Python 142 OK · Node 107 pass · `--offline` 통과(`docs/evidence/expanded-green.txt`).
- 미실행(root 몫): 수정분 재리뷰, 브라우저 검증, 원격 반영·배포. → 브라우저 검증은 아래에서 완료.

### 2026-10-12 — 확장 로컬 브라우저 검증 및 Codex 독립 리뷰 기록 (원격 반영 전)

- Codex 최신 실측: Python 142 OK · Node 107 pass · `collectors/collect_events.py --offline` 109건 계약 통과.
- `tools/check_expanded_events.py`(Codex 작성): 실제 Edge, 데스크톱 1440·모바일 390 각 4검사(서초·NVIDIA 한국어 검색 1건, 가로 넘침 없음, 고용24 해커톤) = 8검사 통과, pageErrors 0. 증거 `docs/evidence/expanded-local.json`·`expanded-local-1440.png`·`expanded-local-390.png`. 도구는 Claude가 독립 리뷰했고 중대한 결함이 없어 수정하지 않았다.
- 원격 push·배포·공개 URL 검사는 아직 진행하지 않았다. 성공으로 기록하지 않는다.
