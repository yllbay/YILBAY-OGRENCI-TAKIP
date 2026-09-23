from pathlib import Path
import os, re

ROOT = Path(os.environ.get('GENESIS_APP_ROOT', '/app/APP'))
FRONT = ROOT / 'frontend' / 'dist'
if not FRONT.exists():
    alt = ROOT / 'frontend'
    if alt.exists():
        FRONT = alt

HTML = FRONT / 'index.html'
JS = FRONT / 'app-0.10.7.js'
CSS = FRONT / 'genesis-home-dashboard-0.15.2.css'
for p in (HTML, JS):
    if not p.is_file():
        raise SystemExit(f'GENESIS home dashboard file missing: {p}')

MARK = 'GENESIS_HOME_DASHBOARD_V1'
ASSET_VER = '20260923-home-1'
CSS_NAME = 'genesis-home-dashboard-0.15.2.css'

html = HTML.read_text(encoding='utf-8')
if MARK not in html:
    link = f'<link rel="stylesheet" href="/static/{CSS_NAME}?v={ASSET_VER}">\n<!-- {MARK} -->\n'
    if '</head>' not in html:
        raise SystemExit('index.html </head> patch point missing')
    html = html.replace('</head>', link + '</head>', 1)
html = re.sub(r'/static/app-0\.10\.7\.js\?v=[^"\']+', f'/static/app-0.10.7.js?v={ASSET_VER}', html, count=1)
HTML.write_text(html, encoding='utf-8')

css = r'''/* GENESIS_HOME_DASHBOARD_V1
   Opening dashboard only. Existing GENESIS workspace remains intact and can be
   reached with ?workspace=1 while the landing page is being developed. */
.genesis.home-dashboard .workspace{
  gap:0!important;
}
.genesis.home-dashboard .pane.topics,
.genesis.home-dashboard .pane.questions,
.genesis.home-dashboard .pane.tests{
  flex:1 1 0!important;
  width:auto!important;
  min-width:0!important;
}
.genesis.home-dashboard .pane-body{
  overflow:visible!important;
}
.genesis.home-dashboard .pane-scroll{
  position:absolute!important;
  inset:0!important;
  padding:0!important;
  overflow:hidden!important;
}
.genesis.home-dashboard .home-empty{
  width:100%;
  height:100%;
  display:grid;
  place-items:center;
  padding:24px;
  color:#9aa6c2;
  font-size:15px;
  font-weight:400;
  letter-spacing:.1px;
  text-align:center;
  user-select:none;
}
.genesis.home-dashboard .head-icon,
.genesis.home-dashboard .head-btn,
.genesis.home-dashboard .fab{
  pointer-events:none!important;
  cursor:default!important;
}
.genesis.home-dashboard .splitter{
  pointer-events:none!important;
  cursor:default!important;
}
@media(max-width:1100px){
  .genesis.home-dashboard .head-title{font-size:20px!important}
  .genesis.home-dashboard .head-sub{font-size:13px!important}
}
'''
CSS.write_text(css, encoding='utf-8')

