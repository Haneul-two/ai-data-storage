"""AI FESTA(인공지능 페스타) 공식 사이트. 본문은 JS 앱이라 비어 있고, head의 JSON-LD @graph에 Event가 있다.
참가비·신청 마감은 제공되지 않아 '확인 필요'로 둔다."""
from .base import CollectResult
from .jsonld import raw_from_event, read_event

SOURCE_ID = "aifesta"
SOURCE_NAME = "AI FESTA"
SOURCE_URL = "https://www.aifesta.kr/"
MAIN_URL = "https://www.aifesta.kr/"


def collect(fetcher, now, max_items=None):
    data = read_event(fetcher.get(MAIN_URL).text, "AI FESTA")
    raw = raw_from_event(data, SOURCE_NAME, MAIN_URL, ["AI", "페스타", "전시"], "참가비와 신청 마감은 공식 사이트에서 확인 필요")
    return CollectResult([raw], f"행사 {data['startDate']}~{data['endDate']} {data['venue']}")
