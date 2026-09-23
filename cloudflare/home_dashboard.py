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

MARK_V1 = 'GENESIS_HOME_DASHBOARD_V1'
MARK_V2 = 'GENESIS_HOME_DASHBOARD_V2'
ASSET_VER = '20260923-home-2'
CSS_NAME = 'genesis-home-dashboard-0.15.2.css'

html = HTML.read_text(encoding='utf-8')
css_href = f'/static/{CSS_NAME}?v={ASSET_VER}'
if CSS_NAME in html:
    html = re.sub(rf'/static/{re.escape(CSS_NAME)}\?v=[^"\']+', css_href, html, count=1)
else:
    if '</head>' not in html:
        raise SystemExit('index.html </head> patch point missing')
    html = html.replace('</head>', f'<link rel="stylesheet" href="{css_href}">\n</head>', 1)
if MARK_V1 not in html:
    html = html.replace('</head>', f'<!-- {MARK_V1} -->\n</head>', 1)
if MARK_V2 not in html:
    html = html.replace('</head>', f'<!-- {MARK_V2} -->\n</head>', 1)
html = re.sub(r'/static/app-0\.10\.7\.js\?v=[^"\']+', f'/static/app-0.10.7.js?v={ASSET_VER}', html, count=1)
HTML.write_text(html, encoding='utf-8')

css = r'''/* GENESIS_HOME_DASHBOARD_V1
   GENESIS_HOME_DASHBOARD_V2
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
.genesis.home-dashboard .home-menu{
  box-sizing:border-box;
  width:100%;
  height:100%;
  display:flex;
  flex-direction:column;
  align-items:stretch;
  gap:12px;
  padding:24px;
}
.genesis.home-dashboard .home-menu-button{
  width:100%;
  min-height:56px;
  display:flex;
  align-items:center;
  justify-content:flex-start;
  gap:12px;
  padding:0 18px;
  border:1px solid #334a73;
  border-radius:12px;
  background:linear-gradient(135deg,#15233d,#101b31);
  color:#eef3ff;
  font:inherit;
  font-size:15px;
  font-weight:750;
  letter-spacing:.1px;
  text-align:left;
  cursor:pointer;
  box-shadow:inset 0 1px 0 #ffffff0a;
  transition:border-color .15s ease,background .15s ease,transform .15s ease;
}
.genesis.home-dashboard .home-menu-button:hover{
  border-color:#7058b3;
  background:linear-gradient(135deg,#1a2c4b,#1c1b3b);
}
.genesis.home-dashboard .home-menu-button:active{
  transform:translateY(1px);
}
.genesis.home-dashboard .home-menu-icon{
  width:26px;
  height:26px;
  flex:0 0 26px;
  display:grid;
  place-items:center;
  border:1px solid #4a5f87;
  border-radius:8px;
  color:#b7c6e4;
  font-size:13px;
  line-height:1;
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
@media(max-width:760px){
  .genesis.home-dashboard .home-menu{padding:16px}
  .genesis.home-dashboard .home-menu-button{min-height:50px;font-size:14px}
}
'''
CSS.write_text(css, encoding='utf-8')

js = JS.read_text(encoding='utf-8')
helper = r'''// GENESIS_HOME_DASHBOARD_V1
// GENESIS_HOME_DASHBOARD_V2
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
 <section class="pane topics home-pane">${homeHeader("topics","Yönetim Paneli","Genel Bakış")}<div class="pane-body"><div class="pane-scroll"><div class="home-menu">
   <button type="button" class="home-menu-button" id="homeQuestionStudio"><span class="home-menu-icon">▤</span><span>Soru Stüdyosu</span></button>
   <button type="button" class="home-menu-button" id="homeCoachingStudio"><span class="home-menu-icon">◈</span><span>Koçluk Stüdyosu</span></button>
   <button type="button" class="home-menu-button" id="homeCreateInstitution"><span class="home-menu-icon">＋</span><span>Kurum Açma</span></button>
 </div></div><span class="fab" aria-hidden="true">+</span></div></section>
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
 const question=document.getElementById("homeQuestionStudio");
 const coaching=document.getElementById("homeCoachingStudio");
 const institution=document.getElementById("homeCreateInstitution");
 if(question)question.onclick=()=>location.assign("/?workspace=1");
 if(coaching)coaching.onclick=()=>location.assign("/coaching");
 if(institution)institution.onclick=()=>{
   if(typeof window.genesisCreateInstitution==="function"){window.genesisCreateInstitution();return}
   notice("Kurum Açma ekranı şu anda kullanılamıyor.");
 };
}
'''

