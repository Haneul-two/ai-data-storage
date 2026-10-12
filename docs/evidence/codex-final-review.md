# Codex 최종 확인 — 2026-10-02 17:20 KST

Claude가 구현한 코드에 Codex가 자기완결적 사양을 기준으로 독립 리뷰했다. 1차 7개 범위의 보완과 2차 4개 지적을 Claude가 수정했고, 아래 실행 검증을 Codex가 새로 수행했다. Codex가 작성한 browser_check.py와 run_claude.py는 Claude가 읽기 리뷰했다. 제품 구현자와 리뷰 모델이 다르다.

| 검증 | 실제 결과 |
|---|---|
| Python unittest discover | 97개 OK, exit0 |
| Node --test --test-reporter=dot | 106개, exit0 |
| collect_events.py --offline | opportunities 33, curated 0, 계약 통과 |
| browser_check.py | 35/35, 콘솔 오류0, exit0 |
| 모든 항목 meets_contract | True |
| 저장 문자열 연락처 마스킹 누락 | 0개 |
| git diff --check | exit0, 공백 오류 없음; Windows LF/CRLF 알림만 존재 |
| 원본 데이터 tracked diff | 없음 |
| 기존 별도 checkout | 기존 CLAUDE.md 변경만 남아 있음 |

현재 전체 33건. 화면 활성 필터는 23건(모집중21 + 예정2), 종료9 + 마감1은 기본 목록에서 제외되고 마감·종료 필터로 확인한다. '종료일 기준 아직 끝나지 않음24'는 활성 필터 수가 아니다.

루트가 갱신된 캡처를 실제로 열었다: after-desktop(1440×900), after-mobile(390×844), detail-desktop, calendar-desktop/mobile, empty-desktop/mobile, error-desktop/mobile, loading-desktop/mobile, no-results-desktop. 잘못된 '미수집' 경고는 로딩·오류에서 사라졌고 내부 전용 AIC 항목은 목록/마감 임박에서 제외됐다. 320/375/390/414/768/1024/1440 CSS 너비 가로 넘침 없음은 browser-check.json에 기록돼 있다. 원격에 준하는 hostname localhost.에서는 debug/now가 무시되고 정상 실데이터가 표시됐다. 실제 외부 Pages 확인은 하지 않았다.

보조 실행기 리뷰의 Windows .cmd 위험은 이 환경에서 적용되지 않는다: Python shutil.which와 PowerShell Get-Command 모두 C:/Users/caring/.local/bin/claude.EXE를 확인했다. 쓰기 도구 허용은 사용자에게 승인된 Claude 구현용 내부 명세에서만 사용하며, 읽기 리뷰 호출은 --read-only를 사용했다. 외부 입력을 받는 서비스가 아니다.

로컬 성능 1회 실측(설치된 Edge 신규 headless 프로필, Python HTTP server, 1440×900): navigation duration 436.8ms, 리소스 본문 128432 bytes, 리소스28개, 렌더 후 DOM897개. 요청은 로컬 정적 CSS/ES modules와 신규 JSON2개뿐이며 외부 폰트/이미지/기존 카테고리 데이터 요청은 없다. 네트워크/실기기/원격 성능 보장은 아니며 실제 Pages 성능은 배포 후 확인한다.

원격 push/배포/스케줄 활성화/Actions runner 실행은 미실행. workflow는 코드와 회귀만 확인했다. 위비티·DACON은 첫 페이지와 요청 상한, Devpost는 원문의 자격 문구, 국내 상세 정보 미확인은 화면에 확인 필요로 표시한다. 규칙집 추가 없음: 일반화할 수정은 최종 코드와 회귀 테스트에 이미 드러난다.
