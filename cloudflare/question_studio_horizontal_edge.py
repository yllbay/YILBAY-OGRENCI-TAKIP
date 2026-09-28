from pathlib import Path

p=Path("cloudflare/package-runtime/index.js")
src=p.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_RESIZE_V1"
OLD_MARK="GENESIS_QUESTION_STUDIO_HORIZONTAL_V2"

if MARK in src:
    print("question studio resize overlay already present")
    raise SystemExit(0)

# Retire the incorrect horizontal-scroll workspace route without touching backend/data.
if OLD_MARK in src:
    old_route='''      // GENESIS_QUESTION_STUDIO_HORIZONTAL_V2
      // Workspace-only UI overlay. No API, R2, Drive or container data mutation.
      if (request.method === "GET" && new URL(request.url).pathname === "/" && new URL(request.url).searchParams.get("workspace") === "1" && (headers.get("content-type") || "").includes("text/html")) {'''
    retired='''      // GENESIS_QUESTION_STUDIO_HORIZONTAL_RETIRED_V2
      // Retired: replaced by native splitter resize enhancement.
      if (false && request.method === "GET" && new URL(request.url).pathname === "/" && new URL(request.url).searchParams.get("workspace") === "1" && (headers.get("content-type") || "").includes("text/html")) {'''
    if old_route not in src:
        raise SystemExit("Horizontal V2 route shape changed; refusing unsafe retirement")
    src=src.replace(old_route,retired,1)

anchor='''      // GENESIS_HOME_DASHBOARD_EDGE_V1
      // UI-only overlay: keep the current verified container image untouched.
'''
if anchor not in src:
    raise SystemExit("Home dashboard route anchor missing; refusing unsafe patch")

block=r'''      // GENESIS_QUESTION_STUDIO_RESIZE_V1
      // Workspace-only UI enhancement: expose the app's native split1/split2 resize handles.
      if (request.method === "GET" && new URL(request.url).pathname === "/" && new URL(request.url).searchParams.get("workspace") === "1" && (headers.get("content-type") || "").includes("text/html")) {
        let html = await upstream.text();
        if (!html.includes("GENESIS_QUESTION_STUDIO_RESIZE_V1")) {
          const resizeOverlay = String.raw`
<style id="genesisQuestionStudioResizeStyle">
/* GENESIS_QUESTION_STUDIO_RESIZE_V1 */
body.gqr-ready #workspace{
  overflow:hidden!important;
}
body.gqr-ready #workspace>.pane{
  min-width:0!important;
  transition:box-shadow .12s ease,border-color .12s ease;
}
body.gqr-ready #workspace>.splitter{
  position:relative!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  width:16px!important;
  min-width:16px!important;
  max-width:16px!important;
  flex:0 0 16px!important;
  cursor:col-resize!important;
  background:linear-gradient(90deg,transparent 0 5px,#d8cde5 5px 11px,transparent 11px 16px)!important;
  z-index:80!important;
  user-select:none!important;
  touch-action:none!important;
}
body.gqr-ready #workspace>.splitter::before{
  content:""!important;
  width:5px!important;
  height:54px!important;
  border-radius:999px!important;
  background:#7d5aa9!important;
  box-shadow:0 0 0 3px rgba(125,90,169,.13),0 3px 10px rgba(47,26,70,.18)!important;
  transition:width .12s ease,height .12s ease,background .12s ease,box-shadow .12s ease!important;
}
body.gqr-ready #workspace>.splitter span{
  display:none!important;
}
body.gqr-ready #workspace>.splitter:hover::before,
body.gqr-resizing #workspace>.splitter.gqr-dragging::before{
  width:7px!important;
  height:72px!important;
  background:#61358f!important;
  box-shadow:0 0 0 5px rgba(125,90,169,.18),0 5px 16px rgba(47,26,70,.28)!important;
}
body.gqr-resizing,body.gqr-resizing *{
  cursor:col-resize!important;
  user-select:none!important;
}
body.gqr-ready #workspace>.pane.gqr-narrow .pane-header{
  padding-left:10px!important;
  padding-right:8px!important;
  gap:7px!important;
}
body.gqr-ready #workspace>.pane.gqr-narrow .head-title{
  font-size:17px!important;
  line-height:20px!important;
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
}
body.gqr-ready #workspace>.pane.gqr-narrow .head-sub{
  max-width:120px!important;
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
}
body.gqr-ready #workspace>.pane.gqr-narrow .head-actions{
  flex:0 0 auto!important;
  gap:3px!important;
}
body.gqr-ready #workspace>.pane.gqr-narrow .head-btn{
  min-width:34px!important;
  width:34px!important;
  height:34px!important;
  padding:0!important;
}
body.gqr-ready #workspace>.pane.gqr-very-narrow .head-sub{
  display:none!important;
}
body.gqr-ready #workspace>.pane.gqr-very-narrow .head-icon{
  transform:scale(.88);
  transform-origin:center;
}
body.gqr-resizing #workspace>.pane{
  box-shadow:inset 0 0 0 1px rgba(125,90,169,.26)!important;
}
</style>
<script id="genesisQuestionStudioResizeScript">
/* GENESIS_QUESTION_STUDIO_RESIZE_V1 */
(()=>{if(new URLSearchParams(location.search).get("workspace")!=="1")return;
let ro=null;
function classify(){
  ["leftPane","middlePane","rightPane"].forEach(id=>{
    const p=document.getElementById(id);if(!p)return;
    const w=p.getBoundingClientRect().width;
    p.classList.toggle("gqr-narrow",w<390);
    p.classList.toggle("gqr-very-narrow",w<315);
  });
}
function bindSplitter(s){
  if(!s||s.dataset.gqrBound==="1")return;
  s.dataset.gqrBound="1";
  s.setAttribute("role","separator");
  s.setAttribute("aria-orientation","vertical");
  s.title="Tut ve sağa/sola sürükle";
  s.addEventListener("mousedown",()=>{
    document.body.classList.add("gqr-resizing");
    s.classList.add("gqr-dragging");
  },true);
}
function finish(){
  document.body.classList.remove("gqr-resizing");
  document.querySelectorAll("#workspace>.splitter.gqr-dragging").forEach(x=>x.classList.remove("gqr-dragging"));
  classify();
}
function install(){
  const ws=document.getElementById("workspace");
  const p1=document.getElementById("leftPane"),p2=document.getElementById("middlePane"),p3=document.getElementById("rightPane");
  const s1=document.getElementById("split1"),s2=document.getElementById("split2");
  if(!ws||!p1||!p2||!p3||!s1||!s2)return false;
  document.body.classList.add("gqr-ready");
  bindSplitter(s1);bindSplitter(s2);
  if(!ro&&window.ResizeObserver){
    ro=new ResizeObserver(classify);ro.observe(p1);ro.observe(p2);ro.observe(p3);
  }
  classify();return true
}
document.addEventListener("mouseup",finish,true);
window.addEventListener("blur",finish);
install();
const mo=new MutationObserver(()=>install());
mo.observe(document.getElementById("app")||document.documentElement,{childList:true,subtree:true});
})();
</script>`;
          html = html.includes("</body>") ? html.replace("</body>", resizeOverlay + "</body>") : html + resizeOverlay;
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
assert "GENESIS_QUESTION_STUDIO_HORIZONTAL_RETIRED_V2" in out
assert 'id="split1"' not in out  # DOM remains owned by the application
assert "gqr-dragging" in out
assert "ResizeObserver" in out
print("GENESIS question studio native splitter enhancement: OK")
