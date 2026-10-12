# 수집 소스 사실과 한계

기준일 2026-10-02 실측. 구현: `collectors/opportunities/sources/`. 실행: `.venv/Scripts/python.exe collectors/collect_events.py [--dry-run|--offline] [--output PATH] [--max-items N]`.

## 공통 정책

- User-Agent `ai-opportunity-board/1.0`. 위비티는 URL이 들어간 긴 UA를 403으로 거절한다(브라우저 흉내는 쓰지 않는다).
- 허용 호스트: devpost.com(*.devpost.com), wevity.com, dacon.io, aisummit.co.kr(각 www 포함). 모든 요청과 redirect는 HTTPS 443·userinfo 없음·허용목록을 재검증한다. redirect 3회, 응답 2.5MB, 요청 timeout 15초, 요청 간 1초.
- robots.txt는 호스트별로 실행 중 캐시한다. 404/410만 "규칙 없음"이고 timeout·403·5xx는 `blocked`다(허용으로 보지 않는다). 와일드카드(`*`, `$`)와 최장 일치를 직접 해석한다.
- 소스당 최대 20건(Devpost 기본 10건). 외부 신청 링크(위비티 홈페이지 필드)는 fetch하지 않고 안전한 HTTPS 링크로만 저장한다.
- 설명은 200자 이내 요약, 이메일·전화는 `[연락처 생략]`으로 치환한다. 연락처 섹션은 추출하지 않는다.

## Devpost (`devpost`)

- 목록 `https://devpost.com/api/hackathons?search=AI&status[]=open&challenge_type[]=online&page=1` → `{hackathons, meta}`. 구조가 다르면 오류, `hackathons: []`는 정상 0건.
- 필터: `themes`에 Machine Learning/AI, 위치 Online, `open_state=open`, `invite_only=false`. 통과분만 상세 1회 조회.
- 상세: `#eligibility-list`(연령·학생 조건 + 국가 문구, 제외 국가는 `span[title]` tooltip), `[data-iso-date]` 정확한 마감 시각, `meta[name=description]` 한 줄 소개.
- 한국 참가 근거(`rules.korea_allowed`): 전세계 문구 + 제외 목록이 South Korea/Republic of Korea/Korea/KR/한국을 금지하지 않음, 또는 제한 목록이 한국을 명시 포함. **North Korea 제외는 한국 제외가 아니다.** "excluding standard exceptions"만 있고 목록을 알 수 없으면 제외한다.
- 마감: 원문 시각(예 `2026-10-26T17:00:00-04:00`)을 `deadlineAt`에 그대로 두고 `deadlineDate`/`endDate`는 서울 날짜(10-27). `dateNote`에 원문 시간대 표기. 시작일은 목록 `submission_period_dates`.
- 참가비는 출처에서 확인하지 않아 `확인 필요`. 상금 `$0`은 null.

## DACON (`dacon`)

- `https://dacon.io/competitions`(SSR)의 `.official-comp` 안 `a[href*="/competitions/official/"]`, 제목 `.name`, 태그 `.keyword`, 상태 `.dday`(참가신청중→open, 마감→closed, 그 외(연습 등)→unknown).
- AI 관련 제목/태그만 최대 20건(open → unknown → closed 순, 목록의 최신순 유지). 각 `/overview/` 상세 조회.
- 상세 inline script `window.__NUXT__=(function...` 은 **실행하지 않고** `competitionDetail` 이후의 따옴표 문자열 필드(`period_start`, `period_end`, `submission_end`, `prize_info`)만 정규식+JSON 문자열 디코드로 읽는다. 변수 참조(`description:k` 등)는 읽을 수 없어 설명은 키워드 요약으로 대체.
- `submission_end`(제출 마감) → `deadlineAt` `+09:00`. `merge_deadline`은 팀 병합 마감이라 쓰지 않는다. `period_start/end`는 대회 기간이며 접수 시작일로 추정하지 않는다. `submission_end`가 시작일보다 앞서는 원문 모순(실제 관측: SW부문 2025-07-15)은 마감으로 쓰지 않고 null.
- 참가 자격은 확인 불가 → `확인 필요`(verified=false). 방식: 제목의 오프라인/온라인, 키워드 `코드 제출`이면 online, 나머지 unknown. `채용` 태그만으로 해커톤을 제외하지 않는다(제목 기준 부트캠프·강의·채용공고만 제외).

## 위비티 (`wevity`)

- 검색은 반드시 `sp=name`(또는 `sp=contents`)이 있어야 필터가 적용된다: `https://www.wevity.com/?c=find&s=1&gub=1&sp=name&sw=AI`. 행 `.list li`(헤더 `li.top`), 제목 `.tit a[href*="gbn=view"]`, `.organ`, `.day .dday`.
- 제목을 로컬에서 다시 AI 단어 경계로 걸러 상세 `?c=find&s=1&gub=1&gbn=view&ix=ID`를 조회한다. 상세 `ul.cd-info-list`: 응모대상, 주최/주관, 접수기간(`시작 ~ 마감`), 총 상금/1등 상금, 홈페이지.
- 접수기간 마감은 날짜만 제공 → `deadlineAt` null, `dateNote`에 날짜만 제공 명시. 개최일은 제공되지 않아 start/endDate null. 응모대상이 있으면 그대로 저장(원문 표기, "기타"·"제한없음" 포함).
- 한계: 다수가 AI 영상/이미지 공모전이다(제목에 AI 포함). 방식은 제목에 온라인/오프라인이 있을 때만 판정.

