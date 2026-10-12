"""콘테스트코리아(contestkorea.com) 공모전 제목 검색 목록 + 상세. 제목 검색(Txt_key=str_meeting)이 서버 렌더링(GET)으로 동작한다.
목록의 접수 기간에는 연도가 없고 상태 라벨(접수중·마감임박·접수예정·심사중 …)이 있다. 종료 상태 행은 상세를 읽지 않고,
연도가 있는 상세의 접수기간만 날짜로 쓴다(목록 마감일과 다르거나 접수중인데 이미 지난 날짜면 신뢰하지 않는다)."""
import re
from urllib.parse import parse_qs, quote, urlsplit

from bs4 import BeautifulSoup

from .. import rules
from ..errors import FetchError, StructureError
from ..urlsafe import is_safe_https_url
from .base import CollectResult, domestic_region, fail_if_every_fetch_failed
from .dacon import infer_mode

SOURCE_ID = "contestkorea"
SOURCE_NAME = "콘테스트코리아"
SOURCE_URL = "https://www.contestkorea.com/sub/list.php?int_gbn=1"
KEYWORDS = (("AI", 12), ("인공지능", 3))  # (제목 검색어, 최대 페이지). 검색어별 하드 상한. 마감 여부로 뒷페이지 존재를 판정하지 않는다(목록 순서가 마감 단조가 아님)
PAGE_LIMIT = KEYWORDS[0][1]
PAGE_LIMIT_SECONDARY = KEYWORDS[1][1]
ITEM_LIMIT = 60  # 상세 조회 하드 상한. --max-items가 더 작으면 그 값
_LIST = "https://www.contestkorea.com/sub/list.php?displayrow=12&int_gbn=1&Txt_sGn=1&Txt_key=str_meeting&Txt_word={word}&Txt_sortkey=a.int_sort&Txt_sortword=desc&page={page}"
_OPEN = {"접수중", "마감임박"}
_CLOSED = {"심사중", "심사대기", "발표대기", "발표보기", "캠페인마감", "마감", "접수마감", "종료"}
_PERIOD_RE = re.compile(r"(\d{4})\s*[.\-]\s*(\d{1,2})\s*[.\-]\s*(\d{1,2})\s*~\s*(\d{4})\s*[.\-]\s*(\d{1,2})\s*[.\-]\s*(\d{1,2})")
_LIST_END_RE = re.compile(r"(\d{2})\.(\d{2})\s*(?:~\s*(\d{2})\.(\d{2}))?")


def page_url(keyword, page):
    return _LIST.format(word=quote(keyword), page=page)


def detail_url(bcode, str_no):
    return f"https://www.contestkorea.com/sub/view.php?int_gbn=1&Txt_bcode={bcode}&str_no={str_no}"


def item_limit(max_items):
    return ITEM_LIMIT if max_items is None else max(0, min(max_items, ITEM_LIMIT))


def _status(label):
    if label in _OPEN:
        return "open"
    if label in _CLOSED:
        return "closed"
    return "unknown"  # 접수예정이나 새 라벨은 마감 근거가 없으므로 닫힌 것으로 보지 않는다


def parse_listing(text):
    soup = BeautifulSoup(text, "html.parser")
    root = soup.select_one("div.list_style_2")
    if root is None:
        raise StructureError("콘테스트코리아 목록에 .list_style_2 구조가 없음")
    ul = root.find("ul", recursive=False)
    items = ul.find_all("li", recursive=False) if ul else []
    rows = []
    for li in items:
        a = li.select_one(".title a[href*='str_no=']")
        name = li.select_one(".title .txt")
        if a is None or name is None:
            continue
        query = parse_qs(urlsplit(a.get("href", "")).query)
        str_no, bcode = (query.get("str_no") or [""])[0], (query.get("Txt_bcode") or [""])[0]
        if not str_no.isdigit() or not bcode.isdigit():
            continue
        label = li.select_one(".d-day .condition")
        period = li.select_one(".date .step-1")
        m = _LIST_END_RE.search(period.get_text(" ", strip=True)) if period else None
        list_end = ((m[3], m[4]) if m[3] else (m[1], m[2])) if m else None  # 'MM.DD~MM.DD' 또는 단일 'MM.DD'
        category = li.select_one(".title .category")
        rows.append({
            "strNo": str_no, "bcode": bcode, "title": name.get_text(" ", strip=True),
            "category": category.get_text(" ", strip=True) if category else None,
            "sourceStatus": _status(label.get_text(strip=True) if label else ""),
            "listEnd": list_end,
        })
    if items and not rows:
        raise StructureError("콘테스트코리아 목록 행에서 제목 링크를 읽지 못함")
    return rows


def _fields(soup):
    out = {}
    for tr in soup.select("table tr"):
        th, td = tr.find("th"), tr.find("td")
        if th is not None and td is not None:
            out.setdefault(re.sub(r"\s+", " ", th.get_text(" ", strip=True)), td)
    return out


def _period(text):
    m = _PERIOD_RE.search(text or "")
    if not m:
        return None
    start = rules.parse_date(f"{m[1]}-{m[2]}-{m[3]}")
    end = rules.parse_date(f"{m[4]}-{m[5]}-{m[6]}")
    return (start, end) if start and end and start <= end else None


def _https_link(anchor, attr="href"):
    value = anchor.get(attr) if anchor is not None else None
    return value if value and is_safe_https_url(value) else None


