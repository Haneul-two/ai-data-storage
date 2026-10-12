"""Devpost 공개 목록 API + 상세 페이지. 한국 참가 증거와 정밀 마감 시각을 상세에서 확인한다."""
import json
import re

from bs4 import BeautifulSoup

from .. import rules
from ..errors import FetchError, StructureError
from .base import CollectResult, effective_limit, fail_if_every_fetch_failed

SOURCE_ID = "devpost"
SOURCE_NAME = "Devpost"
SOURCE_URL = "https://devpost.com/hackathons"
LISTING_URL = "https://devpost.com/api/hackathons?search=AI&status%5B%5D=open&challenge_type%5B%5D=online&page=1"
PAGE_LIMIT = 5  # 목록 9건씩 최대 5페이지(meta 총 건수가 그보다 적으면 거기까지). 2026-10 실측 총 23건=3페이지
DEFAULT_MAX = 20  # 상세 요청 수 상한(소스 하드 상한과 같다). 1페이지만 읽던 때는 10건이었다
_MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_HACK_TITLE_RE = re.compile(r"hackathon", re.IGNORECASE)
_CONTEST_TITLE_RE = re.compile(r"\b(?:competition|contest)\b", re.IGNORECASE)
_PERIOD_RE = re.compile(r"([A-Za-z]{3})[a-z]*\s+(\d{1,2})(?:,\s*(\d{4}))?\s*-\s*(?:([A-Za-z]{3})[a-z]*\s+)?(\d{1,2}),\s*(\d{4})")


def page_url(page):
    return LISTING_URL if page == 1 else LISTING_URL.replace("page=1", f"page={page}")


