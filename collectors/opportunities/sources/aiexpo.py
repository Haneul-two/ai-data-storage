"""AI EXPO KOREA 공식 사이트 '전시회 개요' 페이지. 행사 개요 표(행사명·기간·장소·주최/주관)에서 연도가 명시된 기간만 읽는다.
연도는 코드에 두지 않고 페이지 값을 쓴다. 사전등록·참관 자격·참가비는 이 페이지에 없어 '확인 필요'로 둔다."""
import re

from bs4 import BeautifulSoup

from .. import rules
from ..errors import StructureError
from .base import CollectResult

SOURCE_ID = "aiexpo"
SOURCE_NAME = "AI EXPO KOREA"
SOURCE_URL = "https://aiexpo.co.kr/"
OVERVIEW_URL = "https://aiexpo.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ea%b0%9c%ec%9a%94/"  # /전시회-개요/
_PERIOD_RE = re.compile(r"(20\d\d)\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일(?:\([^)]*\))?\s*[~\-–]\s*(?:(\d{1,2})\s*월\s*)?(\d{1,2})\s*일")


def parse_overview(html):
    soup = BeautifulSoup(html, "html.parser")
    fields = {}
    for tr in soup.select("table tr"):
        th, td = tr.find("th"), tr.find("td")
        if th is not None and td is not None:
            fields.setdefault(re.sub(r"\s+", "", th.get_text()), rules.clean_text(td.get_text(" ", strip=True)))
    if "행사명" not in fields or "기간" not in fields:
        raise StructureError("AI EXPO 전시회 개요에 행사명/기간 표가 없음")
    m = _PERIOD_RE.search(fields["기간"])
    if not m:
        raise StructureError("AI EXPO 개최 기간(연도 포함)을 읽지 못함")
    year, month = m[1], m[2]
    end_month = m[4] or month
    start, end = rules.parse_date(f"{year}-{month}-{m[3]}"), rules.parse_date(f"{year}-{end_month}-{m[5]}")
    if not start or not end or start > end:
        raise StructureError("AI EXPO 개최 기간 날짜가 올바르지 않음")
    title_year = re.search(r"20\d\d", fields["행사명"])
    if title_year and title_year[0] != year:
        raise StructureError(f"AI EXPO 행사명 연도({title_year[0]})와 기간 연도({year})가 다름")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return {
        "title": fields["행사명"], "startDate": start, "endDate": end, "venue": fields.get("장소"),
        "organizer": fields.get("주최/주관"), "b2b": "B2B" in soup.get_text(" "),
    }


def collect(fetcher, now, max_items=None):
    data = parse_overview(fetcher.get(OVERVIEW_URL).text)
    note = "공식 전시회 개요의 개최 기간 기준. 사전등록·참관 자격과 참가비는 공식 사이트에서 확인 필요"
    if data["b2b"]:
        note += " (공식 안내: B2B 전문 전시회)"
    raw = {
        "kind": "event", "title": data["title"], "organizer": data["organizer"],
        "description": f"국내 AI 전문 전시회. 개최 {data['startDate']} ~ {data['endDate']}" + (f", 장소 {data['venue']}" if data["venue"] else "") + ".",
        "tags": ["AI", "전시회", "엑스포"], "mode": "offline" if data["venue"] else "unknown",
        "region": data["venue"] or "국내(장소 확인 필요)", "country": "KR", "startDate": data["startDate"], "endDate": data["endDate"],
        "registrationStartDate": None, "deadlineDate": None, "deadlineAt": None, "eligibility": rules.UNKNOWN_TEXT,
        "eligibilityVerified": False, "fee": rules.UNKNOWN_TEXT, "prize": None, "url": OVERVIEW_URL, "sourceUrl": OVERVIEW_URL,
        "sourceName": SOURCE_NAME, "dateNote": note, "sourceStatus": "unknown",
    }
    return CollectResult([raw], f"행사 {data['startDate']}~{data['endDate']} {data['venue'] or ''}".strip())
