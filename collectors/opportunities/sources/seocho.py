"""서초 AI 페스타 공식 사이트. 행사 정보는 JSON-LD Event에서 읽는다.
일부 프로그램의 사전예약 오픈예정·마감은 축제 전체의 접수 상태가 아니므로 sourceStatus·deadline에 쓰지 않는다."""
import re

from bs4 import BeautifulSoup

from .. import rules
from .base import CollectResult
from .jsonld import raw_from_event, read_event

SOURCE_ID = "seocho"
SOURCE_NAME = "서초 AI 페스타"
SOURCE_URL = "https://seochoai.kr/"
MAIN_URL = "https://seochoai.kr/"
_EVERYONE_RE = re.compile(r"시민\s*누구나")


def open_to_citizens(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return bool(_EVERYONE_RE.search(soup.get_text(" ", strip=True)))


def collect(fetcher, now, max_items=None):
    html = fetcher.get(MAIN_URL).text
    data = read_event(html, "서초 AI 페스타")
    everyone = open_to_citizens(html)
    raw = raw_from_event(
        data, SOURCE_NAME, MAIN_URL, ["AI", "축제", "체험"],
        "일부 프로그램은 별도 사전예약이 있어 프로그램별 신청 상태는 공식 사이트에서 확인",
        eligibility="시민 누구나" if everyone else rules.UNKNOWN_TEXT, eligibilityVerified=everyone,
    )
    return CollectResult([raw], f"행사 {data['startDate']}~{data['endDate']} {data['venue']}")
