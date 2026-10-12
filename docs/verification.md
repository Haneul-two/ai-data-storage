# 검증표 (frontend/backend 4대 축)

기준일 2026-10-02, 로컬 검증. 증거 원문은 `docs/evidence/final-checks.txt`, 브라우저 35개 항목은 `docs/evidence/browser-check.json`.
"통과"는 아래 증거로 관찰한 것만 쓴다. 원격(push·workflow 실행·Pages·예약)은 실행하지 않았다.

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
| 로직 | 통과 | 서울 날짜 환산·마감/개최 분리, 한국 참가 판정(표준 예외는 실제 국가 목록만 승인, `see rules` 거부), 초대 전용·비AI 제외. Python 97 OK |
| 신뢰성 | 부분 | 전체 실패 시 opportunities.json 바이트 불변·상태 파일 기록(`PipelineTest`), 손상 시 exit 2·원본 보존(`CliTest`). workflow 변경은 YAML 텍스트 회귀(`WorkflowTest`)로만 확인 |

## 확인 못 한 중요 항목

- 원격 Actions 실행(scheduled/dispatch)과 `continue-on-error`·`$GITHUB_OUTPUT` 동작: 러너에서 실행하지 않았다. 사람 승인 후 첫 실행에서 확인 필요.
- GitHub Pages 운영 동작과 `design-lab/` 노출: 배포하지 않았다.
- 원문 자격·일정의 정확성: DACON 자격은 `확인 필요`, 위비티 마감은 날짜만, Devpost 한국 참가는 문구 휴리스틱. 화면은 불확실성을 그대로 표시하지만 원문과 일치한다는 보증은 아니다.
- 위비티·DACON은 1페이지만 수집한다(그 밖 항목은 누락될 수 있음).
- 갱신 캡처 12개(after-desktop/mobile, detail-desktop, calendar-desktop/mobile, empty-desktop/mobile, error-desktop/mobile, loading-desktop/mobile, no-results-desktop)는 root가 직접 열어 확인을 마쳤다.
- 교차 리뷰는 작성자와 다른 모델로 완료: Claude 구현 → Codex 독립 리뷰(1·2차 반영), Codex 보조도구(browser_check/run_claude) → Claude 읽기 리뷰. 필수 리뷰 미완료 항목 없음.
- `tools/run_claude.py`의 `.cmd` 조건부 위험은 이 환경에 해당하지 않는다(`shutil.which('claude')`·`Get-Command` 모두 `C:/Users/caring/.local/bin/claude.EXE`). 내부 전용이며 사용자 승인 범위의 고정 명세 파일만 전달하고, 독립 읽기 호출은 `--read-only`.
