"""Dev-Event(brave-people/Dev-Event) 공개 README: 월별(`26년 10월`) 개발자 행사·대회 목록을 한 번에 읽는다.
각 항목은 제목+링크, 분류(온·오프라인/무료·유료/세미나·대회/AI), 주최, 접수 기간(MM. DD) 또는 일시로 이루어진다.
연도는 항목에 없고 월 섹션 제목에서 읽는다. 링크 대상(event-us, luma 등)은 허용목록 밖이라 읽지 않고 링크로만 저장한다.
sourceUrl은 실제로 읽은 README의 월 섹션 anchor이고, 행사별 landing 주소는 url에만 둔다(읽지 않은 페이지를 출처로 표기하지 않는다).
접수 시각은 원문에 있어도 마감 시각으로 단정하지 않고 날짜만 쓴다."""
import re

from .. import rules
from ..errors import StructureError
from ..urlsafe import is_safe_https_url
from .base import CollectResult, domestic_region

SOURCE_ID = "devevent"
SOURCE_NAME = "Dev-Event"
SOURCE_URL = "https://github.com/brave-people/Dev-Event"
README_URL = "https://raw.githubusercontent.com/brave-people/Dev-Event/master/README.md"
_SECTION_RE = re.compile(r"^##\s*`(\d{2})년\s*(\d{1,2})월`\s*$")
_ITEM_RE = re.compile(r"^-\s+__\[(.+)\]\((\S+?)\)__\s*$")
_FIELD_RE = re.compile(r"^\s+-\s+(분류|주최|접수|일시):\s*(.*?)\s*$")
_MD = r"(\d{1,2})\.\s*(\d{1,2})\([^)]*\)(?:\s+\d{1,2}:\d{2})?"
_SPAN_RE = re.compile(rf"^{_MD}(?:\s*~\s*{_MD})?$")
_PLAIN_TAGS = {"AI", "온라인", "무료", "유료"}
# 오프라인 장소 태그가 명시적으로 해외인 행사는 한국 참가 가능 여부를 확인할 수 없어 제외한다(국내 지명 목록은 두지 않고 해외만 거른다)
_FOREIGN_PLACES = ("해외", "미국", "일본", "중국", "대만", "홍콩", "싱가포르", "싱가폴", "베트남", "태국", "인도", "인도네시아", "필리핀", "말레이시아",
                   "영국", "독일", "프랑스", "캐나다", "호주", "유럽", "두바이", "샌프란시스코", "실리콘밸리", "라스베이거스", "뉴욕", "시애틀",
                   "로스앤젤레스", "도쿄", "오사카", "베이징", "상하이", "런던", "파리", "베를린", "바르셀로나")
ITEM_LIMIT = 100  # 한 번에 읽는 README에서 쓰는 항목 하드 상한. --max-items가 더 작으면 그 값


def parse_readme(text):
    """월 섹션 항목 목록. 지난 행사 기록처럼 월 섹션이 아닌 `##` 제목을 만나면 거기서 끝낸다."""
    entries, section, current = [], None, None
    for line in text.splitlines():
        m = _SECTION_RE.match(line)
        if m:
            if not 1 <= int(m[2]) <= 12:
                raise StructureError(f"Dev-Event 월 섹션 제목의 월이 올바르지 않음: {line.strip()}")
            section, current = (2000 + int(m[1]), int(m[2])), None
            continue
        if line.startswith("## "):
            if section is not None:
                break
            continue
        if section is None:
            continue
        item = _ITEM_RE.match(line)
        if item:
            current = {"year": section[0], "month": section[1], "title": rules.clean_text(item[1]), "url": item[2], "tags": [], "organizer": None, "when": None}
            entries.append(current)
            continue
        field = _FIELD_RE.match(line)
        if field and current is not None:
            label, value = field[1], field[2]
            if label == "분류":
                current["tags"] = re.findall(r"`([^`]+)`", value)
            elif label == "주최":
                current["organizer"] = rules.clean_text(value) or None
            else:
                current["when"] = (label, value)
    if section is None:
        raise StructureError("Dev-Event README에 월별 섹션(`YY년 M월`)이 없음")
    if not entries:
        raise StructureError("Dev-Event 월별 섹션에 항목이 없음")
    if not any(e["when"] for e in entries):
        raise StructureError("Dev-Event 항목에서 접수/일시 줄을 하나도 읽지 못함")
    return entries


def _year_near(month, year, section_month):
    """섹션 월에서 6개월 넘게 벗어난 월은 해를 넘긴 것으로 본다(12월 섹션의 01. 05 → 다음 해)."""
    if month < section_month - 6:
        return year + 1
    if month > section_month + 6:
        return year - 1
    return year


def _date(year, month, day):
    return rules.parse_date(f"{year}-{month}-{day}")


