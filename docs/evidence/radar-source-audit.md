# AI Radar 수집 출처 감사 (2026-10-12)

범위: 개인 참가 가능한 국내 + 한국 참가 가능 해외 온라인 AI 행사·공모전·해커톤, 공개 출처만, 로그인·차단 우회·유료 API 없음, 매일 갱신, 운영 LLM 토큰 0.
조사 방법: `ai-opportunity-board/1.0` UA로 robots.txt를 먼저 읽고, 허용되는 페이지만 1~3회 읽어 구조를 확인했다(예외 1건: 온오프믹스, 아래 표 참고). 검색 결과만으로 확정한 자료는 없다. 원본은 repo 밖 임시 폴더에서만 열었고 저장소에는 발췌 최소 fixture만 넣었다(연락처 없음).

## 0. 사양 독립 점검 (`docs/ai-radar-spec.md` 대비, 6건)

1. **수집 단계가 종료 항목을 계속 읽고 있었다.** 사양 P0은 closed/ended를 모든 화면에서 제외하는데, 위비티 90건 중 약 40건이 마감 행이었고 그 상세를 매일 조회했다(요청·시간 낭비, 목록 깊이 확장의 걸림돌). → 종료 라벨 행은 상세를 읽지 않고, 활성 후보가 없는 페이지에서 멈추게 했다.
2. **"수집 수보다 누락 발견"이라 했는데 누락 지점이 코드에 남아 있었다.** Devpost는 목록 총 23건(9건×3페이지)인데 1페이지·기본 10건만 읽어 14건이 보이지 않았다. → meta 총 건수 기반 페이지 읽기(최대 5페이지)와 기본 상한 20건.
3. **"연도 하드코딩 금지"와 조사 힌트 URL이 충돌한다.** `aisummit.co.kr/expo-visitor-2027`, AIoT `/2026/kor/`는 URL 자체에 연도가 있다. 힌트 URL을 쓰면 해마다 코드를 고쳐야 한다. → AI Summit은 연도 없는 메인 페이지를 유지, AIoT는 반려, AI EXPO는 연도 없는 `/전시회-개요/` 경로에서 연도를 페이지 표로 읽는다.
4. **aisummit 2.5MB 초과는 로컬에서 재현되지 않는다.** 로컬 실측 메인 페이지 586KB(gzip 112KB), 기간·장소는 앞 25~30% 안. 운영 환경에서만 2.5MB를 넘었으므로 원인(다른 응답 변형·인라인 데이터 등)은 확인하지 못했다. → 상한을 올리지 않고 앞 1MB만 읽는 선택 옵션을 추가했다(그 안에서 연도 포함 기간을 못 찾으면 추측하지 않고 오류). **운영에서 1회 실수집해 봐야 해소 여부를 알 수 있다.**
5. **출처 간 중복이 URL로만 걸러졌다.** 콘테스트코리아·Dev-Event·위비티·DACON은 같은 공모전을 서로 다른 주소(상세 페이지 vs 주최 링크)로 싣는다. 실측 시 콘테스트코리아 후보 54건 중 29건이 다른 출처와 같은 공모전이었다. → 제목(공백·기호 정규화) + 마감일(없으면 개최 시작일)이 같은 다른 출처 항목은 먼저 등록된 출처 하나만 남긴다. 앞의 `[..]` 표기는 그 항목의 주최명과 정확히 같을 때만 뗀다(`[Track1]`·`[Seoul]` 같은 의미 있는 태그는 보존 — 데이터 누락보다 중복 몇 건이 안전). 날짜가 없으면 합치지 않는다.
6. **"개인 참가"와 "한국 참가 가능"을 코드가 일부만 검증한다.** 해외 출처(Devpost)만 한국 허용 문구를 요구하고, 국내 출처는 응모 대상(콘테스트코리아·위비티) 원문을 그대로 두며 개인/팀/기업 구분 판정은 없다. 확인하지 못한 자격은 '확인 필요'(unverified)로 남기고 추정하지 않는다. 팀 전용·기업 전용 필터는 만들지 않았다(출처가 그 구분을 일관되게 주지 않는다).

