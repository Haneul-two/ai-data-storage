# AI Radar — 최신 운영 상태

작업 전에 [AGENTS.md](AGENTS.md)와 [CLAUDE.md](CLAUDE.md)를 읽고 기존 작업 규칙을 적용한다. 이 보완 파일은 운영 상태와 검증 시점을 갱신한다. 기존 파일 편집은 Claude, 새 파일 작성·조사·검증은 Codex라는 사용자 규칙도 그대로 적용한다.

- 2026-10-12: AI Radar 재설계·신청 마감 제외·10개 출처 확장을 **운영 반영했다**. PR #3 병합, 공개 사이트 https://haneul-two.github.io/ai-data-storage/.
- Python 228개·Node 118개·실제 Edge UI 98개 통과. GPT 6.1 SOL(max) 디자인 조사·리뷰, Claude 구현, Codex 독립 코드·화면 검증 완료.
- 수동 운영 수집 run 38218333647 성공. 데이터 커밋 e94ce06871b91f372319f8fe19e228575beca497과 Pages built 일치. 보관 165건, 공개 노출 118건(공모전 82·행사 22·해커톤 14), 마감·종료 47건 제외. 수치는 날짜와 갱신에 따라 변한다.
- 9개 출처 정상, AI Summit은 GitHub 환경에서 기간 파싱 오류로 이전 항목 1건·검증 시각을 보존한다. 이 출처의 운영 파서는 후속 보완 대상이다. 자동 cron 첫 실행은 아직 검증하지 않았다.
- 최신 운영 증거는 [radar-production.json](docs/evidence/radar-production.json), 반영 경과는 [ai-radar-release.md](docs/ai-radar-release.md)다. 기본 지시문서에 남은 '로컬 대기'는 이 배포 전 기록이다. 배포 이후의 운영 상태 동기화는 이 보완 기록과 Claude 프로젝트 규칙 파일로 완료했다.
- 최신 UI 검사: `.venv/Scripts/python.exe tools/check_radar_ui.py`. 옛 `browser_check.py`는 이전 화면용 역사적 검사다.

상태 보완 파일의 로드 근거: [OpenAI 공식 지침](https://learn.chatgpt.com/docs/agent-configuration/agents-md). 기존 지시파일의 사용 규칙은 위 링크 파일에서 읽는다.