def parse_detail(text):
    soup = BeautifulSoup(text, "html.parser")
    fields = _fields(soup)
    if "접수기간" not in fields:
        raise StructureError("콘테스트코리아 상세에 접수기간 표가 없음")

    def plain(label):
        td = fields.get(label)
        return rules.clean_text(td.get_text(" ", strip=True)) if td is not None else ""

    apply_url = None
    if "접수하기" in fields:
        apply_url = next(filter(None, (_https_link(a) for a in fields["접수하기"].find_all("a"))), None)
    if apply_url is None and "홈페이지" in fields:  # 홈페이지 링크는 href가 javascript라 val2 속성에 주소가 있다
        apply_url = next(filter(None, (_https_link(a, "val2") for a in fields["홈페이지"].find_all("a"))), None)
    organizer = next((plain(label) for label in fields if label.startswith("주최")), "")
    return {
        "period": _period(plain("접수기간")), "target": ", ".join(dict.fromkeys(t.strip() for t in plain("참가대상").split(",") if t.strip())),
        "region": _compact_region(plain("대회지역")), "apply_url": apply_url, "prize": plain("시상내역") or None, "fee": plain("참가비용"),
        "organizer": organizer or None,
    }


def _compact_region(region):
    """사이트가 '서 울', '대 구'처럼 글자 사이에 공백을 넣는 지역명을 붙인다. 여러 단어인 지역은 그대로 둔다."""
    return region.replace(" ", "") if re.fullmatch(r"(?:[가-힣] ){1,3}[가-힣]", region) else region


def _mode(region, title):
    tokens = [t.strip() for t in re.split(r"[,/]", region) if t.strip()]
    if tokens == ["온라인"]:
        return "online"
    if "온라인" in tokens:
        return "hybrid"
    return infer_mode(title, "")


def build_raw(row, detail):
    title = row["title"]
    mode = _mode(detail["region"], title)
    period = detail["period"]
    target = detail["target"]
    known_target = bool(target) and "해당자" not in target
    page = detail_url(row["bcode"], row["strNo"])
    fee = "무료" if "무료" in detail["fee"] else rules.UNKNOWN_TEXT
    return {
        "kind": rules.classify_kind(title, "contest"), "title": title, "organizer": detail["organizer"],
        "description": f"콘테스트코리아에 등록된 공모전. 분류: {row['category']}" if row["category"] else "콘테스트코리아에 등록된 공모전",
        "tags": ["AI", *([row["category"]] if row["category"] else [])], "mode": mode,
        "region": domestic_region(mode) if mode in ("online", "hybrid") or not detail["region"] else detail["region"], "country": "KR",
        "startDate": None, "endDate": None, "registrationStartDate": period[0] if period else None,
        "deadlineDate": period[1] if period else None, "deadlineAt": None,
        "eligibility": target if known_target else rules.UNKNOWN_TEXT, "eligibilityVerified": known_target, "fee": fee,
        "prize": detail["prize"], "url": detail["apply_url"] or page, "sourceUrl": page, "sourceName": SOURCE_NAME,
        "dateNote": "날짜만 제공(시각 미확인, 접수기간 원문 기준)" if period else "접수 기간 확인 필요",
        "sourceStatus": row["sourceStatus"],
    }


def _check_consistent(row, detail, today):
    """목록(연도 없음)과 상세(연도 있음)가 같은 마감일을 가리키는지, 접수중인데 마감이 이미 지나지 않았는지."""
    period = detail["period"]
    if period is None:
        return
    if row["listEnd"] and (period[1][5:7], period[1][8:10]) != row["listEnd"]:
        raise StructureError(f"콘테스트코리아 목록 마감({row['listEnd'][0]}.{row['listEnd'][1]})과 상세 마감({period[1]})이 다름")
    if row["sourceStatus"] == "open" and period[1] < today:
        raise StructureError(f"콘테스트코리아가 접수중이라는 항목의 마감일({period[1]})이 이미 지남")


def _is_candidate(row):
    return row["sourceStatus"] != "closed" and _is_ai_row(row)


def _is_ai_row(row):
    return rules.is_ai_related(row["title"]) and rules.classify_kind(row["title"], "contest")


def collect(fetcher, now, max_items=None):
    limit = item_limit(max_items)
    today = now.astimezone(rules.SEOUL).date().isoformat()
    rows, seen, pages_read, closed = [], set(), 0, []
    for keyword, max_pages in KEYWORDS:
        for page in range(1, max_pages + 1):
            if len(rows) >= limit:
                break
            # 이후 페이지의 HTTP·구조 오류도 소스 실패로 넘겨 부분 결과가 완전 성공으로 보이지 않게 한다
            listing = parse_listing(fetcher.get(page_url(keyword, page)).text)
            pages_read += 1
            new = [r for r in listing if r["strNo"] not in seen]
            if not new:
                break  # 빈 페이지이거나 이미 본 페이지 반복
            seen.update(r["strNo"] for r in new)
            rows.extend(r for r in new if _is_candidate(r))
            closed.extend(detail_url(r["bcode"], r["strNo"]) for r in new if r["sourceStatus"] == "closed" and _is_ai_row(r))  # 상세는 읽지 않고 기존 항목의 마감 전파용으로만 관찰
    rows = rows[:limit]
    items, failures = [], []
    for row in rows:
        try:
            detail = parse_detail(fetcher.get(detail_url(row["bcode"], row["strNo"])).text)
            _check_consistent(row, detail, today)
        except (FetchError, StructureError) as exc:
            failures.append(exc)
            continue
        items.append(build_raw(row, detail))
    fail_if_every_fetch_failed(len(rows), failures, "콘테스트코리아")
    return CollectResult(items, f"AI 활성 후보 {len(rows)}건({pages_read}페이지 확인) 중 {len(items)}건 사용, 상세 조회·검증 실패 {len(failures)}건", closed)
