"""Read-only AI EXPO robots diagnostics; never fetch content without permission."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.opportunities.http import Fetcher
from collectors.opportunities.sources import aiexpo


def main():
    fetcher = Fetcher()
    for attempt in range(2):
        status, body, _, _ = fetcher._request(aiexpo.SOURCE_URL + "robots.txt", check_robots=False)
        text = body.decode("utf-8", "replace").lower()
        print(json.dumps({"attempt": attempt + 1, "status": status, "bytes": len(body),
                          "html": text.lstrip().startswith("<"),
                          "challenge": any(token in text for token in ("awswaf", "challenge", "captcha"))}))
        if status in (200, 404, 410):
            break
    try:
        result = aiexpo.collect(fetcher, None)
        print(json.dumps({"collect": "ok", "items": len(result.items),
                          "sourceUrl": result.items[0]["sourceUrl"],
                          "startDate": result.items[0]["startDate"], "endDate": result.items[0]["endDate"]}))
    except Exception as exc:
        print(json.dumps({"collect": "failed", "error": str(exc)}))


if __name__ == "__main__":
    main()
