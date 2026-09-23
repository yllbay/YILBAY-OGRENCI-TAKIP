from pathlib import Path

p=Path("cloudflare/package-runtime/index.js")
src=p.read_text(encoding="utf-8")
MARK="GENESIS_HOME_DASHBOARD_EDGE_V1"
if MARK in src:
    print("dashboard edge overlay already present")
    raise SystemExit(0)

needle='''      const upstream = await container.fetch(forwarded);
      const headers = new Headers(upstream.headers);
      headers.set("X-Request-ID", requestId);
      headers.set("X-Content-Type-Options", "nosniff");
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers
      });'''

replacement=r'''      const upstream = await container.fetch(forwarded);
      const headers = new Headers(upstream.headers);
      headers.set("X-Request-ID", requestId);
      headers.set("X-Content-Type-Options", "nosniff");

      // GENESIS_HOME_DASHBOARD_EDGE_V1
      // UI-only overlay: keep the current verified container image untouched.
      const url = new URL(request.url);
      const contentType = headers.get("content-type") || "";
      if (request.method === "GET" && url.pathname === "/" && contentType.includes("text/html")) {
        let html = await upstream.text();
        if (!html.includes("GENESIS_HOME_DASHBOARD_EDGE_V1")) {
          const overlay = String.raw`
<style id="genesisHomeDashboardEdgeStyle">
/* GENESIS_HOME_DASHBOARD_EDGE_V1 */
.genesis.home-dashboard .edge-home-menu{box-sizing:border-box;width:100%;height:100%;display:flex;flex-direction:column;align-items:stretch;gap:12px;padding:24px}
.genesis.home-dashboard .edge-home-menu button{width:100%;min-height:56px;display:flex;align-items:center;justify-content:flex-start;gap:12px;padding:0 18px;border:1px solid #334a73;border-radius:12px;background:linear-gradient(135deg,#15233d,#101b31);color:#eef3ff;font:inherit;font-size:15px;font-weight:750;letter-spacing:.1px;text-align:left;cursor:pointer;box-shadow:inset 0 1px 0 #ffffff0a;transition:border-color .15s ease,background .15s ease,transform .15s ease}
.genesis.home-dashboard .edge-home-menu button:hover{border-color:#7058b3;background:linear-gradient(135deg,#1a2c4b,#1c1b3b)}
.genesis.home-dashboard .edge-home-menu button:active{transform:translateY(1px)}
.genesis.home-dashboard .edge-home-menu .edge-icon{width:26px;height:26px;flex:0 0 26px;display:grid;place-items:center;border:1px solid #4a5f87;border-radius:8px;color:#b7c6e4;font-size:13px;line-height:1}
@media(max-width:760px){.genesis.home-dashboard .edge-home-menu{padding:16px}.genesis.home-dashboard .edge-home-menu button{min-height:50px;font-size:14px}}
</style>
<script id="genesisHomeDashboardEdgeScript">
/* GENESIS_HOME_DASHBOARD_EDGE_V1 */
(()=>{const install=()=>{if(document.getElementById("homeQuestionStudio")||document.getElementById("edgeHomeQuestionStudio"))return true;
const pane=document.querySelector(".genesis.home-dashboard .pane.topics .pane-scroll");if(!pane)return false;
pane.innerHTML='<div class="edge-home-menu"><button type="button" id="edgeHomeQuestionStudio"><span class="edge-icon">▤</span><span>Soru Stüdyosu</span></button><button type="button" id="edgeHomeCoachingStudio"><span class="edge-icon">◈</span><span>Koçluk Stüdyosu</span></button><button type="button" id="edgeHomeCreateInstitution"><span class="edge-icon">＋</span><span>Kurum Açma</span></button></div>';
document.getElementById("edgeHomeQuestionStudio").onclick=()=>location.assign("/?workspace=1");
document.getElementById("edgeHomeCoachingStudio").onclick=()=>location.assign("/coaching");
document.getElementById("edgeHomeCreateInstitution").onclick=()=>{if(typeof window.genesisCreateInstitution==="function"){window.genesisCreateInstitution();return}if(typeof window.notice==="function")window.notice("Kurum Açma ekranı şu anda kullanılamıyor.");};
return true};
if(!install()){const o=new MutationObserver(()=>{if(install())o.disconnect()});o.observe(document.documentElement,{childList:true,subtree:true});setTimeout(()=>o.disconnect(),15000)}})();
</script>`;
          html = html.includes("</body>") ? html.replace("</body>", overlay + "</body>") : html + overlay;
          headers.delete("content-length");
        }
        headers.set("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
        return new Response(html, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers
        });
      }
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers
      });'''

if needle not in src:
    raise SystemExit("Worker fetch patch point not found")
p.write_text(src.replace(needle,replacement,1),encoding="utf-8")
out=p.read_text(encoding="utf-8")
assert MARK in out
assert "Soru Stüdyosu" in out
assert "Koçluk Stüdyosu" in out
assert "Kurum Açma" in out
assert 'location.assign("/?workspace=1")' in out
assert 'location.assign("/coaching")' in out
assert 'window.genesisCreateInstitution' in out
print("GENESIS dashboard edge overlay patch: OK")
