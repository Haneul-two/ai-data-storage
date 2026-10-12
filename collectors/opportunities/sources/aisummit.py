"""공식 행사 소스: AI Summit Seoul & EXPO 메인 페이지의 노출 행사 블록만 해석한다.
사이트 <title>은 이전 연도를 유지하는 일이 있어, 본문에서 연도가 명시된 기간 표기만 신뢰한다."""
import re

from bs4 import BeautifulSoup

from .. import rules
from ..errors import StructureError
from .base import CollectResult

SOURCE_ID = "aisummit"
SOURCE_NAME = "AI Summit Seoul"
SOURCE_URL = "https://www.aisummit.co.kr/"
MAIN_URL = "https://www.aisummit.co.kr/"
# 운영 환경에서 이 페이지 응답이 2.5MB 상한을 넘은 적이 있다(로컬 실측은 약 0.6MB, 기간·장소는 앞 25~30% 안). 상한을 올리지 않고
# 앞쪽 1MB만 읽는다. 그 안에서 연도 포함 기간을 못 찾으면 추측하지 않고 오류로 둔다.
PREFIX_BYTES = 1_000_000
_RANGE_RE = re.compile(r"(20\d\d)\s*\.\s*(\d{1,2})\s*\.\s*(\d{1,2})\s*\([^)]*\)\s*[-–~]\s*(\d{1,2})\s*\.\s*(\d{1,2})")
_PART_RE = r"{label}\s*(20\d\d)\s*년\s*(\d{{1,2}})\s*월\s*(\d{{1,2}})\s*-\s*(\d{{1,2}})\s*일"


def _after_label(lines, label):
    for i, line in enumerate(lines):
        if line == label:
            for nxt in lines[i + 1:i + 4]:
                if nxt != ":":
                    return rules.clean_text(nxt)
    return None


def _part(text, label):
    m = re.search(_PART_RE.format(label=label), text)
    if not m:
        return None
    year, month = m[1], m[2]
    return rules.parse_date(f"{year}-{month}-{m[3]}"), rules.parse_date(f"{year}-{month}-{m[4]}")


def parse_main(html):
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title_year = (re.search(r"20\d\d", title_tag.get_text()) or [None])[0] if title_tag else None
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    root = soup.select_one("main") or soup.body or soup
    lines = [ln for ln in root.get_text("\n", strip=True).splitlines() if ln]
    text = "\n".join(lines)
    m = _RANGE_RE.search(text)
    if not m:
        raise StructureError("AI Summit 노출 행사 기간(연도 포함)을 읽지 못함")
    year = m[1]
    start = rules.parse_date(f"{year}-{m[2]}-{m[3]}")
    end = rules.parse_date(f"{year}-{m[4]}-{m[5]}")
    if not start or not end or start > end:
        raise StructureError("AI Summit 행사 기간 날짜가 올바르지 않음")
    conference, expo = _part(text, "컨퍼런스"), _part(text, "EXPO")
    for part in (conference, expo):
        if part and (None in part or not part[0].startswith(year)):
            raise StructureError("AI Summit 기간 표기의 연도가 서로 다름")
    name = _after_label(lines, "행사명") or "AI Summit Seoul & EXPO"
    return {
        "startDate": start, "endDate": end, "titleYear": title_year, "title": f"{name} {year}",
        "venue": _after_label(lines, "장소"), "organizer": _after_label(lines, "주최"),
        "conference": conference, "expo": expo,
    }


def _span(part):
    return f"{part[0]}~{part[1][8:]}"


def collect(fetcher, now, max_items=None):
    page = fetcher.get(MAIN_URL, prefix_bytes=PREFIX_BYTES)
    data = parse_main(page.text)
    year = data["startDate"][:4]
    notes = [f"{label} {_span(part)}" for label, part in (("컨퍼런스", data["conference"]), ("EXPO", data["expo"])) if part]
    venue = data["venue"] or ""
    raw = {
        "kind": "event", "title": data["title"], "organizer": data["organizer"],
        "description": f"서울에서 열리는 AI 컨퍼런스·전시 행사. 개최 {data['startDate']} ~ {data['endDate']}" + (f", 장소 {venue}" if venue else "") + ".",
        "tags": ["AI", "컨퍼런스", "전시"], "mode": "offline", "region": "서울 코엑스" if "코엑스" in venue else "국내(장소 확인 필요)",
        "country": "KR", "startDate": data["startDate"], "endDate": data["endDate"], "registrationStartDate": None,
        "deadlineDate": None, "deadlineAt": None, "eligibility": rules.UNKNOWN_TEXT, "eligibilityVerified": False,
        "fee": rules.UNKNOWN_TEXT, "prize": None, "url": MAIN_URL, "sourceUrl": MAIN_URL, "sourceName": SOURCE_NAME,
        "dateNote": ("; ".join(notes) + " (공식 사이트 노출 기준). " if notes else "") + "접수 마감과 참가비는 공식 사이트에서 확인 필요",
        "sourceStatus": "unknown",
    }
    message = f"노출 행사 {year}년 {data['startDate']}~{data['endDate']}"
    if getattr(page, "truncated", False):
        message += f". 큰 응답이라 앞 {PREFIX_BYTES // 1000}KB만 읽음"
    if data["titleYear"] and data["titleYear"] != year:
        message += f". 경고: 페이지 title은 {data['titleYear']}년 표기, 본문 노출 행사({year}) 기준 사용"
    return CollectResult([raw], message)
