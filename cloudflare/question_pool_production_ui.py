"""Read-only production UI acceptance; no question/folder creation or edits."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = 'https://genesis-web-0152.yilbayonurcelik.workers.dev'
OUT = Path('/tmp/recovery/snapshot')

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    errors, mutations = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    def request_seen(request):
        if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'} and '/api/' in request.url:
            mutations.append(request.url.removeprefix(BASE).split('?')[0])
    page.on('request', request_seen)
    try:
        page.goto(BASE + '/', wait_until='domcontentloaded', timeout=45000)
        expect(page.locator('#edgeHomeQuestionStudio')).to_be_visible(timeout=20000)
        expect(page.locator('#edgeHomeCoachingStudio')).to_have_count(0)
        expect(page.locator('#edgeHomeCreateInstitution')).to_have_count(0)
        expect(page.locator('#closeBtn')).to_have_count(0)
        assert '/api/system/shutdown' not in mutations, mutations
        before = context.request.get(BASE + '/api/internal/question-studio-fingerprint').json()
        page.locator('#edgeHomeQuestionStudio').click()
        expect(page.locator('#topicPlus')).to_be_visible(timeout=20000)
        page.wait_for_function('typeof genesisPoolRevision!=="undefined"&&genesisPoolRevision!==null')
        script = page.locator('script[src*="app-0.10.7.js"]')
        assert 'pool-user-owned-20261001' in script.get_attribute('src')
        response = context.request.get(BASE + '/api/topics')
        assert response.ok and 'no-store' in response.headers.get('cache-control', '')
        splitter = page.locator('#split1')
        box = splitter.bounding_box()
        assert box and 15.5 <= box['width'] <= 16.5, box
        assert splitter.evaluate('(e)=>getComputedStyle(e).cursor') == 'col-resize'
        old_width = page.locator('#leftPane').bounding_box()['width']
        page.mouse.move(box['x']+8, box['y']+100)
        page.mouse.down()
        page.mouse.move(box['x']+68, box['y']+100, steps=8)
        page.mouse.up()
        new_width = page.locator('#leftPane').bounding_box()['width']
        assert abs(new_width-old_width) > 35, (old_width, new_width)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(OUT / 'production-question-studio.png'), full_page=True)
        after = context.request.get(BASE + '/api/internal/question-studio-fingerprint').json()
        assert before['sha256'] == after['sha256']
        assert all(path in {'/api/system/frontend-ready'} or path.startswith('/api/system/sound/')
                   for path in mutations), mutations
        assert not errors, errors
        (OUT / 'production-ui-acceptance.json').write_text(json.dumps({
            'ok': True, 'real_edge_home_navigation': True, 'pool_revision_ready': True,
            'splitter_width': box['width'], 'splitter_drag_delta': new_width-old_width,
            'fingerprint_unchanged': before['sha256'], 'page_errors': errors,
            'operational_mutations_only': mutations
        }, indent=2))
        print('PRODUCTION_READ_ONLY_STUDIO_NAVIGATION_SPLITTER_REVISION_OK')
    finally:
        page.screenshot(path=str(OUT / 'production-ui-final.png'), full_page=True)
        context.close()
        browser.close()
