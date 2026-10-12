"""소스 어댑터 공통 타입과 헬퍼."""
from dataclasses import dataclass, field
from typing import Callable

from ..errors import FetchError, SourceError

SOURCE_LIMIT = 20  # 소스당 하드 상한


@dataclass
class CollectResult:
    items: list = field(default_factory=list)
    message: str = ""
    closed_source_urls: list = field(default_factory=list)  # 목록에서 마감으로 확인한 AI 관련 행의 상세 URL(저장 안 함, 기존 항목 마감 전파용)


@dataclass
class SourceSpec:
    id: str
    name: str
    url: str  # 사용자에게 보여줄 목록 페이지
    collect: Callable  # (fetcher, now, max_items) -> CollectResult


def domestic_region(mode):
    return {"online": "국내 온라인", "offline": "국내 오프라인", "hybrid": "국내 온·오프라인"}.get(mode, "미정")


def effective_limit(max_items):
    return SOURCE_LIMIT if max_items is None else max(0, min(max_items, SOURCE_LIMIT))


def fail_if_every_fetch_failed(attempted, failures, label):
    """후보가 있었는데 상세 조회가 전부 실패하면 부분 성공이 아니라 소스 오류로 본다."""
    if attempted and len(failures) == attempted:
        first = failures[0]
        status = first.status if isinstance(first, FetchError) else "error"
        raise SourceError(status, f"{label} 상세 {attempted}건 모두 조회 실패: {first}")
