"""공식 행사 페이지의 schema.org JSON-LD Event 읽기(서초·AI Festa 공용). 구조가 없거나 모호하면 빈 성공 대신 오류로 만든다."""
import json

from bs4 import BeautifulSoup

from .. import rules
from ..errors import StructureError

_MODES = {"OfflineEventAttendanceMode": "offline", "OnlineEventAttendanceMode": "online", "MixedEventAttendanceMode": "hybrid"}


def _nodes(value):
    if isinstance(value, list):
        for v in value:
            yield from _nodes(v)
    elif isinstance(value, dict):
        yield value
        yield from _nodes(value.get("@graph"))


def _is_event(node):
    kind = node.get("@type")
    return kind == "Event" or (isinstance(kind, list) and "Event" in kind)


def _text(value):
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        value = value.get("name")
    return rules.clean_text(value) if isinstance(value, str) else ""


def _moment(event, key, label):
    parsed = rules.parse_iso_datetime(event.get(key))
    if parsed is None:
        raise StructureError(f"{label} JSON-LD {key}가 없거나 시간대 포함 ISO 날짜가 아님")
    return parsed.astimezone(rules.SEOUL)


def _is_free(event):
    prices = [str(o.get("price")).strip() for o in _nodes(event.get("offers")) if o.get("price") is not None]
    if any(p not in ("0", "0.0", "0.00") for p in prices):
        return None
    return True if event.get("isAccessibleForFree") is True or prices else None


def read_event(html, label):
    """페이지의 JSON-LD에서 Event 하나를 읽어 정규화한 dict로 돌려준다."""
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.get_text())
        except ValueError as exc:
            raise StructureError(f"{label} JSON-LD를 해석하지 못함") from exc
        events.extend(n for n in _nodes(data) if _is_event(n))
    if not events:
        raise StructureError(f"{label} 페이지에 JSON-LD Event가 없음")
    if len(events) > 1:
        raise StructureError(f"{label} 페이지에 JSON-LD Event가 {len(events)}개라 어느 것이 대상인지 알 수 없음")
    event = events[0]
    name = _text(event.get("name"))
    if not name:
        raise StructureError(f"{label} JSON-LD Event에 name이 없음")
    start, end = _moment(event, "startDate", label), _moment(event, "endDate", label)
    if start > end:
        raise StructureError(f"{label} 행사 시작이 종료보다 늦음")
    location = event.get("location")
    location = location[0] if isinstance(location, list) and location else location
    place = location if isinstance(location, dict) else {}
    address = place.get("address") if isinstance(place.get("address"), dict) else {}
    country = address.get("addressCountry")
    if country is not None and str(country).upper() != "KR":
        raise StructureError(f"{label} 행사 국가가 KR이 아님: {country}")
    venue = _text(place.get("name")) or (_text(location) if isinstance(location, str) else "")
    region = _text(address.get("addressRegion"))
    mode = str(event.get("eventAttendanceMode") or "").rsplit("/", 1)[-1]
    return {
        "name": name, "startDate": start.date().isoformat(), "endDate": end.date().isoformat(),
        "startTime": start.strftime("%H:%M"), "endTime": end.strftime("%H:%M"),
        "venue": venue, "region": " ".join(p for p in (region, venue) if p) or "국내(장소 확인 필요)",
        "organizer": _text(event.get("organizer")) or None, "description": _text(event.get("description")),
        "mode": _MODES.get(mode, "unknown"), "free": _is_free(event),
        "cancelled": str(event.get("eventStatus") or "").rsplit("/", 1)[-1] == "EventCancelled",
    }


def schedule_note(data):
    """공식 개최 시각 표기. 접수 마감이 아니라 행사 시간이다."""
    if data["startDate"] == data["endDate"]:
        return f"공식 개최 {data['startTime']}~{data['endTime']}"
    return f"공식 개최 {data['startDate']} {data['startTime']} ~ {data['endDate']} {data['endTime']}"


def raw_from_event(data, source_name, url, tags, note, **over):
    """Event dict → 수집 원시 항목. 접수 기간·마감·자격·참가비는 근거가 있을 때만 over로 채운다."""
    raw = {
        "kind": "event", "title": data["name"], "organizer": data["organizer"],
        "description": data["description"] or data["name"], "tags": tags, "mode": data["mode"],
        "region": data["region"], "country": "KR", "startDate": data["startDate"], "endDate": data["endDate"],
        "registrationStartDate": None, "deadlineDate": None, "deadlineAt": None,
        "eligibility": rules.UNKNOWN_TEXT, "eligibilityVerified": False,
        "fee": "무료" if data["free"] else rules.UNKNOWN_TEXT, "prize": None,
        "url": url, "sourceUrl": url, "sourceName": source_name,
        "dateNote": f"{schedule_note(data)} (공식 사이트 기준). {note}", "sourceStatus": "unknown",
    }
    if data["cancelled"]:
        raw["sourceStatus"] = "closed"
        raw["dateNote"] = f"행사 취소 (공식 사이트 기준). {raw['dateNote']}"
    raw.update(over)
    return raw