def _page_count(text):
    """meta의 총 건수/페이지당 건수로 필요한 목록 페이지 수. 읽을 수 없으면 1페이지."""
    try:
        meta = json.loads(text).get("meta") or {}
        total, per_page = int(meta["total_count"]), int(meta["per_page"])
    except (ValueError, KeyError, TypeError, AttributeError):
        return 1
    return min(PAGE_LIMIT, -(-total // per_page)) if total > 0 and per_page > 0 else 1


def parse_listing(text):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise StructureError("Devpost 목록이 JSON이 아님") from exc
    if not isinstance(data, dict) or not isinstance(data.get("hackathons"), list) or "meta" not in data:
        raise StructureError("Devpost 목록에 hackathons/meta 구조가 없음")
    out = []
    for row in data["hackathons"]:
        themes = [t.get("name", "") for t in row.get("themes") or [] if isinstance(t, dict)]
        location = (row.get("displayed_location") or {}).get("location")
        if (row.get("invite_only") or row.get("open_state") != "open" or str(location).strip().lower() != "online"
                or "Machine Learning/AI" not in themes or not row.get("url") or not row.get("title")):
            continue
        prize = BeautifulSoup(row.get("prize_amount") or "", "html.parser").get_text("").strip()
        out.append({
            "title": row["title"], "url": row["url"], "themes": themes,
            "period": row.get("submission_period_dates") or "",
            "organizer": row.get("organization_name"),
            "prize": prize if re.search(r"[1-9]", prize) else None,  # "$0" 같은 값은 상금 없음으로 본다
        })
    return out


def _period_start(period):
    """'Sep 22 - Oct 26, 2026' 또는 'Dec 20, 2026 - Jan 10, 2027'의 시작일."""
    m = _PERIOD_RE.search(period or "")
    if not m or m[1].lower() not in _MONTHS:
        return None
    start_month = _MONTHS[m[1].lower()]
    year = int(m[3] or m[6])
    if not m[3]:
        end_month = _MONTHS.get(m[4].lower(), start_month) if m[4] else start_month
        if start_month > end_month:
            year -= 1  # 'Dec 20 - Jan 10, 2027'처럼 연말을 넘기면 시작 연도는 종료 연도 전년이다
    return rules.parse_date(f"{year}-{start_month}-{m[2]}")


def parse_detail(text):
    soup = BeautifulSoup(text, "html.parser")
    elig = soup.select_one("#eligibility-list")
    if elig is None:
        raise StructureError("Devpost 상세에 #eligibility-list가 없음")
    lines = []
    for li in elig.find_all("li"):
        line = li.get_text(" ", strip=True)
        tips = [s.get("title") for s in li.select("span[title]") if s.get("title")]
        if tips:
            line += " (" + "; ".join(tips) + ")"
        lines.append(re.sub(r"\s+", " ", line))
    iso = None
    for el in soup.select("[data-iso-date]"):
        iso = el.get("data-iso-date")
        break
    meta = soup.select_one("meta[name=description]") or soup.select_one("meta[property='og:description']")
    description = (meta.get("content") if meta else "") or ""
    if not description:
        for tag in soup.select("script[type='application/ld+json']"):
            try:
                body = json.loads(tag.string or "")
            except ValueError:
                continue
            if isinstance(body, dict) and body.get("description"):
                para = BeautifulSoup(BeautifulSoup(body["description"], "html.parser").get_text(), "html.parser").find("p")
                description = para.get_text(" ", strip=True) if para else ""
                break
    return {"eligibility_lines": lines, "deadlineAt": iso, "description": description}


def _fmt_offset(dt):
    minutes = int(dt.utcoffset().total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    return f"UTC{sign}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"


def _kind(title):
    """명시 hackathon은 해커톤 우선, competition/contest는 공모전, 나머지는 Devpost 기본값인 해커톤."""
    if not _HACK_TITLE_RE.search(title) and _CONTEST_TITLE_RE.search(title):
        return "contest"
    return "hackathon"


def build_raw(candidate, detail):
    """상세 검증을 통과하면 원시 항목, 아니면 None(사유는 호출 측에서 집계)."""
    text = " ".join(detail["eligibility_lines"])
    if not rules.korea_allowed("; ".join(detail["eligibility_lines"])):  # 줄 경계를 절 경계로 판정한다
        return None
    deadline = detail["deadlineAt"]
    parsed = rules.parse_iso_datetime(deadline)
    if parsed is None:
        return None
    seoul = parsed.astimezone(rules.SEOUL)
    tags = ["AI", *[t for t in candidate["themes"] if t != "Machine Learning/AI"]]
    return {
        "kind": _kind(candidate["title"]), "title": candidate["title"], "organizer": candidate["organizer"],
        "description": detail["description"] or candidate["title"], "tags": tags,
        "mode": "online", "region": "해외 온라인", "country": "GLOBAL",
        "startDate": _period_start(candidate["period"]), "endDate": seoul.date().isoformat(),
        "registrationStartDate": None, "deadlineDate": seoul.date().isoformat(), "deadlineAt": deadline,
        "eligibility": text, "eligibilityVerified": True, "fee": rules.UNKNOWN_TEXT, "prize": candidate["prize"],
        "url": candidate["url"], "sourceUrl": candidate["url"], "sourceName": SOURCE_NAME,
        "dateNote": f"원문 마감 {parsed.strftime('%Y-%m-%d %H:%M')} ({_fmt_offset(parsed)}), 서울 기준 {seoul.strftime('%Y-%m-%d %H:%M')}",
        "sourceStatus": "open",
    }


def collect(fetcher, now, max_items=None):
    limit = effective_limit(DEFAULT_MAX if max_items is None else max_items)
    first = fetcher.get(LISTING_URL).text
    candidates, pages = parse_listing(first), _page_count(first)
    for page in range(2, pages + 1):
        if len(candidates) >= limit:
            break
        # 이후 페이지의 HTTP·구조 오류도 소스 실패로 넘겨 부분 결과가 완전 성공으로 보이지 않게 한다
        candidates.extend(parse_listing(fetcher.get(page_url(page)).text))
    candidates = candidates[:limit]
    items, failures, skipped = [], [], 0
    for cand in candidates:
        try:
            detail = parse_detail(fetcher.get(cand["url"]).text)
        except (FetchError, StructureError) as exc:
            failures.append(exc)
            continue
        raw = build_raw(cand, detail)
        if raw is None:
            skipped += 1
        else:
            items.append(raw)
    fail_if_every_fetch_failed(len(candidates), failures, "Devpost")
    return CollectResult(items, f"후보 {len(candidates)}건 중 {len(items)}건 사용, 한국 참가 근거/마감 미확인 {skipped}건 제외, 조회 실패 {len(failures)}건")
