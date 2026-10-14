# AI Radar 이름 정리안

2026-10-14 사용자 `이어서진행해줘` 승인으로 폴더·저장소·origin 이름 변경을 적용했다. 새 주소의 Pages 빌드와 공개 브라우저 검증도 같은 날 통과했다(아래 표·검증 단락).

| 항목 | 이전 | 현재 | 상태 |
|---|---|---|---|
| 활성 작업 폴더 | `C:/Users/caring/Projects/ai-data-storage-events` | `C:/Users/caring/Projects/ai-radar` | 완료 |
| GitHub 저장소 | `Haneul-two/ai-data-storage` | `Haneul-two/ai-radar` (기존 저장소 이름 변경, 새 저장소 아님) | 완료 |
| origin | `.../ai-data-storage.git` | `https://github.com/Haneul-two/ai-radar.git` (ls-remote master 791a56c 성공) | 완료 |
| homepage·description | 이전 이름 | `https://haneul-two.github.io/ai-radar/`, `AI Radar 국내참가AI행사공모전해커톤탐색` (GitHub PATCH 성공) | 완료 |
| Pages 설정 | — | API html_url이 새 주소, source master/root 유지 | 설정 확인 |
| 공개 사이트 `/ai-radar/` | `https://haneul-two.github.io/ai-data-storage/` | `https://haneul-two.github.io/ai-radar/` | **완료** — PR #6 병합 2cc8744 Pages built, 공개 JSON 로컬 일치, Edge 1440/390 통과 |
| 화면·브라우저 이름 | AI Radar | AI Radar | 변경 없음 |

**환경**: 기존 `.venv`는 `C:/Users/caring/Projects/_backups/ai-radar-venv-20261014`로 이동·보존했고(삭제 없음), 새 폴더 `.venv`를 동일한 13개 버전으로 복구했다. 새 경로에서 Python 3.11.15/pip 24 CLI가 동작하고 전체 Python 241·Node 118, 현재 데이터 175건의 offline 계약 검증을 통과했다. 원본 `AI-DATA-STORAGE` checkout은 건드리지 않고 보호한다.

**호환**: 화면 파일은 상대 경로, 갱신 workflow는 `github.repository` 동적 참조를 쓰므로 이름 변경에 대응한다. 이름 변경 전 기존 원격의 최신 자동 데이터 갱신은 보존 병합했다.

**주의**: 저장소 링크는 새 이름으로 연결되지만 GitHub Pages의 기존 사이트 주소(`/ai-data-storage/`)는 자동으로 연결되지 않는다 ([GitHub 공식 안내](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)). 이전 주소는 사용자가 북마크를 직접 갱신해야 하는 과거 URL이다.

**새 주소 검증(완료)**: PR #6 병합 2cc8744, 새 저장소 Test 38531497891·Pages 38531500212 success, Pages API built=2cc8744(중복 Pages 38531498169는 cancelled라 세지 않음). 2026-10-14T07:59:28Z `tools/check_naming_public.py` 통과 — 공개 JSON이 로컬 배포본과 일치(datasetUpdatedAt 2026-10-14T03:47:46Z, 보관 175·노출 118, 10출처 ok), Edge 1440/390 제목·브랜드 AI Radar, notice 없음, `AI EXPO` 검색에 기존 ID aiexpo-119c9024b15a 포함, overflow 0, pageerror/requestfailed 0. 증거 `docs/evidence/naming-production.json`·`naming-public-1440.png`·`naming-public-390.png`. 정상 서비스 표현은 이 검증 범위에 한한다.