## 1. 후보 조사표

| 후보 | 공식 URL | robots.txt | 결과 | 사유 / 실제 파싱 결과 |
|---|---|---|---|---|
| **콘테스트코리아** | https://www.contestkorea.com/sub/list.php (제목 검색 `Txt_key=str_meeting&Txt_word=AI`) | 200, `User-agent: *` `Allow:/` | **구현 `contestkorea`** | 서버 렌더링 GET. 12건/페이지, 최신 접수순. 목록=제목·상태 라벨·접수 MM.DD, 상세 표=접수기간(연도 포함)·참가대상·대회지역·시상·참가비·접수 링크. 활성(접수중/마감임박/접수예정) 후보는 12페이지 안에서 끝남(실측 11페이지에도 접수중 1건). 실측 후보 54건 → 반영 25건(29건은 다른 출처와 중복). 상세 오류 0건 |
| **Dev-Event** (brave-people/Dev-Event) | https://raw.githubusercontent.com/brave-people/Dev-Event/master/README.md (사람용: https://dev-event.vercel.app/events) | raw.githubusercontent.com 404(규칙 없음) | **구현 `devevent`** | 월별(`26년 10월`) 목록 한 번에 읽기, 약 120KB. 97항목 → AI 진행·예정 33건 → 중복 제거 후 24건. 접수 기간(MM. DD)·일시·분류(온/오프라인·무료/유료·세미나/대회/AI)·주최. 링크 대상(event-us·luma 등)은 허용목록 밖이라 읽지 않는다 |
| **AI EXPO KOREA** | https://aiexpo.co.kr/전시회-개요/ | 200, `/wp-admin/`만 차단 | **구현 `aiexpo`** | 개요 표(행사명·기간 `2027년 4월 14일(수) ~ 16일(금)`·장소 서울 COEX 1층 Hall A·주최). 연도는 페이지에서 읽음. 접수 마감·참가비·자격은 페이지에 없음 → 확인 필요. 페이지가 "B2B 전문 전시회"라고 밝힐 때만 노트에 옮김. `www.`는 301로 `aiexpo.co.kr`에 넘기므로 www는 허용하지 않음 |
| AI Summit Seoul & EXPO | https://www.aisummit.co.kr/ (힌트 `/expo-visitor-2027`) | 200, AI 학습 봇만 차단·`/api/` 등 일부 차단, `/` 허용 | 기존 `aisummit` 수정 | 힌트 페이지는 1.9MB로 메인(586KB)보다 크고 URL에 연도가 있어 대안이 아님. 메인 앞 1MB만 읽기로 변경(위 0-4). 로컬에서 2027.8.11~8.13 정상 파싱 |
| 씽굿 thinkcontest.com | https://www.thinkcontest.com/thinkgood/user/contest/index.do | 200, `User-agent: *` `Allow: /` (로그인·첨부 일부 차단) | **반려** | 공모전 목록이 JS 템플릿(`[[contest_pk]]`) 렌더링이고 목록 데이터 요청 주소가 HTML·공개 JS(sub/main/common.js)에 나오지 않는다. SSR에 있는 것은 배너 캐러셀 12건과 '이번 주 마감' 10건뿐. sitemap.xml은 2025-08~09 기준이라 낡음. 비공개 XHR을 추측해 부르지 않는다 |
| AI Factory aifactory.space | https://aifactory.space/ko/competition | 404(규칙 없음, Next.js 404 페이지) | **반려** | 목록은 SSR(633KB)이지만 112건이 모두 '종료'. `진행중/참가 접수중` 필터는 클라이언트에서만 동작(`?status=` 계열 쿼리 4종을 써 봐도 SSR 결과 동일). 활성 항목의 근거를 얻지 못함 |
| AIoT Korea | https://www.aiotkorea.or.kr/2026/kor/ | `/robots.txt` 404(규칙 없음) | **반려** | 경로에 연도(`2026`)가 들어 있어 연도 하드코딩 없이 찾을 수 없고, 본문이 JS 앱이라 SSR 텍스트에 기간이 없음. AI 전문 행사도 아님(AIoT) |
| 디지털 트윈 구룡포 AI 해커톤 | https://dtaiagent.imweb.me/ | 200, `/` 허용 | **반려** | 단일 행사 사이트. 지원서 제출은 2026.07.20~**09.13**(연장) 마감, 10/13은 오프라인 본선일이라 접수 마감이 아님(마감과 개최일 혼동 금지). 이미 접수 종료. 재사용 가능한 목록 구조도 없음 |
| daker.ai (데이콘 해커톤) | https://daker.ai/public/hackathons | 200, `/api/` 차단 | **반려** | 7.7KB SPA 껍데기. 데이터는 robots가 막은 `/api/`로만 제공. sitemap의 개별 슬러그 22건은 같은 껍데기를 돌려줌. 해당 대회는 콘테스트코리아·위비티·DACON·Dev-Event 경유로 이미 들어온다 |
| 온오프믹스 onoffmix.com | https://onoffmix.com/event/main/ | `User-agent: *` **Disallow: /** (검색엔진·일부 봇만 허용) | **반려(robots)** | 우리 UA는 허용 대상이 아니다. **조사 중 실수**: robots 전문을 끝까지 읽기 전에 목록 페이지를 1회 요청했다(robots는 앞부분만 보고 이어서 요청). 그 응답은 폐기했고 저장·구현에 쓰지 않았으며 이후 요청하지 않았다 |
| 이벤터스 event-us.kr | https://event-us.kr/ | 200, 일부 경로 차단 | **반려** | 홈이 Angular 템플릿(`{{ item.title }}`)이며 SSR 목록 없음 |
| lablab.ai | https://lablab.ai/ai-hackathons | 200, 목록 허용 | **반려** | SSR 목록에 일정은 있으나(`SEP 1 - DEC 1`) 연도·한국 참가 가능 여부 근거가 목록에 없고, 항목별 규칙 확인이 필요해 한국 참가 증거를 만들 수 없다 |
| AIcrowd / Zindi / Kaggle | aicrowd.com, zindi.world, kaggle.com | AIcrowd 허용, Zindi 301, Kaggle `/robots.txt` 404 | **반려** | 국가 자격 문구를 항목별로 읽어야 하는 글로벌 대회. 한국 참가 증거를 확보할 구조적 근거 없음(Devpost와 달리 일관된 자격 문구 없음) |
| 링커리어 linkareer.com | https://linkareer.com/list/contest | 200, 목록 허용 | **반려** | 목록(`__NEXT_DATA__`)이 이름·URL뿐이고 날짜·상태가 없으며 상세는 GraphQL 상태 의존. 같은 공모전은 콘테스트코리아·위비티가 이미 제공 |
| 에브리커리어(캠퍼스픽) | https://www.campuspick.com/contest | 200, `/contest` 허용 | **반려** | 20KB 정적 목록에 제목·주최만 있고 날짜·상태·상세 링크 없음 |
| KISTI AIDA 등 기관 개별 사이트 | aida.kisti.re.kr 등 | `/robots.txt` 302 | 미조사 | Dev-Event·콘테스트코리아가 이미 링크로 제공. 개별 기관 사이트를 늘리지 않음 |


