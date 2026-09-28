from pathlib import Path

p=Path("cloudflare/package-runtime/index.js")
src=p.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_HORIZONTAL_V1"

if MARK in src:
    print("question studio horizontal overlay already present")
    raise SystemExit(0)

anchor='''      // GENESIS_HOME_DASHBOARD_EDGE_V1
      // UI-only overlay: keep the current verified container image untouched.
'''
if anchor not in src:
    raise SystemExit("Home dashboard route anchor missing; refusing unsafe patch")

block=r'''      // GENESIS_QUESTION_STUDIO_HORIZONTAL_V1
      // Workspace-only UI overlay. No API, R2, Drive or container data mutation.
      if (request.method === "GET" && url.pathname === "/" && url.searchParams.get("workspace") === "1" && contentType.includes("text/html")) {
        let html = await upstream.text();
        if (!html.includes("GENESIS_QUESTION_STUDIO_HORIZONTAL_V1")) {
          const questionStudioOverlay = String.raw`
<style id="genesisQuestionStudioHorizontalStyle">
/* GENESIS_QUESTION_STUDIO_HORIZONTAL_V1 */
body.gqs-ready .genesis{min-width:0!important}
body.gqs-ready #workspace.gqs-horizontal{
  overflow-x:auto!important;
  overflow-y:hidden!important;
  overscroll-behavior-x:contain;
  scroll-behavior:smooth;
  scroll-snap-type:x proximity;
  scrollbar-gutter:stable;
  touch-action:pan-x pan-y;
  padding-bottom:25px!important;
}
body.gqs-ready #workspace.gqs-horizontal::-webkit-scrollbar{height:14px}
body.gqs-ready #workspace.gqs-horizontal::-webkit-scrollbar-track{background:#ebe7f1;border-radius:999px}
body.gqs-ready #workspace.gqs-horizontal::-webkit-scrollbar-thumb{background:#8062aa;border:3px solid #ebe7f1;border-radius:999px}
body.gqs-ready #workspace.gqs-horizontal>.pane{
  flex:none!important;
  flex-shrink:0!important;
  scroll-snap-align:start;
  transition:opacity .16s ease,box-shadow .16s ease,border-color .16s ease,transform .16s ease;
}
body.gqs-ready #workspace.gqs-horizontal>#leftPane{width:clamp(350px,29vw,500px)!important;min-width:350px}
body.gqs-ready #workspace.gqs-horizontal>#middlePane{width:clamp(500px,39vw,720px)!important;min-width:500px}
body.gqs-ready #workspace.gqs-horizontal>#rightPane{width:clamp(400px,32vw,560px)!important;min-width:400px}
body.gqs-ready #workspace.gqs-horizontal>.splitter{flex:0 0 18px;scroll-snap-align:none}
body.gqs-ready #workspace.gqs-horizontal>.pane .pane-header{
  position:sticky;
  left:0;
  z-index:55;
  box-shadow:0 5px 16px rgba(50,24,89,.13);
  transition:filter .16s ease,opacity .16s ease,box-shadow .16s ease;
}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-active{
  border-color:#8054bd;
  box-shadow:0 12px 30px rgba(62,34,104,.20);
}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-active .pane-header{
  filter:saturate(1.12) brightness(1.03);
  box-shadow:0 6px 19px rgba(55,25,96,.26);
}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-dim{opacity:.91}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-partial .pane-header{
  min-width:min(420px,calc(100vw - 42px));
  padding-left:12px;
  padding-right:12px;
}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-partial .head-title{font-size:19px;line-height:23px}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-partial .head-sub{font-size:13px;line-height:17px;max-width:210px}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-partial .head-actions{gap:5px}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-partial .head-btn{
  background:rgba(255,255,255,.14);
  border-radius:9px;
}
body.gqs-ready #workspace.gqs-horizontal>.pane .head-copy{min-width:0}
body.gqs-ready #workspace.gqs-horizontal>.pane .head-actions{flex:0 0 auto}
body.gqs-ready #workspace.gqs-horizontal>.pane .head-btn{
  transition:background .16s ease,transform .16s ease;
}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-active .head-btn:hover{background:rgba(255,255,255,.16)}
body.gqs-ready #workspace.gqs-horizontal>.pane.gqs-active .pane-body>.fab{
  box-shadow:0 7px 18px rgba(62,27,110,.28);
}
#gqsDock{
  position:fixed;
  z-index:850;
  left:50%;
  bottom:18px;
  transform:translateX(-50%);
  display:flex;
  align-items:center;
  gap:7px;
  min-width:350px;
  max-width:min(720px,calc(100vw - 28px));
  height:54px;
  padding:6px 8px;
  border:1px solid rgba(117,88,158,.42);
  border-radius:16px;
  background:rgba(255,255,255,.94);
  box-shadow:0 12px 34px rgba(28,15,49,.24);
  backdrop-filter:blur(14px);
  color:#281b38;
}
#gqsDock .gqs-nav,#gqsDock .gqs-action{
  width:42px;
  height:42px;
  flex:0 0 42px;
  border:1px solid #d3c7e0;
  border-radius:11px;
  background:#f7f2fc;
  color:#542b82;
  font:700 20px "Segoe UI",Arial,sans-serif;
  cursor:pointer;
}
#gqsDock .gqs-action{
  background:linear-gradient(145deg,#6a35b9,#7b49ca);
  border-color:#7141be;
  color:#fff;
}
#gqsDock .gqs-action.menu{font-size:24px;line-height:1}
#gqsDock .gqs-action[hidden]{display:none!important}
#gqsDock .gqs-nav:disabled{opacity:.35;cursor:default}
#gqsDock .gqs-copy{min-width:0;flex:1;padding:0 6px;text-align:center}
#gqsDock .gqs-title{display:block;font-size:15px;font-weight:800;line-height:18px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#gqsDock .gqs-sub{display:block;margin-top:2px;font-size:11px;color:#6e6478;line-height:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media(max-width:760px){
  body.gqs-ready #workspace.gqs-horizontal>#leftPane{width:88vw!important;min-width:320px}
  body.gqs-ready #workspace.gqs-horizontal>#middlePane{width:92vw!important;min-width:360px}
  body.gqs-ready #workspace.gqs-horizontal>#rightPane{width:88vw!important;min-width:320px}
  #gqsDock{bottom:10px;min-width:0;width:calc(100vw - 20px);height:50px}
  #gqsDock .gqs-nav,#gqsDock .gqs-action{width:38px;height:38px;flex-basis:38px}
  #gqsDock .gqs-sub{display:none}
}
</style>
<script id="genesisQuestionStudioHorizontalScript">
/* GENESIS_QUESTION_STUDIO_HORIZONTAL_V1 */
(()=>{if(new URLSearchParams(location.search).get("workspace")!=="1")return;
const IDS=["leftPane","middlePane","rightPane"];
const TITLES={leftPane:"Konular",middlePane:"Konu Soruları",rightPane:"Testler"};
let savedX=0,raf=0,activeIndex=0,currentWs=null;

function ensureDock(){
  let d=document.getElementById("gqsDock");
  if(d)return d;
  d=document.createElement("div");
  d.id="gqsDock";
  d.setAttribute("role","navigation");
  d.setAttribute("aria-label","Soru Stüdyosu panel gezintisi");
  d.innerHTML='<button class="gqs-nav" id="gqsPrev" type="button" title="Önceki panel">‹</button><div class="gqs-copy"><span class="gqs-title" id="gqsTitle">Konular</span><span class="gqs-sub" id="gqsSub">Konu Seç</span></div><button class="gqs-action menu" id="gqsMenu" type="button" title="Panel menüsü" hidden>⋮</button><button class="gqs-action" id="gqsAdd" type="button" title="Bu panelde yeni kayıt">+</button><button class="gqs-nav" id="gqsNext" type="button" title="Sonraki panel">›</button>';
  document.body.appendChild(d);
  d.querySelector("#gqsPrev").onclick=()=>scrollToPane(activeIndex-1);
  d.querySelector("#gqsNext").onclick=()=>scrollToPane(activeIndex+1);
  d.querySelector("#gqsAdd").onclick=()=>{const p=document.getElementById(IDS[activeIndex]);const b=p&&p.querySelector(".pane-body>.fab");if(b)b.click()};
  d.querySelector("#gqsMenu").onclick=()=>{const p=document.getElementById(IDS[activeIndex]);const b=p&&p.querySelector(".head-btn,[data-head-menu]");if(b)b.click()};
  return d
}
function scrollToPane(i){
  const ws=document.getElementById("workspace");if(!ws)return;
  i=Math.max(0,Math.min(IDS.length-1,i));
  const p=document.getElementById(IDS[i]);if(!p)return;
  const target=Math.max(0,p.offsetLeft-ws.offsetLeft-8);
  ws.scrollTo({left:target,behavior:"smooth"})
}
function update(){
  raf=0;
  const ws=document.getElementById("workspace");if(!ws)return;
  const wr=ws.getBoundingClientRect();
  let best=-1,bestVisible=-1;
  IDS.forEach((id,i)=>{
    const p=document.getElementById(id);if(!p)return;
    const r=p.getBoundingClientRect();
    const visible=Math.max(0,Math.min(r.right,wr.right)-Math.max(r.left,wr.left));
    const ratio=visible/Math.max(1,r.width);
    if(visible>bestVisible){bestVisible=visible;best=i}
    p.classList.toggle("gqs-partial",ratio>0&&ratio<.72);
    p.classList.toggle("gqs-dim",ratio>0&&ratio<.48);
  });
  if(best>=0)activeIndex=best;
  IDS.forEach((id,i)=>{const p=document.getElementById(id);if(p)p.classList.toggle("gqs-active",i===activeIndex)});
  const p=document.getElementById(IDS[activeIndex]),dock=ensureDock();
  const title=p?.querySelector(".head-title")?.textContent?.trim()||TITLES[IDS[activeIndex]];
  const sub=p?.querySelector(".head-sub")?.textContent?.trim()||"";
  dock.querySelector("#gqsTitle").textContent=title;
  dock.querySelector("#gqsSub").textContent=sub;
  dock.querySelector("#gqsPrev").disabled=activeIndex===0;
  dock.querySelector("#gqsNext").disabled=activeIndex===IDS.length-1;
  const menu=p&&p.querySelector(".head-btn,[data-head-menu]");
  dock.querySelector("#gqsMenu").hidden=!menu;
}
function schedule(){if(!raf)raf=requestAnimationFrame(update)}
function install(){
  const ws=document.getElementById("workspace");
  if(!ws||!IDS.every(id=>document.getElementById(id)))return false;
  document.body.classList.add("gqs-ready");
  ws.classList.add("gqs-horizontal");
  if(currentWs!==ws){
    if(currentWs)savedX=currentWs.scrollLeft||savedX;
    currentWs=ws;
    ws.addEventListener("scroll",()=>{savedX=ws.scrollLeft;schedule()},{passive:true});
    ws.addEventListener("wheel",e=>{
      if(Math.abs(e.deltaY)>Math.abs(e.deltaX)&&e.shiftKey){e.preventDefault();ws.scrollLeft+=e.deltaY}
    },{passive:false});
    requestAnimationFrame(()=>{ws.scrollLeft=savedX;schedule()});
  }
  ensureDock();schedule();return true
}
install();
const mo=new MutationObserver(()=>{if(install())schedule()});
mo.observe(document.getElementById("app")||document.documentElement,{childList:true,subtree:true});
window.addEventListener("resize",schedule,{passive:true});
})();
</script>`;
          html = html.includes("</body>") ? html.replace("</body>", questionStudioOverlay + "</body>") : html + questionStudioOverlay;
          headers.delete("content-length");
        }
        headers.set("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
        return new Response(html, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers
        });
      }

'''
src=src.replace(anchor,block+anchor,1)
p.write_text(src,encoding="utf-8")
out=p.read_text(encoding="utf-8")
assert MARK in out
assert "gqs-horizontal" in out
assert "gqsDock" in out
assert "scrollToPane" in out
assert 'url.searchParams.get("workspace") === "1"' in out
print("GENESIS question studio horizontal overlay patch: OK")
