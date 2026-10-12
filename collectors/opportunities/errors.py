"""수집 파이프라인 예외. status 값은 Source.status('error'|'blocked')와 같다."""


class SourceError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class FetchError(SourceError):
    pass


class StructureError(SourceError):
    """HTTP는 성공했지만 예상한 목록/상세 구조가 없는 응답."""

    def __init__(self, message):
        super().__init__("error", message)


class ExistingDataError(Exception):
    """기존 JSON이 손상됐거나 계약을 어긴 경우. 조용히 초기화하지 않고 중단한다."""