if MARK_V2 not in js:
    if MARK_V1 in js:
        pat = re.compile(r'// GENESIS_HOME_DASHBOARD_V1\nfunction genesisWorkspaceMode\(\)\{.*?\n\}\n(?=function render\(\)\{)', re.S)
        js2, count = pat.subn(helper, js, count=1)
        if count != 1:
            raise SystemExit(f'Existing dashboard V1 helper replacement failed: {count}')
        js = js2
    else:
        anchor = 'function render(){\n'
        if anchor not in js:
            raise SystemExit('render() patch point missing')
        js = js.replace(anchor, helper + anchor, 1)

if 'if(!genesisWorkspaceMode()){root.innerHTML=homeDashboardHtml();bindHomeDashboard();return}' not in js:
    old = ''' if(S.builder){root.innerHTML=builderHtml();bindBuilder();return}\n root.innerHTML=`<div class="genesis">`'''
    new = ''' if(S.builder){root.innerHTML=builderHtml();bindBuilder();return}\n if(!genesisWorkspaceMode()){root.innerHTML=homeDashboardHtml();bindHomeDashboard();return}\n root.innerHTML=`<div class="genesis">`'''
    if old not in js:
        raise SystemExit('render dashboard insertion point missing')
    js = js.replace(old, new, 1)

if 'genesisWorkspaceMode()?refresh():render()' not in js:
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
    (MARK_V1 in html and MARK_V2 in html, 'HTML dashboard markers missing'),
    (f'/static/{CSS_NAME}?v={ASSET_VER}' in html, 'home CSS link missing'),
    (f'/static/app-0.10.7.js?v={ASSET_VER}' in html, 'app cache-bust missing'),
    (MARK_V1 in js and MARK_V2 in js, 'JS dashboard markers missing'),
    ('Yönetim Paneli' in js and 'Genel Bakış' in js, 'dashboard panel 1 missing'),
    ('İşlemler' in js and 'Seçim Yap' in js, 'dashboard panel 2 missing'),
    ('Durum' in js and 'Sistem' in js, 'dashboard panel 3 missing'),
    ('id="homeQuestionStudio"' in js and 'Soru Stüdyosu' in js, 'Soru Stüdyosu button missing'),
    ('id="homeCoachingStudio"' in js and 'Koçluk Stüdyosu' in js, 'Koçluk Stüdyosu button missing'),
    ('id="homeCreateInstitution"' in js and 'Kurum Açma' in js, 'Kurum Açma button missing'),
    ('location.assign("/?workspace=1")' in js, 'Soru Stüdyosu navigation missing'),
    ('location.assign("/coaching")' in js, 'Koçluk Stüdyosu navigation missing'),
    ('window.genesisCreateInstitution()' in js, 'Kurum Açma action missing'),
    ('genesisWorkspaceMode()?refresh():render()' in js, 'dashboard bootstrap missing'),
    (MARK_V2 in css and '.home-menu-button' in css, 'dashboard V2 CSS missing'),
    ('?workspace=1' in css, 'workspace preservation note missing'),
]
for ok,msg in checks:
    if not ok:
        raise SystemExit(msg)
print('GENESIS opening dashboard V2 patch: OK')
