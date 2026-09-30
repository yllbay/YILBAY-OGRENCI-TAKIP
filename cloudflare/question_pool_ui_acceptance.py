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
    def revision_handler(context):
        def revision(route):
            response = context.request.get(BASE + '/api/internal/question-studio-fingerprint')
            assert response.ok
            route.fulfill(json={'revision': response.json()['sha256'], 'pending': False,
                                'durable': True, 'existing_content_locked': True})
        return revision
    for context in contexts:
        context.route('**/api/question-pool/revision', revision_handler(context))
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        pages.append(page)
        page.goto(BASE + '/?workspace=1', wait_until='domcontentloaded')
        expect(page.locator('#topicPlus')).to_be_visible(timeout=20000)
        expect(page.locator('[data-topic]')).to_have_count(1, timeout=10000)
        page.wait_for_function('typeof genesisPoolRevision!=="undefined"&&genesisPoolRevision!==null')
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
        assert first.locator('[data-question]').get_attribute('draggable') == 'true'
        expect(first.locator('[data-qdelete]')).to_have_count(1)
        first.wait_for_function('document.querySelector("[data-question] img")?.complete&&document.querySelector("[data-question] img").naturalWidth>0')

        # UI-created folder becomes visible in another independent profile without reload.
        first.locator('#topicPlus').click()
        first.locator('#shortName').fill('Arayuz Kabul')
        first.locator('#desc').fill('Disposable browser acceptance')
        first.locator('#formSave').click()
        expect(first.locator('[data-topic]')).to_have_count(2, timeout=20000)
        expect(second.locator('[data-topic]')).to_have_count(2, timeout=20000)
        first.locator('[data-topic]').first.click(button='right')
        for action in ('update', 'delete', 'toroot'):
            expect(first.locator(f'[data-act="{action}"]')).to_be_enabled()
        first.screenshot(path=str(OUT / 'pool-ui-desktop.png'), full_page=True)
        first.locator('#rightPane').click(position={'x':30,'y':500})  # Dismiss the existing context menu.
        # Delete the UI-created empty folder; the second profile must converge too.
        first.locator('[data-topic]').filter(has_text='ARAYUZ KABUL').click(button='right')
        first.once('dialog',lambda dialog:dialog.accept())
        first.locator('[data-act="delete"]').click()
        expect(first.locator('[data-topic]')).to_have_count(1,timeout=20000)
        expect(second.locator('[data-topic]')).to_have_count(1,timeout=20000)
        for page in (first,second):
            page.locator('[data-topic]').click()
            expect(page.locator('[data-question]')).to_have_count(1)
        first.once('dialog',lambda dialog:dialog.accept())
        first.locator('[data-qdelete]').click()
        expect(first.locator('[data-question]')).to_have_count(0,timeout=20000)
        expect(second.locator('[data-question]')).to_have_count(0,timeout=20000)
        # Create/delete an exam using the actual context menu and native dialogs.
        first.locator('[data-class]').first.click(button='right')
        first.once('dialog',lambda dialog:dialog.accept('Arayuz Sinav Silme'))
        first.locator('[data-exam-act="newexam"]').click()
        expect(first.locator('[data-exam]')).to_have_count(1,timeout=20000)
        second.wait_for_function('allTestFolders(S.testTree).some(c=>(c.exams||[]).length===1)')
        second.locator('[data-class]').click()
        expect(second.locator('[data-exam]')).to_have_count(1,timeout=20000)
        first.locator('[data-exam]').click(button='right')
        first.once('dialog',lambda dialog:dialog.accept())
        first.locator('[data-exam-act="deleteexam"]').click()
        expect(first.locator('[data-exam]')).to_have_count(0,timeout=20000)
        expect(second.locator('[data-exam]')).to_have_count(0,timeout=20000)
        first.locator('[data-class]').first.click(button='right')
        expect(first.locator('[data-exam-act="deleteclass"]')).to_be_enabled()
        first.once('dialog',lambda dialog:dialog.accept())
        first.locator('[data-exam-act="deleteclass"]').click()
        expect(first.locator('[data-class]')).to_have_count(0,timeout=20000)
        expect(second.locator('[data-class]')).to_have_count(0,timeout=20000)
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
            'user_deletes_enabled': True, 'second_profile_observed_deletes': True, 'page_errors': errors,
            'revision_transport': 'mocked-local-only; fingerprint from real disposable DB'
        }, indent=2))
        print('DISPOSABLE_BROWSER_USER_DELETES_SPLITTER_TWO_PROFILES_REFRESH_OK')
    finally:
        for index, page in enumerate(pages):
            page.screenshot(path=str(OUT / f'pool-ui-final-{index}.png'), full_page=True)
        for context in contexts:
            context.close()
        browser.close()
