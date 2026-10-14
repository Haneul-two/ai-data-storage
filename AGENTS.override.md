# AI Radar — 최신 운영 상태

작업 전에 [AGENTS.md](AGENTS.md)와 [CLAUDE.md](CLAUDE.md)를 읽고 기존 작업 규칙을 적용한다. 이 보완 파일은 운영 상태와 검증 시점을 갱신한다. 기존 파일 편집은 Claude, 새 파일 작성·조사·검증은 Codex라는 사용자 규칙은 유지하며, 이번 AI Summit·AI EXPO 갱신 오류 수정은 사용자 `너가 수정해줘` 승인과 후속 진행 요청으로 Codex가 직접 편집했다.

- 2026-10-14 이름 정리 **완료(폴더·저장소·origin)**: 활성 폴더 `C:/Users/caring/Projects/ai-radar`, 저장소 `Haneul-two/ai-radar`(기존 저장소 이름 변경, homepage·description 갱신), origin `https://github.com/Haneul-two/ai-radar.git`(ls-remote master 791a56c 성공), 공개 URL https://haneul-two.github.io/ai-radar/. 기존 `.venv`는 `C:/Users/caring/Projects/_backups/ai-radar-venv-20261014`에 보존하고 새 `.venv`를 동일 13개 버전으로 복구했다(Python 241·Node 118·현재 데이터 175건 offline 통과). 원본 `AI-DATA-STORAGE` checkout은 보호한다. **새 주소의 Pages 빌드·브라우저 검증은 아직 후속**이며 그 전에는 새 URL 정상 서비스를 단정하지 않는다. 아래 과거 URL·검증 사실은 역사적 기록이다.
- 2026-10-12: AI Radar 재설계·신청 마감 제외·10개 출처 확장을 **운영 반영했다**. PR #3 병합, 공개 사이트 https://haneul-two.github.io/ai-data-storage/.
- Python 228개·Node 118개·실제 Edge UI 98개 통과. GPT 6.1 SOL(max) 디자인 조사·리뷰, Claude 구현, Codex 독립 코드·화면 검증 완료.
- 수동 운영 수집 run 38218333647 성공. 데이터 커밋 e94ce06871b91f372319f8fe19e228575beca497과 Pages built 일치. 보관 165건, 공개 노출 118건(공모전 82·행사 22·해커톤 14), 마감·종료 47건 제외. 수치는 날짜와 갱신에 따라 변한다.
- AI Summit 오류는 PR #4로 해결했다. 운영 수집 38223091709 성공, 데이터 커밋 d2cece2와 Pages built 일치. 이 출처 status=ok, 항목 verifiedAt=lastSuccessAt=2026-10-12T08:21:49Z. 공개 Edge 1440/390에서 AI Summit 실패 알림 없음·overflow 없음·pageerror 0 확인. Python 229·Node 118 통과, GPT-6 Astra 독립 리뷰 통과. 증거 `docs/evidence/aisummit-production.json`.
- AI EXPO 오류는 PR #5로 보완했다. HTTP 조회 실패 시 독립 SHOWALA 공개 기록을 동일 행사 검증 후 사용하며 실제 출처와 기존 ID를 보존한다. 운영 run 38262223254 성공, 데이터 0fa3c6e Pages built 일치, AI EXPO status=ok·verifiedAt=lastSuccessAt=2026-10-12T14:20:56Z. 공개 Edge 1440/390에서 모든 출처 실패 알림 없음·overflow 없음·pageerror 0. Python 241·Node 118 및 GPT-6 SOL/Claude 정적 리뷰 통과. 증거 `docs/evidence/aiexpo-production.json`.
- 현재 10개 출처 모두 정상, 보관 169건·공개 122건(2026-10-12 23:26 KST 확인, 날짜에 따라 변함). 예약 실행은 확인됐다: run 38352906516(2026-10-13T05:44:01Z)·38508066853(2026-10-14T03:47:32Z) 모두 event=schedule·conclusion=success. cron 설정은 UTC 00:00(KST 09:00)이나 실제 실행은 위 시각이므로 정시 실행이라고 단정하지 않는다. SHOWALA 대체 기록이 종료되거나 다른 회차로 바뀌면 안전하게 실패하므로 해당 등록 경로를 재검토한다.
- 최신 출처 복구 증거는 [aiexpo-production.json](docs/evidence/aiexpo-production.json), 반영 경과는 [HISTORY.md](docs/HISTORY.md)다. 이전 radar-production.json·ai-radar-release.md와 기본 지시문서의 '로컬 대기'는 과거 기록이다. 2026-10-13 10:04 KST 공개 재확인에서도 10개 출처 ok·PC/모바일 실패 알림 없음.
- 최신 UI 검사: `.venv/Scripts/python.exe tools/check_radar_ui.py`. 옛 `browser_check.py`는 이전 화면용 역사적 검사다.

상태 보완 파일의 로드 근거: [OpenAI 공식 지침](https://learn.chatgpt.com/docs/agent-configuration/agents-md). 기존 지시파일의 사용 규칙은 위 링크 파일에서 읽는다.
