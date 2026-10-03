"""Keep the GENESIS edge home limited to verified core actions.

Pure Worker-source transform. Does not touch DB, R2 or container data.
Supports upgrading deployed V1/V2 overlays to V3.
"""
MARKER = "GENESIS_CORE_SCOPE_HOME_V3"
OLD_MARKERS = ("GENESIS_CORE_SCOPE_HOME_V1", "GENESIS_CORE_SCOPE_HOME_V2")

def patch(module: bytes) -> bytes:
    text = module.decode("utf-8")
    if MARKER in text:
        return module
    if "GENESIS_HOME_DASHBOARD_EDGE_V1" not in text:
        raise RuntimeError("GENESIS home edge overlay marker missing")

    legacy_buttons = '<button type="button" id="edgeHomeQuestionStudio"><span class="edge-icon">▤</span><span>Soru Stüdyosu</span></button><button type="button" id="edgeHomeCoachingStudio"><span class="edge-icon">◈</span><span>Koçluk Stüdyosu</span></button><button type="button" id="edgeHomeCreateInstitution"><span class="edge-icon">＋</span><span>Kurum Açma</span></button>'
    core_button = '<button type="button" id="edgeHomeQuestionStudio"><span class="edge-icon">▤</span><span>Soru Stüdyosu</span></button>'
    if legacy_buttons in text:
        text = text.replace(legacy_buttons, core_button, 1)
    elif core_button not in text:
        raise RuntimeError("GENESIS home edge button block changed")

    legacy_handlers = 'document.getElementById("edgeHomeQuestionStudio").onclick=()=>location.assign("/?workspace=1");\ndocument.getElementById("edgeHomeCoachingStudio").onclick=()=>location.assign("/coaching");\ndocument.getElementById("edgeHomeCreateInstitution").onclick=()=>{if(typeof window.genesisCreateInstitution==="function"){window.genesisCreateInstitution();return}if(typeof window.notice==="function")window.notice("Kurum Açma ekranı şu anda kullanılamıyor.");};'
    q_handler = 'document.getElementById("edgeHomeQuestionStudio").onclick=()=>location.assign("/?workspace=1");'
    v2_handlers = q_handler + '\nconst close=document.getElementById("closeBtn");if(close)close.onclick=()=>{if(typeof window.notice==="function")window.notice("Bu bir web uygulamasıdır. Sekmeyi tarayıcıdan kapatabilirsiniz.");};'
    v3_handlers = q_handler + '\nconst close=document.getElementById("closeBtn");if(close)close.remove();'
    if legacy_handlers in text:
        text = text.replace(legacy_handlers, v3_handlers, 1)
    elif v2_handlers in text:
        text = text.replace(v2_handlers, v3_handlers, 1)
    elif v3_handlers not in text:
        if q_handler not in text:
            raise RuntimeError("GENESIS home edge handler block changed")
        text = text.replace(q_handler, v3_handlers, 1)

    # Defense in depth: even if native code re-renders the titlebar, the close
    # control remains invisible and cannot receive pointer events.
    style_anchor = '</style>'
    if '#closeBtn{display:none!important;pointer-events:none!important}' not in text:
        if style_anchor not in text:
            raise RuntimeError("GENESIS edge style block missing")
        text = text.replace(style_anchor, '#closeBtn{display:none!important;pointer-events:none!important}\n</style>', 1)

    inserted = False
    for old in OLD_MARKERS:
        marker = f"/* {old} */"
        if marker in text:
            text = text.replace(marker, marker + f"\n/* {MARKER} */", 1)
            inserted = True
            break
    if not inserted:
        anchor = '/* GENESIS_HOME_DASHBOARD_EDGE_V1 */\n(()=>{'
        if anchor not in text:
            raise RuntimeError("GENESIS edge script anchor missing")
        text = text.replace(anchor, f'/* GENESIS_HOME_DASHBOARD_EDGE_V1 */\n/* {MARKER} */\n(()=>{{', 1)

    assert "edgeHomeQuestionStudio" in text
    assert "edgeHomeCoachingStudio" not in text
    assert "edgeHomeCreateInstitution" not in text
    assert 'api("/api/system/shutdown"' not in text
    assert 'close.remove()' in text
    assert '#closeBtn{display:none!important;pointer-events:none!important}' in text
    assert MARKER in text
    return text.encode("utf-8")