## 2. 기존 목록 깊이 재검토

| 출처 | 이전 | 실측 | 변경 |
|---|---|---|---|
| 위비티 | 최대 6페이지·상세 100건, 종료 행도 상세 조회 | 15건/페이지 AI 후보. 1~3페이지 전부 접수중, 4페이지 접수중 8+종료 7, **5페이지부터 종료만**(12페이지까지 확인) | 종료 라벨 행은 상세를 읽지 않음. 목록은 등록순이라 마감 단조 정렬이 아니므로(1회 실측의 '5페이지부터 종료만'은 영구 중단 근거가 아님) 활성 후보가 없는 페이지에서 멈추지 않고, 빈 페이지·반복 페이지·상한(6페이지·100건)에서만 멈춘다. 상세 요청 약 89→53건 |
| Devpost | 1페이지 9건, 상세 기본 10건 | meta 총 23건=3페이지 | meta 기반으로 2~3페이지도 읽음(최대 5페이지, 상세 기본 20건). 한도를 채우면 다음 페이지를 읽지 않음. 이후 페이지 오류는 소스 실패 |
| DACON | 1페이지 SSR | 목록 14건(접수 1·연습 등 4·종료 9), '더보기'는 메뉴일 뿐 추가 로딩 아님 | 변경 없음(20건 상한 이내). 목록 구조가 한 페이지임을 확인 |
| 콘테스트코리아(신규) | — | 'AI' 검색 12페이지 안에 활성 끝, '인공지능' 검색은 활성 1건 | 'AI' 최대 12페이지 + '인공지능' 최대 3페이지, 상세 최대 60건, 빈/반복 페이지 또는 키워드별 페이지 상한에서만 정지(마감 여부로 뒷페이지 존재를 판정하지 않음) |
| 페이지 파라미터가 없는 출처 | seocho·nvidia·aifesta·aisummit·aiexpo | 단일 페이지 | 페이지 확장 없음 |

