"""소스 레지스트리. 순서는 중복 URL 충돌 시 우선순위다."""
from . import aisummit, dacon, devpost, wevity
from .base import SourceSpec


def default_sources():
    return [
        SourceSpec(m.SOURCE_ID, m.SOURCE_NAME, m.SOURCE_URL, m.collect)
        for m in (devpost, dacon, wevity, aisummit)
    ]
