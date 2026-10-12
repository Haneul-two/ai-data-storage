"""실데이터 UI 검증. 로컬 서버 8012, Playwright 및 설치된 Edge가 필요하다."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'evidence'
BASE = 'http://127.0.0.1:8012/'
checks = []
errors = []


def check(name, condition, detail=None):
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})
    if not condition:
        raise AssertionError(f'{name}: {detail}')


def overflow(page):
    return page.evaluate('''() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth,
      outside: [...document.querySelectorAll('body *')].filter(e => {
        const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
        return r.width && s.position !== 'absolute' && r.right > innerWidth + 1;
      }).map(e => e.className).slice(0, 10) })''')


def capture(page, name):
    page.screenshot(path=str(OUT / f'{name}.png'), scale='css')


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='msedge', headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
    page.goto(BASE)
    expect(page.locator('.opp').first).to_be_visible()
    total = page.locator('.opp').count()
    check('실데이터 표시', total > 0, total)
    check('데스크톱 CSS 너비', page.evaluate('()=>innerWidth') == 1440)
    capture(page, 'after-desktop')

    page.locator('#q').fill('항만')
    expect(page.locator('.opp')).to_have_count(1)
    check('검색 결과와 입력 포커스', page.locator('#q').evaluate('(e)=>e===document.activeElement'))
    check('검색 URL 반영', 'q=' in page.url)
    page.locator('#q').fill('없는검색결과XYZ')
    expect(page.locator('.opp')).to_have_count(0)
    expect(page.locator('#content').get_by_role('button', name='필터 초기화', exact=True)).to_be_visible()
    capture(page, 'no-results-desktop')
    page.locator('#content').get_by_role('button', name='필터 초기화', exact=True).click()
    expect(page.locator('.opp')).to_have_count(total)
    check('검색 초기화', page.locator('#q').input_value() == '')

    button = page.locator('.opp [data-save-id]').first
    saved_id = button.get_attribute('data-save-id')
    button.click()
    expect(button).to_have_attribute('aria-pressed', 'true')
    page.reload()
    expect(page.locator(f'.opp [data-save-id="{saved_id}"]')).to_have_attribute('aria-pressed', 'true')
    check('저장 재접속 유지', True)
    page.locator('#saved-toggle').click()
    expect(page.locator('.opp')).to_have_count(1)
    check('저장 목록 필터', True)
    page.locator('#saved-toggle').click()

    opener = page.locator('.opp [data-open-id]').first
    opener_id = opener.get_attribute('data-open-id')
    opener.click()
    dialog = page.locator('dialog')
    expect(dialog).to_be_visible()
    check('상세 초기 포커스', page.get_by_role('button', name='상세 정보 닫기').evaluate('(e)=>e===document.activeElement'))
    for _ in range(8):
        page.keyboard.press('Tab')
        check('상세 Tab 포커스 유지(배경 요소 진입 없음)', page.evaluate("()=>{const a=document.activeElement;return a===document.body||!!a.closest('dialog')}"))
    check('외부 링크 보안 속성', dialog.locator('a').evaluate_all("es=>es.every(e=>e.protocol==='https:'&&e.rel.includes('noopener')&&e.rel.includes('noreferrer'))"))
    capture(page, 'detail-desktop')
    page.keyboard.press('Escape')
    expect(dialog).not_to_be_visible()
    check('상세 닫기 포커스 복귀', page.locator(f'.opp [data-open-id="{opener_id}"]').evaluate('(e)=>e===document.activeElement'))

    page.get_by_role('button', name='달력', exact=True).click()
    expect(page.locator('.cal')).to_be_visible()
    title = page.locator('.cal-title').inner_text()
    page.get_by_role('button', name='다음 달', exact=True).click()
    check('달력 월 이동', page.locator('.cal-title').inner_text() != title)
    page.get_by_role('button', name='오늘', exact=True).click()
    check('달력 오늘 복귀', page.locator('.cal-title').inner_text() == title)
    capture(page, 'calendar-desktop')
    page.get_by_role('button', name='목록', exact=True).click()

    for width in (320, 375, 390, 414, 768, 1024, 1440):
        page.set_viewport_size({'width': width, 'height': 844 if width < 768 else 900})
        metrics = overflow(page)
        check(f'{width}px 가로 넘침', metrics['width'] == width and metrics['scroll'] <= width and not metrics['outside'], metrics)
        if width == 390:
            capture(page, 'after-mobile')
            page.locator('#rail-toggle').click()
            expect(page.locator('#rail-toggle')).to_have_attribute('aria-expanded', 'true')
            check('모바일 필터 펼침', True)
            page.locator('#rail-toggle').click()
            check('모바일 터치 목표', page.locator('button:visible').evaluate_all("es=>es.every(e=>e.getBoundingClientRect().height>=44)"))
            page.get_by_role('button', name='달력', exact=True).click()
            check('모바일 달력 넘침', overflow(page)['scroll'] <= width)
            capture(page, 'calendar-mobile')
            page.get_by_role('button', name='목록', exact=True).click()

    for mode in ('empty', 'error', 'loading'):
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(BASE + '?debug=' + mode)
        expect(page.locator('#debug-banner')).to_be_visible()
        if mode == 'empty':
            expect(page.get_by_text('아직 표시할 기회가 없어요', exact=True)).to_be_visible()
        elif mode == 'error':
            expect(page.get_by_role('button', name='다시 시도', exact=True)).to_be_visible()
        else:
            expect(page.locator('.skeleton')).to_be_visible()
        check(f'{mode} 상태', True)
        capture(page, mode + '-mobile')
        page.set_viewport_size({'width': 1440, 'height': 900})
        capture(page, mode + '-desktop')

    # 외부 호스트처럼 인식하는 localhost.에서 검증 파라미터가 무시되는지 실제 화면으로 확인.
    page.goto('http://localhost.:8012/?debug=empty&now=2000-01-01T00:00:00Z')
    expect(page.locator('.opp').first).to_be_visible()
    check('운영 호스트 debug 무시', page.locator('#debug-banner').is_hidden() and page.evaluate('()=>typeof window.__boardDebug') == 'undefined')
    check('브라우저 콘솔 오류 없음', not errors, errors)
    context.close()
    browser.close()

report = {'checks': checks, 'passed': sum(c['passed'] for c in checks), 'errors': errors}
(OUT / 'browser-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'passed': report['passed'], 'total': len(checks), 'errors': errors}))