`--max-items`는 모든 목록형 소스(위비티·Devpost·콘테스트코리아·Dev-Event)에서 상세/항목 수 상한으로 동작한다(테스트 포함).

## 3. 상한과 실행 시간 예측

| 출처 | 목록 요청 최대 | 상세 요청 최대 | 이번 실측 |
|---|---|---|---|
| devpost | 5 | 20 | 3 + 15 |
| dacon | 1 | 20 | 1 + 14 |
| wevity | 6 | 100 | 5 + 53 |
| aisummit / seocho / nvidia / aifesta / aiexpo / devevent | 각 1 | 0 | 각 1 |
| contestkorea | 12 + 3 | 60 | 14 + 54 |
| robots.txt | 10호스트 | | 10 |

- 하드 상한 합계 약 250요청, 실측 257요청(robots·재시도 없음)에 4분 30초. 요청당 평균 약 1.05초(간격 1초 + 응답 지연).
- GitHub 러너는 지연이 더 클 수 있어 요청당 3초로 보수적으로 잡아도 하드 상한 250요청 = 약 12.5분이다. 이전 15분 job 한도는 여유가 부족하므로 job `timeout-minutes` 15→25, 수집 단계에 `timeout-minutes: 18`(job보다 짧게 두어 tests·commit·실패 표시 단계가 남도록)을 추가했다.

## 4. 변경한 수집 URL·허용 호스트

- 허용 호스트 추가(정확한 이름만, 와일드카드·하위 도메인 없음): `www.contestkorea.com`, `aiexpo.co.kr`, `raw.githubusercontent.com`.
- 새 요청 URL
  - `https://www.contestkorea.com/sub/list.php?displayrow=12&int_gbn=1&Txt_sGn=1&Txt_key=str_meeting&Txt_word={AI|인공지능}&Txt_sortkey=a.int_sort&Txt_sortword=desc&page={n}`
  - `https://www.contestkorea.com/sub/view.php?int_gbn=1&Txt_bcode={bcode}&str_no={no}`
  - `https://raw.githubusercontent.com/brave-people/Dev-Event/master/README.md`
  - `https://aiexpo.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ea%b0%9c%ec%9a%94/` (`/전시회-개요/`)
  - Devpost 목록 `...&page=2..5` (같은 API, page 파라미터만 변경)