## AI Summit Seoul (`aisummit`)

- 공식 행사 단일 페이지 어댑터. 현재 페이지는 **2027.8.11(수) - 8.13(금)** 을 노출하지만 `<title>`은 2026 표기다. 본문 `YYYY.M.D(요일) - M.D` 표기와 `컨퍼런스/EXPO YYYY년 M월 D-D일` 표기만 신뢰하고, 서로 연도가 다르거나 읽지 못하면 오류. 제목 연도가 다르면 소스 메시지에 경고.
- 컨퍼런스 8/11-12, EXPO 8/11-13, 코엑스, 주최 DMK Global/COEX/KITA. 마감·참가비·자격은 확인 필요(추측하지 않음). 푸터/연락처 텍스트는 저장하지 않고 설명은 구조화 필드로 합성.
- `aisummit.co.kr/robots.txt`는 `/api/`, `/search`, `?format=` 계열 등을 막지만 `/`는 허용한다.

## 저장·병합 규칙

- 전체 원격 실패 시 `data/opportunities.json`은 바이트 불변이고 `data/ingest-status.json`만 갱신된다. 부분 실패는 성공 소스만 교체하고 실패 소스 행·`verifiedAt`·`lastSuccessAt`을 보존한다.
- 성공 소스에서 사라진 활성 항목은 `stale=true`(verifiedAt 유지), 종료 후 90일이 지난 항목만 제외한다. 날짜가 없는 항목은 verifiedAt 기준.
- id = `소스id-sha1(canonical sourceUrl)[:12]`. 서로 다른 소스가 같은 canonical `url`을 가리키면 소스 우선순위(devpost > dacon > wevity > aisummit)로 한 건만 남긴다.
- 기존 JSON이 손상됐거나 계약을 어기면 종료 코드 2로 중단하고 어떤 파일도 쓰지 않는다. 종료 코드 1은 모든 소스 실패.
- `data/curated.json`(수동 입력, `schemaVersion: 2`, 전체 항목 계약)은 현재 비어 있다. 값이 있으면 검증 후 병합하며 자동 재확인은 하지 않는다(각 항목의 `verifiedAt`이 입력 시점). 기존 `data/events.json`은 건드리지 않는다.

## 파이프라인 계약(2차 리뷰 보완 포함)

- 모든 신선한 소스 결과와 `curated.json` 항목은 같은 계약(`rules.meets_contract`)을 통과해야 한다: AI 관련성, 지역(KR 또는 GLOBAL+online), 자격 확인(GLOBAL은 `eligibilityVerified`와 한국 참가 증거), 초대 전용 제외. 신선한 결과는 위반 항목만 건너뛰고 메시지에 "계약 위반으로 N건 제외"를 남기며, curated 위반은 `ExistingDataError`로 중단(원본 보존). curated 파일이 없거나 비어 있으면 정상이다.
- 저장된 stale 항목도 병합 때 같은 계약을 다시 검사해 위반분은 출력에서 뺀다(예: 나중에 추가된 internal 대회 규칙).
- "excluding standard exceptions"는 **괄호 안에 실제 국가명 목록**(예: Brazil, Crimea, Cuba, Iran, North Korea, Quebec, Russia)이 있을 때만 승인한다. `(see rules)`·TBD·빈 괄호는 거부한다.
- Fetcher는 redirect 대상의 robots.txt를 **요청 전에** 검사한다(중간 redirect 포함).
- 위비티·DACON은 시간·요청 한도 때문에 목록 **1페이지만** 본다.
- Devpost 상세 한국 참가 문구와 위비티 응모대상은 원문을 그대로 보여주며, 원문이 바뀌면 안전하게 제외 쪽으로 동작한다.
- workflow Actions 버전은 2026-10-02에 직접 조회한 최신 릴리스 기준이다: [actions/checkout v7.0.1](https://github.com/actions/checkout/releases), [actions/setup-python v7.0.0](https://github.com/actions/setup-python/releases), [actions/setup-node v7.0.0](https://github.com/actions/setup-node/releases) (workflow에는 major `@v7`로 고정).

## 알려진 한계

- 시간·요청 한도 때문에 위비티/DACON은 1페이지만 본다(위비티 검색 결과 15건, DACON 목록 14건 수준).
- Devpost 한국 참가 판정은 상세 페이지의 문구 휴리스틱이다. 문구가 바뀌면 안전하게 제외 쪽으로 동작한다.
- 온오프믹스는 일반 UA 자동 수집을 금지해 제외했다.