js = JS.read_text(encoding='utf-8')
if MARK not in js:
    anchor = 'function render(){\n'
    if anchor not in js:
        raise SystemExit('render() patch point missing')
    helper = r'''// GENESIS_HOME_DASHBOARD_V1
function genesisWorkspaceMode(){
 return new URLSearchParams(location.search).get("workspace")==="1";
}
function homeHeader(type,title,sub){
 const lead=type==="topics"?icons.hamb:icons.list;
 return `<div class="pane-header"><span class="head-icon" aria-hidden="true">${lead}</span><div class="head-copy"><div class="head-title">${title}</div><div class="head-sub">${sub}</div></div><div class="head-actions"><span class="head-btn dots" aria-hidden="true">⋮</span></div></div>`;
}
function homeDashboardHtml(){
 return `<div class="genesis home-dashboard">
 <div class="titlebar"><div class="brand-logo">${logo()}</div><div class="brand-copy"><div class="brand-name">GENESIS</div><div class="brand-sub">Akıllı Test Bankası Yönetim Sistemi</div></div>
 <div class="window-controls"><button class="win-btn" id="minBtn">−</button><button class="win-btn" id="maxBtn">□</button><button class="win-btn close" id="closeBtn">×</button></div></div>
 <div class="workspace" id="workspace">
 <section class="pane topics home-pane">${homeHeader("topics","Yönetim Paneli","Genel Bakış")}<div class="pane-body"><div class="pane-scroll"><div class="home-empty">Henüz veri yok</div></div><span class="fab" aria-hidden="true">+</span></div></section>
 <div class="splitter" aria-hidden="true"><span>Ⅱ</span></div>
 <section class="pane questions home-pane">${homeHeader("questions","İşlemler","Seçim Yap")}<div class="pane-body"><div class="pane-scroll"><div class="home-empty">Seçim yapılmadı</div></div><span class="fab" aria-hidden="true">+</span></div></section>
 <div class="splitter" aria-hidden="true"><span>Ⅱ</span></div>
 <section class="pane tests home-pane">${homeHeader("tests","Durum","Sistem")}<div class="pane-body"><div class="pane-scroll"><div class="home-empty">Henüz veri yok</div></div><span class="fab" aria-hidden="true">+</span></div></section>
 </div></div>`;
}
function bindHomeDashboard(){
 document.getElementById("closeBtn").onclick=async()=>{try{await api("/api/system/shutdown",{method:"POST"})}catch{}};
 document.getElementById("minBtn").onclick=()=>notice("Tarayıcı penceresini küçültmek için Windows düğmesini kullanın.");
 document.getElementById("maxBtn").onclick=async()=>{try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen()}catch{}};
}
'''
    js = js.replace(anchor, helper + anchor, 1)

    old = ''' if(S.builder){root.innerHTML=builderHtml();bindBuilder();return}\n root.innerHTML=`<div class="genesis">'''
    new = ''' if(S.builder){root.innerHTML=builderHtml();bindBuilder();return}\n if(!genesisWorkspaceMode()){root.innerHTML=homeDashboardHtml();bindHomeDashboard();return}\n root.innerHTML=`<div class="genesis">'''
    if old not in js:
        raise SystemExit('render dashboard insertion point missing')
    js = js.replace(old, new, 1)

    old_boot = '(window.GENESIS_AUTH_READY||Promise.resolve()).then(()=>refresh());'
    new_boot = '(window.GENESIS_AUTH_READY||Promise.resolve()).then(()=>genesisWorkspaceMode()?refresh():render());'
    if old_boot not in js:
        raise SystemExit('bootstrap patch point missing')
    js = js.replace(old_boot, new_boot, 1)
    JS.write_text(js, encoding='utf-8')

html = HTML.read_text(encoding='utf-8')
js = JS.read_text(encoding='utf-8')
css = CSS.read_text(encoding='utf-8')
checks = [
    (MARK in html, 'HTML marker missing'),
    (f'/static/{CSS_NAME}?v={ASSET_VER}' in html, 'home CSS link missing'),
    (f'/static/app-0.10.7.js?v={ASSET_VER}' in html, 'app cache-bust missing'),
    (MARK in js, 'JS marker missing'),
    ('Yönetim Paneli' in js and 'Genel Bakış' in js, 'dashboard panel 1 missing'),
    ('İşlemler' in js and 'Seçim Yap' in js, 'dashboard panel 2 missing'),
    ('Durum' in js and 'Sistem' in js, 'dashboard panel 3 missing'),
    ('genesisWorkspaceMode()?refresh():render()' in js, 'dashboard bootstrap missing'),
    ('?workspace=1' in css, 'workspace preservation note missing'),
]
for ok,msg in checks:
    if not ok:
        raise SystemExit(msg)
print('GENESIS opening dashboard patch: OK')
