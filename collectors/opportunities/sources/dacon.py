"""DACON 공개 대회 목록(SSR) + overview의 inert 문자열 필드. 인라인 JS는 절대 실행하지 않는다."""
import json
import re

from bs4 import BeautifulSoup

from .. import rules
from ..errors import FetchError, StructureError
from .base import CollectResult, domestic_region, effective_limit, fail_if_every_fetch_failed

SOURCE_ID = "dacon"
SOURCE_NAME = "DACON"
SOURCE_URL = "https://dacon.io/competitions"
LISTING_URL = "https://dacon.io/competitions"
_ID_RE = re.compile(r"/competitions/official/(\d+)/")
_FIELDS = ("period_start", "period_end", "submission_end", "name", "keyword", "prize_info")
_STATUS = {"참가신청중": "open", "마감": "closed"}
_PRIORITY = {"open": 0, "unknown": 1, "closed": 2}


def detail_url(cpt_id):
    return f"https://dacon.io/competitions/official/{cpt_id}/overview/"


def parse_listing(text):
    soup = BeautifulSoup(text, "html.parser")
    root = soup.select_one(".official-comp")
    if root is None:
        raise StructureError("DACON 목록에 .official-comp 구조가 없음")
    rows, seen, anchors = [], set(), root.select('a[href*="/competitions/official/"]')
    for a in anchors:
        m = _ID_RE.search(a.get("href", ""))
        name = a.select_one(".name")
        if not m or name is None or m[1] in seen:
            continue
        seen.add(m[1])
        keyword = a.select_one(".keyword")
        dday = a.select_one(".dday")
        tags = [t.strip() for t in keyword.get_text(" ", strip=True).split("|")] if keyword else []
        rows.append({
            "cptId": m[1], "title": name.get_text(" ", strip=True), "tags": [t for t in tags if t],
            "sourceStatus": _STATUS.get(dday.get_text(" ", strip=True) if dday else "", "unknown"),
        })
    if anchors and not rows:
        raise StructureError("DACON 목록 행에서 제목을 읽지 못함")
    return rows


def parse_detail(text):
    """competitionDetail 안의 따옴표 문자열 필드만 정규식으로 읽는다(eval 금지)."""
    start = text.find("competitionDetail:{")
    if start < 0:
        raise StructureError("DACON overview에 competitionDetail이 없음")
    segment = text[start:start + 40000]
    out = {}
    for key in _FIELDS:
        m = re.search(r'(?<![A-Za-z0-9_])' + key + r':"((?:[^"\\]|\\.)*)"', segment)
        if m:
            try:
                out[key] = json.loads('"' + m[1] + '"')
            except ValueError:
                out[key] = m[1]
    return out


def infer_mode(title, keyword):
    online, offline = "온라인" in title, "오프라인" in title
    if online and offline:
        return "hybrid"
    if offline:
        return "offline"
    if online or re.search(r"코드 ?제출", keyword or ""):
        return "online"
    return "unknown"


def _kst_iso(stamp):
    m = re.match(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})$", stamp or "")
    if not m:
        return None
    iso = f"{m[1]}T{m[2]}+09:00"
    return iso if rules.parse_iso_datetime(iso) else None


def build_raw(row, detail):
    title = row["title"]
    mode = infer_mode(title, " | ".join(row["tags"]))
    deadline_at = _kst_iso(detail.get("submission_end"))
    start = rules.parse_date((detail.get("period_start") or "")[:10])
    mismatch = bool(deadline_at and start and deadline_at[:10] < start)
    if mismatch:  # 출처 값이 대회 시작보다 앞서는 모순(원문 오류 가능) — 마감으로 쓰지 않는다
        deadline_at = None
        note ="제출 마감 원문이 대회 시작일보다 앞서 사용하지 않음. 마감 확인 필요"
    elif deadline_at:
        note = f"제출 마감 {deadline_at[:10]} {deadline_at[11:16]} KST(DACON 표기). 대회 기간은 접수 기간이 아니며 신청 마감은 확인 필요"
    else:
        note = "제출 마감 확인 필요"
    return {
        "kind": rules.classify_kind(title, "contest"), "title": title, "organizer": None,
        "description": "DACON 공개 대회 페이지. 분류: " + ", ".join(row["tags"][:5]) if row["tags"] else "DACON 공개 대회 페이지",
        "tags": row["tags"], "mode": mode,
        "region": domestic_region(mode), "country": "KR",
        "startDate": start,
        "endDate": rules.parse_date((detail.get("period_end") or "")[:10]),
        "registrationStartDate": None, "deadlineDate": deadline_at[:10] if deadline_at else None, "deadlineAt": deadline_at,
        "eligibility": rules.UNKNOWN_TEXT, "eligibilityVerified": False, "fee": rules.UNKNOWN_TEXT,
        "prize": detail.get("prize_info") or None,
        "url": detail_url(row["cptId"]), "sourceUrl": detail_url(row["cptId"]), "sourceName": SOURCE_NAME,
        "dateNote": note, "sourceStatus": row["sourceStatus"],
    }


def collect(fetcher, now, max_items=None):
    rows = parse_listing(fetcher.get(LISTING_URL).text)
    rows = [r for r in rows if rules.is_ai_related(r["title"], r["tags"]) and rules.classify_kind(r["title"], "contest")]
    rows.sort(key=lambda r: _PRIORITY[r["sourceStatus"]])  # 정렬은 안정적이라 목록의 최신순이 유지된다
    rows = rows[:effective_limit(max_items)]
    items, failures = [], []
    for row in rows:
        try:
            detail = parse_detail(fetcher.get(detail_url(row["cptId"])).text)
        except (FetchError, StructureError) as exc:
            failures.append(exc)
            continue
        items.append(build_raw(row, detail))
    fail_if_every_fetch_failed(len(rows), failures, "DACON")
    return CollectResult(items, f"AI 관련 후보 {len(rows)}건 중 {len(items)}건 사용, 상세 조회 실패 {len(failures)}건")
