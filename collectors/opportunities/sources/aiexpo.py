"""AI EXPO KOREA 공식 사이트 '전시회 개요' 페이지. 행사 개요 표(행사명·기간·장소·주최/주관)에서 연도가 명시된 기간만 읽는다.
연도는 코드에 두지 않고 페이지 값을 쓴다. 사전등록·참관 자격·참가비는 이 페이지에 없어 '확인 필요'로 둔다."""
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from .. import rules
from ..errors import FetchError, StructureError
from ..urlsafe import canonical_url, is_safe_https_url
from .base import CollectResult

SOURCE_ID = "aiexpo"
SOURCE_NAME = "AI EXPO KOREA"
SOURCE_URL = "https://aiexpo.co.kr/"
OVERVIEW_URL = "https://aiexpo.co.kr/%ec%a0%84%ec%8b%9c%ed%9a%8c-%ea%b0%9c%ec%9a%94/"  # /전시회-개요/
SHOWALA_URL = "https://www.showala.com/ex/ex_detail.php?idx=4273"
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


def parse_showala(html, now):
    """독립 전시포털의 같은 행사임을 확인한다. 종료된 과거 회차로 갱신하지 않는다."""
    root = BeautifulSoup(html, "html.parser").select_one(".ba_info")
    if root is None:
        raise StructureError("SHOWALA AI EXPO 행사 정보가 없음")

    def text(selector):
        tag = root.select_one(selector)
        if tag is None:
            raise StructureError(f"SHOWALA AI EXPO 필드 없음: {selector}")
        return rules.clean_text(tag.get_text(" ", strip=True))

    title = text(".eng_tit")
    match = re.fullmatch(r"AI EXPO KOREA (20\d\d)", title)
    if not match or text(".kor_tit") != f"{match[1]} 국제인공지능대전":
        raise StructureError("SHOWALA AI EXPO 행사명·연도 불일치")
    homepage_tag = root.select_one(".homp .des a[href]")
    homepage = homepage_tag["href"] if homepage_tag else text(".homp .des")
    if not is_safe_https_url(homepage) or urlsplit(homepage).hostname not in ("aiexpo.co.kr", "www.aiexpo.co.kr"):
        raise StructureError("SHOWALA 행사 공식 홈페이지 불일치")
    period = re.fullmatch(r"(20\d\d-\d{2}-\d{2})\s*~\s*(20\d\d-\d{2}-\d{2})", text(".date .des"))
    start, end = (rules.parse_date(period[1]), rules.parse_date(period[2])) if period else (None, None)
    today = (now or datetime.now(timezone.utc)).astimezone(rules.SEOUL).date().isoformat()
    if not start or not end or start > end or start[:4] != match[1] or end[:4] != match[1] or end < today:
        raise StructureError("SHOWALA AI EXPO 기간이 잘못됐거나 이전 회차임")
    organizer = text(".opener .des")
    if not all(name in organizer for name in ("한국인공지능협회", "서울메쎄", "인공지능신문")):
        raise StructureError("SHOWALA AI EXPO 주최 기관 불일치")
    return {
        "title": f"{title} (국제인공지능대전)", "startDate": start, "endDate": end,
        "venue": " ".join(rules.clean_text(tag.get_text(" ", strip=True)) for tag in root.select(".where .des")),
        "organizer": organizer, "b2b": "B2B" in root.get_text(" "),
    }


def collect(fetcher, now, max_items=None):
    source_url, recovery = OVERVIEW_URL, ""
    try:
        page = fetcher.get(OVERVIEW_URL)
    except FetchError as exc:
        try:
            alternate_page = fetcher.get(SHOWALA_URL)
            if canonical_url(alternate_page.url) != canonical_url(SHOWALA_URL):
                raise StructureError("SHOWALA 최종 확인 URL이 행사 상세 경로와 다름")
            data = parse_showala(alternate_page.text, now)
        except FetchError as alternate:
            status = "blocked" if "blocked" in (exc.status, alternate.status) else "error"
            raise FetchError(status, f"공식 사이트: {exc}; SHOWALA: {alternate}") from alternate
        source_url = alternate_page.url
        recovery = f"직접 조회 실패({exc.status}); 한국전시산업진흥회 SHOWALA로 확인. "
    else:
        data = parse_overview(page.text)
    note = ("한국전시산업진흥회 SHOWALA의 개최 기간 기준. " if recovery else "공식 전시회 개요의 개최 기간 기준. ")
    note += "사전등록·참관 자격과 참가비는 공식 사이트에서 확인 필요"
    if data["b2b"]:
        note += " (공식 안내: B2B 전문 전시회)"
    raw = {
        "kind": "event", "title": data["title"], "organizer": data["organizer"],
        "description": f"국내 AI 전문 전시회. 개최 {data['startDate']} ~ {data['endDate']}" + (f", 장소 {data['venue']}" if data["venue"] else "") + ".",
        "tags": ["AI", "전시회", "엑스포"], "mode": "offline" if data["venue"] else "unknown",
        "region": data["venue"] or "국내(장소 확인 필요)", "country": "KR", "startDate": data["startDate"], "endDate": data["endDate"],
        "registrationStartDate": None, "deadlineDate": None, "deadlineAt": None, "eligibility": rules.UNKNOWN_TEXT,
        "eligibilityVerified": False, "fee": rules.UNKNOWN_TEXT, "prize": None, "url": OVERVIEW_URL, "sourceUrl": source_url,
        "sourceName": f"{SOURCE_NAME} · SHOWALA" if recovery else SOURCE_NAME, "dateNote": note, "sourceStatus": "unknown",
    }
    return CollectResult([raw], (recovery + f"행사 {data['startDate']}~{data['endDate']} {data['venue'] or ''}").strip())
