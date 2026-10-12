"""안전한 HTTP 조회: 허용목록·redirect 재검증·크기 상한·robots 캐시·요청 간격."""
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import requests

from .errors import FetchError
from .robots import RobotsRules
from .urlsafe import is_fetch_allowed

# 위비티는 URL이 포함된 긴 UA를 403으로 거절하므로 짧고 정직한 UA를 쓴다(브라우저 흉내 아님).
USER_AGENT = "ai-opportunity-board/1.0"
TIMEOUT = 15
MIN_INTERVAL = 1.0
MAX_BYTES = 2_500_000
MAX_REDIRECTS = 3
_REDIRECT_CODES = (301, 302, 303, 307, 308)


@dataclass
class FetchResult:
    text: str
    url: str


class Fetcher:
    def __init__(self, session=None, sleep=time.sleep, monotonic=time.monotonic, timeout=TIMEOUT,
                 min_interval=MIN_INTERVAL, max_bytes=MAX_BYTES, max_redirects=MAX_REDIRECTS, user_agent=USER_AGENT):
        self.session = session or requests.Session()
        self._sleep, self._monotonic = sleep, monotonic
        self.timeout, self.min_interval = timeout, min_interval
        self.max_bytes, self.max_redirects, self.user_agent = max_bytes, max_redirects, user_agent
        self._last = None
        self._robots = {}  # host -> RobotsRules | FetchError (이번 실행 동안만 캐시)

    def _throttle(self):
        if self._last is not None:
            wait = self.min_interval - (self._monotonic() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._monotonic()

    def _request(self, url, check_robots=True):
        """redirect를 직접 따라가며 매 단계 허용목록과 robots를 요청 전에 재검증한다. (status, body, final_url).
        robots.txt 자체를 가져올 때만 check_robots=False(재귀 방지)."""
        for _ in range(self.max_redirects + 1):
            if not is_fetch_allowed(url):
                raise FetchError("blocked", f"허용되지 않은 URL: {url}")
            if check_robots:
                self._check(url)
            self._throttle()
            try:
                resp = self.session.get(url, headers={"User-Agent": self.user_agent, "Accept": "*/*"},
                                        timeout=self.timeout, allow_redirects=False, stream=True)
            except requests.RequestException as exc:
                raise FetchError("error", f"요청 실패({type(exc).__name__}): {url}") from exc
            try:
                if resp.status_code in _REDIRECT_CODES:
                    location = resp.headers.get("Location")
                    if not location:
                        raise FetchError("error", f"Location 없는 redirect: {url}")
                    url = urljoin(url, location)
                    continue
                body = bytearray()
                for chunk in resp.iter_content(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > self.max_bytes:
                        raise FetchError("error", f"응답 크기 상한 초과: {url}")
                return resp.status_code, bytes(body), url
            finally:
                resp.close()
        raise FetchError("error", f"redirect 한도({self.max_redirects}) 초과")

    def _robots_for(self, url):
        host = urlsplit(url).hostname.lower()
        if host not in self._robots:
            try:
                status, body, _ = self._request(f"https://{host}/robots.txt", check_robots=False)
                if status == 200:
                    self._robots[host] = RobotsRules(body.decode("utf-8", "replace"))
                elif status in (404, 410):
                    self._robots[host] = RobotsRules("")
                else:
                    self._robots[host] = FetchError("blocked", f"robots.txt 확인 불가(HTTP {status}): {host}")
            except FetchError as exc:
                self._robots[host] = FetchError("blocked", f"robots.txt 확인 실패: {exc}")
        cached = self._robots[host]
        if isinstance(cached, FetchError):
            raise cached
        return cached

    def _check(self, url):
        parts = urlsplit(url)
        path = (parts.path or "/") + (("?" + parts.query) if parts.query else "")
        if not self._robots_for(url).allowed(self.user_agent, path):
            raise FetchError("blocked", f"robots.txt가 조회를 허용하지 않음: {parts.hostname}{parts.path}")

    def get(self, url):
        if not is_fetch_allowed(url):
            raise FetchError("blocked", f"허용되지 않은 URL: {url}")
        status, body, final = self._request(url)
        if status != 200:
            raise FetchError("error", f"HTTP {status}: {url}")
        return FetchResult(text=body.decode("utf-8", "replace"), url=final)
