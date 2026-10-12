"""확장한 행사 출처의 실제 화면 검증(로컬/공개 URL)."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8012/"
label = "expanded-public" if base.startswith("https:") else "expanded-local"
out = Path(__file__).resolve().parents[1] / "docs/evidence"
checks, errors = [], []
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    for width, height in [(1440, 900), (390, 844)]:
        context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + "?kind=event&status=all&mode=all&view=list")
        expect(page.locator(".opp").first).to_be_visible()
        for query, title in [("서초 AI 페스타", "2026 서초 AI 페스타"),
                             ("엔비디아 AI 데이 서울 2026", "NVIDIA AI Day Seoul 2026")]:
            page.locator("#q").fill(query)
            expect(page.locator(".opp")).to_have_count(1)
            expect(page.locator(".opp")).to_contain_text(title)
            checks.append({"width": width, "query": query, "passed": True})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        checks.append({"width": width, "overflow": False, "passed": True})
        page.locator("#q").fill("")
        page.screenshot(path=str(out / f"{label}-{width}.png"), scale="css")
        page.goto(base + "?kind=hackathon&status=all&mode=all&view=list&q=고용24")
        expect(page.locator(".opp").first).to_contain_text("고용24")
        checks.append({"width": width, "hackathon": True, "passed": True})
        context.close()
    browser.close()
assert not errors, errors
result = {"base": base, "checks": checks, "pageErrors": errors}
(out / f"{label}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"checks": len(checks), "errors": errors}))
