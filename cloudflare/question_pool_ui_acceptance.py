"""Browser acceptance against disposable localhost only; never production.

Local mode has no R2 revision service. Only that response is mocked using the
real disposable DB fingerprint. All folder writes, images and UI are real.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = 'http://127.0.0.1:18000'
OUT = Path('/tmp/recovery/snapshot')
OUT.mkdir(parents=True, exist_ok=True)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    contexts = [browser.new_context(viewport={'width': 1440, 'height': 900}) for _ in range(2)]
    pages = []
    errors = []
    for context in contexts:
        def revision(route, context=context):
            response = context.request.get(BASE + '/api/internal/question-studio-fingerprint')
            assert response.ok
            route.fulfill(json={'revision': response.json()['sha256'], 'pending': False,
                                'durable': True, 'existing_content_locked': True})
        context.route('**/api/question-pool/revision', revision)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        pages.append(page)
        page.goto(BASE + '/?workspace=1', wait_until='domcontentloaded')
        expect(page.locator('#topicPlus')).to_be_visible(timeout=20000)
        expect(page.locator('[data-topic]')).to_have_count(1, timeout=10000)
    first, second = pages
    try:
        # Real splitter hit area, cursor and drag; whole workspace has no scrollbar.
        splitter = first.locator('#split1')
        box = splitter.bounding_box()
        assert box and abs(box['width'] - 16) < .5, box
        assert splitter.evaluate('(e)=>getComputedStyle(e).cursor') == 'col-resize'
        old_width = first.locator('#leftPane').bounding_box()['width']
        first.mouse.move(box['x'] + 8, box['y'] + 100)
        first.mouse.down()
        first.mouse.move(box['x'] + 68, box['y'] + 100, steps=8)
        first.mouse.up()
        new_width = first.locator('#leftPane').bounding_box()['width']
        assert new_width - old_width > 45, (old_width, new_width)
        assert first.locator('#workspace').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
        assert first.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        first.locator('[data-topic]').click()
        expect(first.locator('[data-question]')).to_have_count(1)
        assert first.locator('[data-question]').get_attribute('draggable') == 'false'
        expect(first.locator('[data-qdelete]')).to_have_count(0)
        assert first.locator('[data-question] img').first.evaluate('(e)=>e.complete&&e.naturalWidth>0')

        # UI-created folder becomes visible in another independent profile without reload.
        first.locator('#topicPlus').click()
        first.locator('#shortName').fill('Arayuz Kabul')
        first.locator('#desc').fill('Disposable browser acceptance')
        first.locator('#formSave').click()
        expect(first.locator('[data-topic]')).to_have_count(2, timeout=20000)
        expect(second.locator('[data-topic]')).to_have_count(2, timeout=20000)
        first.locator('[data-topic]').first.click(button='right')
        for action in ('update', 'delete', 'toroot'):
            expect(first.locator(f'[data-act="{action}"]')).to_be_disabled()
        first.screenshot(path=str(OUT / 'pool-ui-desktop.png'), full_page=True)
        first.set_viewport_size({'width': 800, 'height': 900})
        first.reload(wait_until='domcontentloaded')
        expect(first.locator('#workspace')).to_be_visible()
        assert first.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        assert first.locator('#workspace').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
        first.screenshot(path=str(OUT / 'pool-ui-narrow.png'), full_page=True)
        assert not errors, errors
        (OUT / 'pool-ui-acceptance.json').write_text(json.dumps({
            'ok': True, 'splitter_width': box['width'], 'splitter_drag_delta': new_width-old_width,
            'second_profile_refreshed': True, 'no_horizontal_workspace_scroll': True,
            'existing_mutations_disabled': True, 'page_errors': errors,
            'revision_transport': 'mocked-local-only; fingerprint from real disposable DB'
        }, indent=2))
        print('DISPOSABLE_BROWSER_SPLITTER_IMMUTABILITY_TWO_PROFILES_REFRESH_OK')
    finally:
        for index, page in enumerate(pages):
            page.screenshot(path=str(OUT / f'pool-ui-final-{index}.png'), full_page=True)
        for context in contexts:
            context.close()
        browser.close()
