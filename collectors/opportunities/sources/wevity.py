"""위비티 공모전 검색 목록 + 상세. 검색은 sp=name 이 있어야 필터가 적용된다(sw=AI만으로는 기본 목록이 나온다)."""
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from .. import rules
from ..errors import FetchError, StructureError
from ..urlsafe import is_safe_https_url
from .base import CollectResult, domestic_region, effective_limit, fail_if_every_fetch_failed
from .dacon import infer_mode

SOURCE_ID = "wevity"
SOURCE_NAME = "위비티"
SOURCE_URL = "https://www.wevity.com/?c=find&s=1&gub=1"
LISTING_URL = "https://www.wevity.com/?c=find&s=1&gub=1&sp=name&sw=AI"
_IX_RE = re.compile(r"[?&]ix=(\d+)")
_PERIOD_RE = re.compile(r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})\s*~\s*(\d{4}[-./]\d{1,2}[-./]\d{1,2})")
_STATUS = {"접수중": "open", "마감임박": "open", "마감": "closed"}


def detail_url(ix):
    return f"https://www.wevity.com/?c=find&s=1&gub=1&gbn=view&ix={ix}"


def parse_listing(text):
    soup = BeautifulSoup(text, "html.parser")
    root = soup.select_one(".list")
    if root is None or root.select_one("li.top") is None:
        raise StructureError("위비티 목록에 .list 헤더 구조가 없음")
    rows, body_rows = [], 0
    for li in root.select("li"):
        if "top" in (li.get("class") or []):
            continue
        body_rows += 1
        a = li.select_one(".tit a[href*='gbn=view']")
        m = _IX_RE.search(a.get("href", "")) if a else None
        if not m:
            continue
        organ, dday = li.select_one(".organ"), li.select_one(".day .dday")
        rows.append({
            "ix": m[1], "title": a.get_text(" ", strip=True),
            "organizer": organ.get_text(" ", strip=True) if organ else None,
            "sourceStatus": _STATUS.get(dday.get_text(" ", strip=True) if dday else "", "unknown"),
        })
    if body_rows and not rows:
        raise StructureError("위비티 목록 행에서 제목 링크를 읽지 못함")
    return rows


def parse_detail(text):
    soup = BeautifulSoup(text, "html.parser")
    info = soup.select_one("ul.cd-info-list")
    if info is None:
        raise StructureError("위비티 상세에 .cd-info-list가 없음")
    fields = {}
    for li in info.find_all("li", recursive=False):
        label = li.select_one(".tit")
        if label is None:
            continue
        key = label.get_text(strip=True)
        anchor = li.find("a")
        fields[key] = {"text": re.sub(r"\s+", " ", li.get_text(" ", strip=True).replace(key, "", 1)).strip(),
                       "href": anchor.get("href") if anchor else None}
    period = None
    m = _PERIOD_RE.search(fields.get("접수기간", {}).get("text", ""))
    if m:
        start, end = rules.parse_date(m[1]), rules.parse_date(m[2])
        period = (start, end) if start and end else None
    homepage = (fields.get("홈페이지") or {}).get("href")
    descriptions = []
    body = soup.select_one("#viewContents")
    if body is not None:
        for line in body.get_text("\n").splitlines():
            line = line.strip().lstrip("■▶●◆※-· ").strip()
            if len(line) >= 25:
                descriptions.append(line)
            if len(descriptions) == 4:
                break
    prize_total = (fields.get("총 상금") or {}).get("text") or None
    prize_first = (fields.get("1등 상금") or {}).get("text") or None
    if prize_total and re.search(r"\d", prize_total):
        prize_total = f"총 {prize_total}"
    prize = " / ".join(p for p in (prize_total, f"1등 {prize_first}" if prize_first else None) if p) or None
    own_site = homepage and (urlsplit(homepage).hostname or "").endswith("wevity.com")
    return {
        "period": period, "target": (fields.get("응모대상") or {}).get("text") or None,
        "organizer": (fields.get("주최/주관") or {}).get("text") or None,
        "homepage": homepage if homepage and not own_site and is_safe_https_url(homepage) else None,
        "prize": prize, "descriptions": descriptions,
    }


def build_raw(row, detail):
    title = row["title"]
    mode = infer_mode(title, "")
    start, end = detail["period"] if detail["period"] else (None, None)
    target = detail["target"]
    page = detail_url(row["ix"])
    return {
        "kind": rules.classify_kind(title, "contest"), "title": title, "organizer": detail["organizer"] or row["organizer"],
        "description": next((d for d in detail["descriptions"] if d not in title), title), "tags": ["AI"], "mode": mode,
        "region": domestic_region(mode), "country": "KR",
        "startDate": None, "endDate": None, "registrationStartDate": start, "deadlineDate": end, "deadlineAt": None,
        "eligibility": target or rules.UNKNOWN_TEXT, "eligibilityVerified": bool(target), "fee": rules.UNKNOWN_TEXT,
        "prize": detail["prize"], "url": detail["homepage"] or page, "sourceUrl": page, "sourceName": SOURCE_NAME,
        "dateNote": "날짜만 제공(시각 미확인, 접수기간 원문 기준)" if end else "접수 기간 확인 필요",
        "sourceStatus": row["sourceStatus"],
    }


def collect(fetcher, now, max_items=None):
    rows = parse_listing(fetcher.get(LISTING_URL).text)
    rows = [r for r in rows if rules.is_ai_related(r["title"]) and rules.classify_kind(r["title"], "contest")]
    rows = rows[:effective_limit(max_items)]
    items, failures = [], []
    for row in rows:
        try:
            detail = parse_detail(fetcher.get(detail_url(row["ix"])).text)
        except (FetchError, StructureError) as exc:
            failures.append(exc)
            continue
        items.append(build_raw(row, detail))
    fail_if_every_fetch_failed(len(rows), failures, "위비티")
    return CollectResult(items, f"AI 관련 후보 {len(rows)}건 중 {len(items)}건 사용, 상세 조회 실패 {len(failures)}건")
