from pathlib import Path

p=Path("cloudflare/package-runtime/index.js")
src=p.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_SPLITTER_CSS_V1"

if MARK in src:
    print("question studio splitter CSS already present")
    raise SystemExit(0)

# Retire both experimental workspace HTML overlays. They must not own workspace rendering.
for comment,cond in [
    (
      "// GENESIS_QUESTION_STUDIO_HORIZONTAL_V2",
      'if (request.method === "GET" && new URL(request.url).pathname === "/" && new URL(request.url).searchParams.get("workspace") === "1" && (headers.get("content-type") || "").includes("text/html")) {'
    ),
    (
      "// GENESIS_QUESTION_STUDIO_RESIZE_V1",
      'if (request.method === "GET" && new URL(request.url).pathname === "/" && new URL(request.url).searchParams.get("workspace") === "1" && (headers.get("content-type") || "").includes("text/html")) {'
    ),
]:
    pos=src.find(comment)
    if pos>=0:
        pcond=src.find(cond,pos)
        if pcond>=0:
            src=src[:pcond]+cond.replace("if (","if (false && ",1)+src[pcond+len(cond):]

anchor='''      // GENESIS_HOME_DASHBOARD_EDGE_V1
      // UI-only overlay: keep the current verified container image untouched.
'''
if anchor not in src:
    raise SystemExit("Home dashboard route anchor missing; refusing unsafe patch")

block=r'''      // GENESIS_QUESTION_STUDIO_SPLITTER_CSS_V1
      // The app already owns drag behavior via setupSplit(split1/split2).
      // Only restore a visible hit target and responsive header readability.
      if (request.method === "GET" && new URL(request.url).pathname === "/static/genesis-premium-0.11.7.css" && (headers.get("content-type") || "").includes("text/css")) {
        let css = await upstream.text();
        if (!css.includes("GENESIS_QUESTION_STUDIO_SPLITTER_CSS_V1")) {
          css += String.raw`

/* GENESIS_QUESTION_STUDIO_SPLITTER_CSS_V1 */
.genesis #workspace>.pane{
  min-width:0;
  container-type:inline-size;
}
.genesis #workspace>.splitter{
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
  user-select:none!important;
  z-index:30!important;
}
.genesis #workspace>.splitter span{
  display:block!important;
  width:5px!important;
  height:58px!important;
  overflow:hidden!important;
  font-size:0!important;
  border-radius:999px!important;
  background:#7c58a6!important;
  box-shadow:0 0 0 3px rgba(124,88,166,.14),0 3px 10px rgba(45,26,66,.18)!important;
  transition:width .12s ease,height .12s ease,background .12s ease,box-shadow .12s ease!important;
}
.genesis #workspace>.splitter:hover span,
.genesis #workspace>.splitter:active span{
  width:7px!important;
  height:76px!important;
  background:#5f348a!important;
  box-shadow:0 0 0 5px rgba(124,88,166,.2),0 5px 16px rgba(45,26,66,.28)!important;
}
.genesis #workspace>.splitter:hover{
  background:linear-gradient(90deg,transparent 0 4px,#c9b7dc 4px 12px,transparent 12px 16px)!important;
}
@container (max-width:390px){
  .pane-header{padding-left:10px!important;padding-right:8px!important;gap:7px!important}
  .head-title{font-size:17px!important;line-height:20px!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}
  .head-sub{max-width:120px!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}
  .head-actions{flex:0 0 auto!important;gap:3px!important}
  .head-btn{min-width:34px!important;width:34px!important;height:34px!important;padding:0!important}
}
@container (max-width:315px){
  .head-sub{display:none!important}
  .head-icon{transform:scale(.88);transform-origin:center}
}
`;
          headers.delete("content-length");
        }
        headers.set("Cache-Control","no-store, no-cache, must-revalidate, max-age=0");
        return new Response(css,{status:upstream.status,statusText:upstream.statusText,headers});
      }

'''
src=src.replace(anchor,block+anchor,1)
p.write_text(src,encoding="utf-8")
out=p.read_text(encoding="utf-8")
assert MARK in out
assert "/static/genesis-premium-0.11.7.css" in out
assert "container-type:inline-size" in out
assert "cursor:col-resize" in out
print("GENESIS native question studio splitters CSS enhancement: OK")
