from pathlib import Path

HTML = Path('/app/APP/frontend/dist/coaching-v2.html')
JS = Path('/app/APP/frontend/dist/coaching-v2.js')
CSS = Path('/app/APP/frontend/dist/coaching-v2.css')
MARKER = 'GENESIS_COACHING_SIDEBAR_ACTIONS'

def patch_html(path: Path) -> None:
    src = path.read_text(encoding='utf-8')
    if MARKER in src:
        return
    needle = '<div class="side-heading"><span>ÖĞRENCİLER</span><button id="addStudent" class="icon-btn" title="Öğrenci ekle">+</button></div><label class="search">'
    replacement = '<div class="side-heading"><span>ÖĞRENCİLER</span></div><div class="side-quick-actions" data-feature="GENESIS_COACHING_SIDEBAR_ACTIONS"><button id="addStudent" class="primary side-quick-btn" type="button">+ Öğrenci Ekle</button><button id="sideAddCourse" class="side-quick-btn" type="button">+ Ders Ekle</button></div><label class="search">'
    if needle not in src:
        raise SystemExit('Koçluk sidebar HTML patch point bulunamadı')
    path.write_text(src.replace(needle, replacement, 1), encoding='utf-8')

def patch_js(path: Path) -> None:
    src = path.read_text(encoding='utf-8')
    if MARKER in src:
        return
    needle = 'const handlers={addStudent:()=>studentForm(),emptyAdd:()=>studentForm(),'
    replacement = "const handlers={addStudent:()=>studentForm(),sideAddCourse:()=>{if(!state.selected||!state.dashboard){toast('Ders eklemek için önce bir öğrenci seçin.',true);return}/* GENESIS_COACHING_SIDEBAR_ACTIONS */setTab('courses');courseForm()},emptyAdd:()=>studentForm(),"
    if needle not in src:
        raise SystemExit('Koçluk sidebar JS patch point bulunamadı')
    path.write_text(src.replace(needle, replacement, 1), encoding='utf-8')

def patch_css(path: Path) -> None:
    src = path.read_text(encoding='utf-8')
    if MARKER in src:
        return
    addon = "\n/* GENESIS_COACHING_SIDEBAR_ACTIONS */\n.side-quick-actions{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;margin:0 0 12px}.side-quick-btn{min-width:0;min-height:40px;padding:9px 7px;font-size:11px;font-weight:800;white-space:nowrap}.side-quick-actions .primary{background:linear-gradient(135deg,#6748ba,#523795);border-color:#8062d0}\n"
    path.write_text(src + addon, encoding='utf-8')

for target in (HTML, JS, CSS):
    if not target.is_file():
        raise SystemExit(f'Koçluk frontend dosyası eksik: {target}')

patch_html(HTML)
patch_js(JS)
patch_css(CSS)
