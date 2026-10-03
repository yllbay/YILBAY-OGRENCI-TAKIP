"""Remove deferred/unimplemented launch actions from the GENESIS edge home overlay.

Pure Worker-source transform. Does not touch DB, R2 or container data.
"""
MARKER = "GENESIS_CORE_SCOPE_HOME_V1"

def patch(module: bytes) -> bytes:
    text = module.decode("utf-8")
    if MARKER in text:
        return module
    if "GENESIS_HOME_DASHBOARD_EDGE_V1" not in text:
        raise RuntimeError("GENESIS home edge overlay marker missing")

    old_buttons = '<button type="button" id="edgeHomeQuestionStudio"><span class="edge-icon">▤</span><span>Soru Stüdyosu</span></button><button type="button" id="edgeHomeCoachingStudio"><span class="edge-icon">◈</span><span>Koçluk Stüdyosu</span></button><button type="button" id="edgeHomeCreateInstitution"><span class="edge-icon">＋</span><span>Kurum Açma</span></button>'
    new_buttons = '<button type="button" id="edgeHomeQuestionStudio"><span class="edge-icon">▤</span><span>Soru Stüdyosu</span></button>'
    if old_buttons not in text:
        raise RuntimeError("GENESIS home edge button block changed")
    text = text.replace(old_buttons, new_buttons, 1)

    old_handlers = 'document.getElementById("edgeHomeQuestionStudio").onclick=()=>location.assign("/?workspace=1");\ndocument.getElementById("edgeHomeCoachingStudio").onclick=()=>location.assign("/coaching");\ndocument.getElementById("edgeHomeCreateInstitution").onclick=()=>{if(typeof window.genesisCreateInstitution==="function"){window.genesisCreateInstitution();return}if(typeof window.notice==="function")window.notice("Kurum Açma ekranı şu anda kullanılamıyor.");};'
    new_handlers = 'document.getElementById("edgeHomeQuestionStudio").onclick=()=>location.assign("/?workspace=1");'
    if old_handlers not in text:
        raise RuntimeError("GENESIS home edge handler block changed")
    text = text.replace(old_handlers, new_handlers, 1)

    # Keep a durable marker inside the existing edge script.
    anchor = '/* GENESIS_HOME_DASHBOARD_EDGE_V1 */\n(()=>{'
    if anchor not in text:
        raise RuntimeError("GENESIS edge script anchor missing")
    text = text.replace(anchor, f'/* GENESIS_HOME_DASHBOARD_EDGE_V1 */\n/* {MARKER} */\n(()=>{{', 1)

    assert "edgeHomeQuestionStudio" in text
    assert "edgeHomeCoachingStudio" not in text
    assert "edgeHomeCreateInstitution" not in text
    assert "genesisCreateInstitution" not in text
    return text.encode("utf-8")
