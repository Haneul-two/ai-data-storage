"""Bounded, read-only diagnosis of the official AI Summit response."""
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.opportunities.http import Fetcher, MAX_BYTES
from collectors.opportunities.sources import aisummit


def main():
    page = Fetcher().get(aisummit.MAIN_URL, prefix_bytes=MAX_BYTES)
    for limit in (1_000_000, aisummit.PREFIX_BYTES):
        text = page.text.encode("utf-8")[:limit].decode("utf-8", "replace")
        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        root = soup.select_one("main") or soup.body or soup
        visible = root.get_text("\n", strip=True)
        try:
            data = aisummit.parse_main(text)
            parsed = {key: data[key] for key in ("startDate", "endDate", "titleYear")}
        except Exception as exc:
            parsed = {"error": type(exc).__name__}
        print(json.dumps({
            "limit": limit, "bytes": len(text.encode("utf-8")), "truncated": page.truncated,
            "bodyOffset": text.find("<body"), "mainOffset": text.find("<main"),
            "offsetUnit": "unicode characters",
            "visibleChars": len(visible), "parsed": parsed,
            "yearCounts": {year: visible.count(year) for year in ("2026", "2027")},
        }))


if __name__ == "__main__":
    main()