- 변경된 기존 요청: `https://www.aisummit.co.kr/` 은 같은 URL이지만 앞 1MB까지만 읽음. 위비티 목록 URL은 같고 읽는 페이지 수·상세 대상이 줄었다.
- 외부 행사/신청 링크(event-us, luma, daker.ai, docs.google.com 등)는 저장만 하고 읽지 않는다.

## 5. 새 출처 데이터 계약 요약

- 콘테스트코리아: 접수기간은 상세의 연도 포함 `YYYY.MM.DD ~ YYYY.MM.DD`만 날짜로 쓴다. 날짜만 제공 → `deadlineAt` null. 목록 마감 MM.DD와 상세 마감이 다르거나, 접수중인데 마감이 이미 지났으면 그 항목을 쓰지 않고 실패로 센다(후보가 전부 그러하면 소스 오류). `심사기간`은 개최일이 아니므로 `startDate/endDate`는 null. 접수예정은 `sourceStatus: unknown` + 접수 시작일. 참가대상이 `해당자 ▶`뿐이면 자격 미확인. 접수 링크가 https가 아니면 상세 페이지를 `url`로 쓴다.
- Dev-Event: 접수 범위는 `registrationStartDate`/`deadlineDate`(날짜만, 원문 시각은 `dateNote`에만), 일시는 `startDate`/`endDate`. 연도는 월 섹션 제목에서 읽고 섹션 월에서 6개월 넘게 벗어난 월은 해를 넘긴 것으로 본다(`12. 20 ~ 01. 05` → 다음 해). 오늘(한국시간) 이전에 끝난 항목은 만들지 않는다. 일반 세미나·모임은 제목에도 AI 단어가 있어야 하고, 해커톤·대회는 AI 태그만으로 인정한다(클라우드·블록체인 모임에 붙은 AI 태그를 거르기 위함). 자격은 미확인.
- AI EXPO: 개최 기간만. 사전등록·참관 자격·참가비는 확인 필요.

## 6. 알려진 한계·미완료

- 예약 시각 자동 실행과 실제 운영 수집(`data/*.json` 갱신)은 이번 범위 밖(root가 1회 실행).
- aisummit 2.5MB 초과의 원인은 로컬에서 재현하지 못했다. 앞 1MB 읽기가 운영에서 통하는지는 실수집으로만 확인된다.
- Dev-Event는 커뮤니티가 큐레이션하는 목록이며 행사 원문은 읽지 않는다 → 날짜·참가비는 '디렉터리 표기'다(`dateNote`에 명시). 제목에 AI 단어가 없는 일반 세미나(예: Gemini·Copilot 행사)는 놓칠 수 있다.
- 콘테스트코리아·위비티의 응모 대상은 원문 표기 그대로이며 개인/팀/기업 구분은 하지 않는다.
- 다른 모델 교차 리뷰(Codex)는 이 세션에서 호출하지 못했다.

## 독립 리뷰 후 보완(Dev-Event·Fetcher)

- Dev-Event `sourceUrl`은 실제로 읽은 README의 월 섹션 anchor(`https://github.com/brave-people/Dev-Event#26년-11월`)이고, 행사별 landing 주소는 `url`에만 둔다.
- 오프라인 태그가 명시적 해외(미국·일본·샌프란시스코 등 `devevent._FOREIGN_PLACES`)이면 제외한다(온라인 병행이어도 한국 참가 확인 불가). 국내 지명 목록은 두지 않는다.
- 한국 장소 태그/국내 README 정책의 근거: 이 README는 한국 개발자 커뮤니티(brave-people)의 국내 행사 큐레이션이고 장소 태그가 `오프라인(서울 강남구)`처럼 국내 지명이다. 이번 보완에서 원문을 다시 수집해 확인하지는 않았고(전체 수집 금지), fixture와 이전 조사 기록에 근거한다. 해외 표기가 실제로 얼마나 있는지는 미실측이다.
- `Fetcher.get(prefix_bytes)`는 `1 <= prefix_bytes <= max_bytes`가 아니면 `ValueError`(요청 전). 상한 2.5MB 계약 유지.
