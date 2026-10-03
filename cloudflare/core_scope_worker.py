"""Keep the GENESIS edge home limited to verified core actions.

Pure Worker-source transform. Does not touch DB, R2 or container data.
Supports upgrading an already-deployed V1 overlay to V2.
"""
MARKER = "GENESIS_CORE_SCOPE_HOME_V2"
OLD_MARKER = "GENESIS_CORE_SCOPE_HOME_V1"

def patch(module: bytes) -> bytes:
    text = module.decode("utf-8")
    if MARKER in text:
        return module
    if "GENESIS_HOME_DASHBOARD_EDGE_V1" not in text:
        raise RuntimeError("GENESIS home edge overlay marker missing")

    old_buttons = '<button type="button" id="edgeHomeQuestionStudio"><span class="edge-icon">▤</span><span>Soru Stüdyosu</span></button><button type="button" id="edgeHomeCoachingStudio"><span class="edge-icon">◈</span><span>Koçluk Stüdyosu</span></button><button type="button" id="edgeHomeCreateInstitution"><span class="edge-icon">＋</span><span>Kurum Açma</span></button>'
    new_buttons = '<button type="button" id="edgeHomeQuestionStudio"><span class="edge-icon">▤</span><span>Soru Stüdyosu</span></button>'
    if old_buttons in text:
        text = text.replace(old_buttons, new_buttons, 1)
    elif new_buttons not in text:
        raise RuntimeError("GENESIS home edge button block changed")

    legacy_handlers = 'document.getElementById("edgeHomeQuestionStudio").onclick=()=>location.assign("/?workspace=1");\ndocument.getElementById("edgeHomeCoachingStudio").onclick=()=>location.assign("/coaching");\ndocument.getElementById("edgeHomeCreateInstitution").onclick=()=>{if(typeof window.genesisCreateInstitution==="function"){window.genesisCreateInstitution();return}if(typeof window.notice==="function")window.notice("Kurum Açma ekranı şu anda kullanılamıyor.");};'
    v1_handlers = 'document.getElementById("edgeHomeQuestionStudio").onclick=()=>location.assign("/?workspace=1");'
    v2_handlers = v1_handlers + '\nconst close=document.getElementById("closeBtn");if(close){close.onclick=()=>{};close.title="Web uygulamasında kapatma devre dışı";};'
    if legacy_handlers in text:
        text = text.replace(legacy_handlers, v2_handlers, 1)
    elif v2_handlers not in text:
        if v1_handlers not in text:
            raise RuntimeError("GENESIS home edge handler block changed")
        text = text.replace(v1_handlers, v2_handlers, 1)

    if OLD_MARKER in text:
        text = text.replace(f"/* {OLD_MARKER} */", f"/* {OLD_MARKER} */\n/* {MARKER} */", 1)
    else:
        anchor = '/* GENESIS_HOME_DASHBOARD_EDGE_V1 */\n(()=>{'
        if anchor not in text:
            raise RuntimeError("GENESIS edge script anchor missing")
        text = text.replace(anchor, f'/* GENESIS_HOME_DASHBOARD_EDGE_V1 */\n/* {MARKER} */\n(()=>{{', 1)

    assert "edgeHomeQuestionStudio" in text
    assert "edgeHomeCoachingStudio" not in text
    assert "edgeHomeCreateInstitution" not in text
    assert 'api("/api/system/shutdown"' not in text
    assert 'close.onclick' in text
    assert MARKER in text
    return text.encode("utf-8")
