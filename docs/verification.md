# 검증표 (frontend/backend 4대 축)

기준일 2026-10-02 로컬 검증 + 2026-10-12 운영 확인. 증거 원문은 `docs/evidence/final-checks.txt`, 브라우저 35개 항목은 `docs/evidence/browser-check.json`.
"통과"는 아래 증거로 관찰한 것만 쓴다. 원격은 2026-10-12에 push·병합·수동 workflow 실행·Pages 배포를 실제로 확인했다(아래). 예약 시각에 자동 발생한 첫 실행은 아직 없어 통과로 쓰지 않는다.

## Frontend

| 축 | 판정 | 증거와 관찰 |
|---|---|---|
| UI | 통과 | 1440/390 캡처 `docs/evidence/after-desktop.png`·`after-mobile.png`. 320/375/390/414/768/1024/1440 가로 넘침 없음(`tools/browser_check.py` 항목). 색·간격은 `tokens.css` 토큰 |
| UX | 통과 | 상세 모달 Tab 포커스가 dialog 또는 BODY(브라우저 UI)에만 머물고 배경 요소로 새지 않음(브라우저 검사). 로딩/오류/빈/조건없음 4상태 캡처 존재 |
| State | 통과 | 로딩·오류 캡처(desktop·mobile)를 root가 직접 열어 '미수집' 알림 없음 확인. Node `tests/notices.test.mjs`: 로딩/오류에서 미수집 알림 없음·저장 경고 유지·ready 빈 상태에서만 표시 |
| 성능 | 로컬 통과 / 운영 미확인 | 로컬 1회 실측(Edge 신규 headless, Python HTTP server, 1440×900): navigation 436.8ms, 리소스 28개·128432 bytes, DOM 897개, 외부 리소스 0(`docs/evidence/codex-final-review.md`). 배포·실기기 성능은 미확인 |

## Backend/Data

| 축 | 판정 | 증거와 관찰 |
|---|---|---|
| 보안 | 통과 | 허용 호스트·HTTPS 443·userinfo 없음·redirect 재검증과 redirect 대상 robots 선검사(Python `FetcherTest`, `ReviewFixesTest`). 연락처 마스킹(`test_mask_contacts`). 원본 `events.json` 등 미수정. 계정/키 저장 없음 |
| 데이터 | 통과 | `--offline`: opportunities 33건·curated 0건 계약 통과. 4개 출처 실데이터 ok(devpost 6·dacon 11·wevity 15·aisummit 1). curated·신선 결과·저장 항목 모두 `meets_contract`(`SecondReviewTest`) |
| 로직 | 통과 | 서울 날짜 환산·마감/개최 분리, 한국 참가 판정(표준 예외는 실제 국가 목록만 승인, `see rules` 거부), 초대 전용·비AI 제외. Python 140 OK(확장 43 포함; 최신 142 OK는 아래 확장 항목, `docs/evidence/expanded-green.txt`) |
| 신뢰성 | 부분 | 전체 실패 시 opportunities.json 바이트 불변·상태 파일 기록(`PipelineTest`), 손상 시 exit 2·원본 보존(`CliTest`). workflow 변경은 YAML 텍스트 회귀(`WorkflowTest`)로만 확인 |

## 확인 못 한 중요 항목

