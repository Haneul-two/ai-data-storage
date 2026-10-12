# AI Radar 운영 상태 — 2026-10-12

기존 CLAUDE.md와 AGENTS.md의 작업 규칙을 먼저 읽고 적용한다. 이 파일은 배포 이후의 최신 상태를 기록한다.

- PR #3 병합으로 AI Radar 재설계·한국시간 신청 마감 제외·10출처 수집 확장을 공개 보드에 반영했다. https://haneul-two.github.io/ai-data-storage/.
- 수동 운영 수집 38218333647 성공, 데이터 커밋 e94ce06871b91f372319f8fe19e228575beca497 Pages built 확인. 현재 보관 165건·노출 118건·마감/종료 제외 47건이며 갱신과 날짜에 따라 달라진다.
- 검사: Python 228·Node 118·Edge UI 98 통과. 공개 데스크톱/모바일에서 독립 날짜 계산과 실제 노출 ID 일치, 한국어 행사 검색, 상세 Escape·포커스 복귀, 가로 넘침 없음, pageerror 0.
- AI Summit은 사용자 `너가 수정해줘` 승인으로 이번 오류만 Codex가 직접 수정했다. PR #4 병합, 운영 수집 38223091709 성공, 데이터 d2cece2 Pages built 일치. status=ok·verifiedAt=lastSuccessAt=2026-10-12T08:21:49Z, 공개 Edge 1440/390에서 AI Summit 실패 알림 없음·overflow 없음·pageerror 0. Python 229·Node 118 및 GPT-6 Astra 독립 리뷰 통과. 증거 `docs/evidence/aisummit-production.json`.
- 현재 AI EXPO만 robots.txt HTTP 202로 blocked이며 이전 데이터를 보존한다(다른 9출처 정상). 예약 cron 첫 실제 실행은 아직 미검증이다. 원래 파일 편집 역할 규칙은 이번 명시적 승인 범위 밖에서는 유지한다.
- Claude 세션 한도 전에 조기 마감 전파 코드까지 작성됐다. 이번에 새로 작성한 테스트 파일의 분류 코드 오타는 Codex가 수정했고 전체 회귀를 다시 통과했다. 조기 마감 전파가 미완료라는 중간 보고는 이후 검증으로 해결됐다.
- 최신 증거: docs/evidence/radar-production.json. 경과: docs/ai-radar-release.md. 기존 문서의 로컬 대기 상태는 이 배포 전 기록이다. 배포 이후 상태 동기화가 남았다는 중간 기록은 이 파일과 AGENTS.override.md의 최신 기록으로 해결됐다.

프로젝트 규칙 파일의 로드 근거: [Claude Code 공식 문서](https://code.claude.com/docs/en/memory#organize-rules-with-clauderules). 기존 규칙과 파일 편집 역할은 유지한다.
