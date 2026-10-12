# 공개 기회 수집 파이프라인

상위 계약: `spec.md`. 신규 `collectors/opportunities/`에 source parser, 검증/정규화, 저장/CLI 책임을 분리한다. 기존 `collectors/collect_events.py`는 신규 CLI로 이어지는 얇은 entrypoint로 Claude가 교체한다.

- 실제 확인 가능한 Devpost와 국내 공개 소스를 수집한다. 소스당 최대20개, HTTP timeout15s, 명시 User-agent, robots 확인·캐시, 요청 간격1s. 허용 호스트(devpost.com·*.devpost.com, www.wevity.com/wevity.com, dacon.io/www.dacon.io, 공식행사 adapter 사용 시 www.aisummit.co.kr/aisummit.co.kr)만 fetch한다. 주소 자체의 공인 HTTPS hostname+port443+userinfo 없음을 검증하고 redirect도 같은 정책이다. 외부 apply URL은 fetch하지 않고 HTTPS 안전 링크로만 보일 수 있다. parser 구조 미확인 소스는 error/blocked로 기록하며, P0는 실제 국내 소스 1개 이상과 Devpost만 연결한다.
- Devpost `/api/hackathons?search=AI&status[]=open&challenge_type[]=online&page=1`: `hackathons`, `meta`; title, displayed_location.location, themes[].name, submission_period_dates, organization_name, prize_amount, url. 온라인+Machine Learning/AI 필터 이후 상세 공개 페이지에서 한국 참가 허용 증거(country 문구가 All countries/territories 또는 worldwide/open globally이고 tooltip/본문 제외 국가 목록이 South Korea/Republic of Korea/Korea(North Korea 제외)/KR을 금지하지 않음, 또는 제한 목록이 한국/대한민국/South Korea/Republic of Korea를 명시 포함)와 정밀 deadline을 확인한다. invite_only 또는 제한 자격은 제외한다.
- 위비티 `https://www.wevity.com/?c=find&s=1&gub=1&sw=AI`, 데이콘 `https://dacon.io/competitions`는 200 실측, robots 일반 읽기 허용. 실제 card/상세 구조를 확인한 뒤 parser fixture를 고정한다.
- AI/인공지능/머신러닝/딥러닝/LLM/생성형 모델 관련 키워드는 제목·핵심 소개·태그에서 검증한다. 일반 사이트 header/footer의 AI 단어 때문에 전 항목을 포함하지 않는다. `chair`, `paid`, `Thailand`처럼 부분문자열 ai는 일치하지 않는다.
- 해커톤 우선 → 공모전/경진대회 → 일회성 행사(컨퍼런스/박람회/세미나/밋업). 부트캠프·정규 강의·채용·제품/뉴스는 제외한다.
- 해외 offline/hybrid 또는 한국 참가 근거 미확인 항목은 제외. 국내의 자격 제한은 그대로 표시하며 eligibilityVerified=false는 '참가 조건 확인 필요'로 보일 수 있다. 해외는 verified false 자동 포함 금지. 연령/학생 조건은 보존한다. 모집 대상이 전세계 학생이면 학생 조건을 보존한다.
- sourceUrl 기준 stable id, canonical URL 중복 제거. 입력 schemaVersion2와 날짜/URL 불변식을 검증한다. 연락처를 마스킹하고 설명은 짧은 사실 요약으로 저장한다.
- `data/curated.json`은 명시 출처와 조회 근거를 가진 수동 입력. 오래된 `events.json`은 읽기 전용이며 자동으로 날짜를 바꾸지 않는다.
- 모든 원격 소스 실패 시 opportunities.json은 바이트 단위 불변이다. 매 시도 상태는 별도 `data/ingest-status.json`(`{lastAttemptAt, sources: Source[]}`)에 원자적으로 기록하고 UI loader가 opportunities.sources에 id 기준 overlay한다. 부분 실패는 성공 소스를 교체하고 실패 소스의 항목/verifiedAt을 보존한다. archived 성공 소스의 이전 항목은 90일간 제목·날짜 변형 없이 유지한다. 성공 소스에서 사라진 활성 항목은 stale=true로 유지('출처 재확인 필요' 표시), 90일 지난 종료 항목만 결과에서 제외한다. 파일 삭제는 없다. 원자적 저장은 검증 완료 후 replace.
- fixtures는 최소 필요한 public markup만 담고 capturedAt/URL 주석과 synthetic 추가분을 둔다. raw 전체 페이지 저장 금지, 연락처는 마스킹한다. JSON 손상은 무시하지 않고 실패로 종료한다.
- CLI는 `--dry-run`(실제 조회하지만 데이터 파일 수정 없음), `--output`(결과 저장 경로), `--offline`(fixture/curated 검증) 제공. `--dry-run` 검증과 운영 성공을 구분한다.
- 하루1회 workflow 초안은 repository variable `ENABLE_OPPORTUNITY_UPDATES == 'true'`일 때만 수집·커밋·푸시 가능. 기본 미설정은 비활성. 승인 전 변수를 바꾸거나 원격 workflow를 실행하지 않는다.
- 의미 있는 RED→GREEN 테스트 증거: 관련성/유형/날짜/자격, 파싱, robots 차단, URL validation, 원본 보존·부분 실패·전체 실패, 동일 입력 중복 없음.
