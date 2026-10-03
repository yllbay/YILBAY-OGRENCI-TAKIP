"""Keep the GENESIS edge home limited to verified core actions.

V4 replaces the fragile pane mutation with a body-level launcher that survives
native root re-renders. Pure Worker-source transform; no DB/R2 mutation.
"""
import re

MARKER = "GENESIS_CORE_SCOPE_HOME_V4"
OLD_MARKERS = (
    "GENESIS_CORE_SCOPE_HOME_V1",
    "GENESIS_CORE_SCOPE_HOME_V2",
    "GENESIS_CORE_SCOPE_HOME_V3",
)

STABLE_OVERLAY = r'''<style id="genesisHomeDashboardEdgeStyle">
/* GENESIS_HOME_DASHBOARD_EDGE_V1 */
/* GENESIS_CORE_SCOPE_HOME_V4 */
#genesisCoreHomeLauncher{position:fixed;z-index:2147483000;left:24px;top:118px;width:min(340px,calc(100vw - 48px));box-sizing:border-box;padding:18px;border:1px solid #334a73;border-radius:14px;background:#101b31;box-shadow:0 14px 40px #0008}
#genesisCoreHomeLauncher[hidden]{display:none!important}
#genesisCoreHomeLauncher .edge-home-title{margin:0 0 12px;color:#9aa6c2;font:600 12px/1.2 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase}
#genesisCoreHomeLauncher a{box-sizing:border-box;width:100%;min-height:56px;display:flex;align-items:center;justify-content:flex-start;gap:12px;padding:0 18px;border:1px solid #4a5f87;border-radius:12px;background:linear-gradient(135deg,#15233d,#101b31);color:#eef3ff;text-decoration:none;font:750 15px/1 system-ui,sans-serif}
#genesisCoreHomeLauncher a:hover{border-color:#7058b3;background:linear-gradient(135deg,#1a2c4b,#1c1b3b)}
#genesisCoreHomeLauncher .edge-icon{width:26px;height:26px;flex:0 0 26px;display:grid;place-items:center;border:1px solid #4a5f87;border-radius:8px;color:#b7c6e4;font-size:13px}
#closeBtn{display:none!important;pointer-events:none!important}
@media(max-width:760px){#genesisCoreHomeLauncher{left:16px;top:104px;width:calc(100vw - 32px);padding:14px}}
</style>
<div id="genesisCoreHomeLauncher" hidden aria-label="GENESIS ana menü"><div class="edge-home-title">Yönetim Paneli</div><a id="edgeHomeQuestionStudio" href="/?workspace=1"><span class="edge-icon">▤</span><span>Soru Stüdyosu</span></a></div>
<script id="genesisHomeDashboardEdgeScript">
/* GENESIS_HOME_DASHBOARD_EDGE_V1 */
/* GENESIS_CORE_SCOPE_HOME_V4 */
(()=>{const launcher=document.getElementById("genesisCoreHomeLauncher");const sync=()=>{const home=!!document.querySelector(".genesis.home-dashboard");if(launcher)launcher.hidden=!home;const close=document.getElementById("closeBtn");if(close)close.remove()};sync();const o=new MutationObserver(sync);o.observe(document.documentElement,{childList:true,subtree:true});setTimeout(()=>o.disconnect(),15000)})();
</script>'''

def patch(module: bytes) -> bytes:
    text = module.decode("utf-8")
    if MARKER in text:
        return module
    if "GENESIS_HOME_DASHBOARD_EDGE_V1" not in text:
        raise RuntimeError("GENESIS home edge overlay marker missing")

    # The overlay lives inside a String.raw template. Replace its complete
    # style/launcher/script payload so previous V1-V3 timing assumptions cannot leak.
    pattern = re.compile(
        r'<style id="genesisHomeDashboardEdgeStyle">.*?</script>',
        re.S,
    )
    text, count = pattern.subn(STABLE_OVERLAY, text, count=1)
    if count != 1:
        raise RuntimeError(f"GENESIS edge overlay replacement failed: {count}")

    # Do not inject the launcher into workspace mode; the native workspace owns that page.
    condition = 'request.method === "GET" && url.pathname === "/" && contentType.includes("text/html")'
    scoped = 'request.method === "GET" && url.pathname === "/" && url.searchParams.get("workspace") !== "1" && contentType.includes("text/html")'
    if scoped not in text:
        if condition not in text:
            raise RuntimeError("GENESIS root overlay condition changed")
        text = text.replace(condition, scoped, 1)

    for old in OLD_MARKERS:
        text = text.replace(f"/* {old} */", f"/* {old} */")
    assert MARKER in text
    assert 'id="edgeHomeQuestionStudio"' in text
    assert "edgeHomeCoachingStudio" not in text
    assert "edgeHomeCreateInstitution" not in text
    assert 'id="closeBtn"' not in STABLE_OVERLAY
    assert '#closeBtn{display:none!important;pointer-events:none!important}' in text
    assert 'MutationObserver(sync)' in text
    assert 'url.searchParams.get("workspace") !== "1"' in text
    return text.encode("utf-8")