def resolve_dates(entry):
    """(kind, start, end) 날짜 문자열. 접수는 (접수 시작|None, 마감), 일시는 (시작, 종료). 읽지 못하면 None."""
    if not entry["when"]:
        return None
    label, value = entry["when"]
    m = _SPAN_RE.match(value)
    if not m:
        return None
    sy, sm = entry["year"], entry["month"]
    first = (int(m[1]), int(m[2]))
    last = (int(m[3]), int(m[4])) if m[3] else None
    if label == "접수":
        if last is None:  # 마감일 하나만 있는 표기
            end = _date(_year_near(first[0], sy, sm), *first)
            return ("접수", None, end) if end else None
        ey = _year_near(last[0], sy, sm)
        start, end = _date(ey if first <= last else ey - 1, *first), _date(ey, *last)
        return ("접수", start, end) if start and end else None
    ys = _year_near(first[0], sy, sm)
    start = _date(ys, *first)
    end = _date(ys if (last or first) >= first else ys + 1, *(last or first))
    return ("일시", start, end) if start and end and start <= end else None


def _mode_region(tags):
    offline = [t for t in tags if t.startswith("오프라인")]
    online = "온라인" in tags
    mode = "hybrid" if online and offline else "online" if online else "offline" if offline else "unknown"
    place = re.match(r"오프라인\((.+)\)", offline[0]) if offline else None
    if mode == "hybrid":
        return mode, f"{place[1]} 및 온라인" if place else domestic_region(mode)
    if mode == "offline" and place:
        return mode, place[1]
    return mode, domestic_region(mode)


def _is_foreign_offline(tags):
    for tag in tags:
        place = re.match(r"오프라인\((.+)\)", tag)
        if place and any(place[1].strip().startswith(name) for name in _FOREIGN_PLACES):
            return True
    return False


def _kind(entry):
    """제목에 해커톤이 있으면 해커톤, 분류가 대회면 공모전, 나머지(세미나·모임)는 행사. 강의·부트캠프·채용 제목은 None."""
    title = entry["title"]
    if rules.is_excluded_title(title):
        return None
    if rules.classify_kind(title) == "hackathon":
        return "hackathon"
    return "contest" if "대회" in entry["tags"] else "event"


def _is_ai(entry):
    """AI 분류(디렉터리 태그)를 근거로 삼되, 일반 세미나·모임은 제목에도 AI 단어가 있어야 한다. 해커톤·대회는 AI 태그만으로 인정한다
    (제목이 'Cursor Hackathon'처럼 AI 단어 없이 AI 대회인 경우가 있고, 클라우드·블록체인 모임에 AI 태그가 붙는 경우는 걸러야 하기 때문)."""
    if rules.is_ai_related(entry["title"]):
        return True
    return "AI" in entry["tags"] and ("대회" in entry["tags"] or rules.classify_kind(entry["title"]) == "hackathon")


def build_raw(entry, dates, today):
    label, start, end = dates
    mode, region = _mode_region(entry["tags"])
    fee = "무료" if "무료" in entry["tags"] else "유료" if "유료" in entry["tags"] else rules.UNKNOWN_TEXT
    extra = [t for t in entry["tags"] if t not in _PLAIN_TAGS and not t.startswith("오프라인")]
    raw_when = entry["when"][1]
    if label == "접수":
        status = "open" if start and start <= today else "unknown"
        period = {"registrationStartDate": start, "deadlineDate": end, "startDate": None, "endDate": None}
        note = f"접수 {raw_when} (Dev-Event 목록 표기, 날짜만 사용). 자격·참가비·접수 방법은 행사 페이지에서 확인 필요"
    else:
        status = "unknown"
        period = {"registrationStartDate": None, "deadlineDate": None, "startDate": start, "endDate": end}
        note = f"개최 {raw_when} (Dev-Event 목록 표기). 접수 마감·자격은 행사 페이지에서 확인 필요"
    return {
        "kind": _kind(entry), "title": entry["title"], "organizer": entry["organizer"],
        "description": "Dev-Event 개발자 행사 목록에 등록된 AI 관련 항목", "tags": ["AI", *extra], "mode": mode, "region": region,
        "country": "KR", **period, "deadlineAt": None, "eligibility": rules.UNKNOWN_TEXT, "eligibilityVerified": False,
        "fee": fee, "prize": None, "url": entry["url"], "sourceUrl": f"{SOURCE_URL}#{entry['year'] % 100}년-{entry['month']}월", "sourceName": SOURCE_NAME,
        "dateNote": note, "sourceStatus": status,
    }


def collect(fetcher, now, max_items=None):
    limit = ITEM_LIMIT if max_items is None else max(0, min(max_items, ITEM_LIMIT))
    today = now.astimezone(rules.SEOUL).date().isoformat()
    entries = parse_readme(fetcher.get(README_URL).text)
    items, skipped = [], 0
    for entry in entries:
        if len(items) >= limit:
            break
        dates = resolve_dates(entry)
        if not _is_ai(entry) or dates is None or max(d for d in dates[1:] if d) < today or not is_safe_https_url(entry["url"]) or _kind(entry) is None                 or _is_foreign_offline(entry["tags"]):
            skipped += 1
            continue
        items.append(build_raw(entry, dates, today))
    return CollectResult(items, f"월별 항목 {len(entries)}건 중 AI 진행·예정 {len(items)}건 사용(비AI·지난 행사·날짜 미확정·비HTTPS 링크·해외 오프라인 제외 {skipped}건)")