- 원격 Actions: 수동 `workflow_dispatch` 첫 운영 수집(run 38190817956)에서 collect/tests/commit/Request Pages rebuild 전부 success, Pages API 재빌드 작동 확인(**확인함**). 단 **예약(cron) 시각에 자동 발생한 첫 실행은 미확인**이고 `continue-on-error` 실패 경로(종료 코드 1·2)도 러너에서 실행한 적 없다.
- GitHub Pages 운영: https://haneul-two.github.io/ai-data-storage/ 배포·정상 확인(**확인함**, 최신 빌드 built = 데이터 커밋 2427883). `design-lab/`는 root에 포함돼 URL을 알면 접근 가능하며 링크만 하지 않는다(배포 제외 아님).
- 공개 사이트 10/10 검사(`docs/evidence/deployment-check.json`, 콘솔 오류 0, 캡처 `deployed-desktop.png`·`deployed-mobile.png`)는 생성된 증거이며 이 목록의 미확인 항목(예약 첫 실행, 배포·실기기 성능 미측정, 원문 정확성, 실패 경로)까지 통과했다는 뜻이 아니다. 운영 수치: 전체 39 / 활성 27 / 종료 8 / 마감 4 / stale 5, 출처 4곳 ok.
- 원문 자격·일정의 정확성: DACON 자격은 `확인 필요`, 위비티 마감은 날짜만, Devpost 한국 참가는 문구 휴리스틱. 화면은 불확실성을 그대로 표시하지만 원문과 일치한다는 보증은 아니다.
- DACON은 1페이지만, 위비티는 최대 6페이지(후보 90건)까지 수집한다(그 밖 항목은 누락될 수 있음).
- 공식 행사 확장(2026-10-12, 로컬): 출처 7곳 수집 1회 모두 ok, 전체 109건(기존 39건 전부 보존; devpost 6·dacon 10·wevity 89·aisummit·seocho·nvidia·aifesta 각 1). 서초 AI 페스타·NVIDIA AI Day Seoul 2026·고용24 해커톤(ix111124) 포함, AI FESTA 26은 종료일 10-08로 저장. 증거 `docs/evidence/expanded-red.txt`(RED: 43개 중 38개 실패)·`expanded-green.txt`(Python 140·Node 106·offline 통과). 이후 Codex 독립 리뷰 보완(NVIDIA 한국어 태그, JSON-LD EventCancelled) 후 최신 실측: Python 142 OK · Node 107 pass · `--offline` 109건 계약 통과. 실제 Edge 로컬(`tools/check_expanded_events.py`, 데스크톱 1440·모바일 390 각 4검사 = 8검사 통과, pageErrors 0): 서초 AI 페스타·NVIDIA 한국어 검색 각 1건, 가로 넘침 없음, 고용24 해커톤 검색. 증거 `docs/evidence/expanded-local.json`·`expanded-local-1440.png`·`expanded-local-390.png`. **원격 반영·배포·공개 URL 검사는 아직 하지 않았다(성공으로 기록하지 않음).**
- 갱신 캡처 12개(after-desktop/mobile, detail-desktop, calendar-desktop/mobile, empty-desktop/mobile, error-desktop/mobile, loading-desktop/mobile, no-results-desktop)는 root가 직접 열어 확인을 마쳤다.
- 교차 리뷰는 작성자와 다른 모델로 완료: Claude 구현 → Codex 독립 리뷰(1·2차 반영), Codex 보조도구(browser_check/run_claude) → Claude 읽기 리뷰. 필수 리뷰 미완료 항목 없음.
- `tools/run_claude.py`의 `.cmd` 조건부 위험은 이 환경에 해당하지 않는다(`shutil.which('claude')`·`Get-Command` 모두 `C:/Users/caring/.local/bin/claude.EXE`). 내부 전용이며 사용자 승인 범위의 고정 명세 파일만 전달하고, 독립 읽기 호출은 `--read-only`.
- Codex 리뷰 보완(2026-10-12, 로컬): NVIDIA 한국어 검색 태그·dateNote 문구·JSON-LD EventCancelled→closed 반영. Python 142 · Node 107 · offline 통과, 3개 출처만 재확인 병합(109건, 출처 7곳 유지). **수정분 재리뷰·브라우저 검증·원격 반영은 root 몫으로 대기.**
- 확장 운영 반영 실측(2026-10-12, 공개): PR #2 병합(merge 04a31cd, Test 38208115198·Pages 38208115264 success), 운영 수동 update run 38208115725 success(data commit 5b822b9). 110건, **6출처 ok + aisummit error**(응답 2.5MB 상한 초과, 이전 1건·검증 시각 보존; 부분 실패로 기록하며 7출처 성공이 아님). 공개 보드 실Edge 1440/390 8검사 통과·pageErrors 0(`docs/evidence/expanded-public.json`·png). 종료 필터 2검사: AI FESTA 26 status closed 1건(종료 표시), status open 0건. 5b822b9의 Pages built 확인(builds/latest built, 공개 JSON updatedAt 2026-10-12T05:29:11Z·110건 일치, 공개 browser 8검사 재통과·pageErrors 0; `docs/evidence/expanded-deployment.json`). **예약 자동 실행은 미확인.** 위 '로컬 109건' 항목은 과거 로컬 기록으로 보존한다.
