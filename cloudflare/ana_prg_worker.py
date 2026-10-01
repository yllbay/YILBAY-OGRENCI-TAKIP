"""Small, idempotent native-navigation patch to the preserved live Worker."""
def patch(module:bytes)->bytes:
    src=module.decode('utf-8')
    if 'ANA_PRG_NATIVE_EDGE_V1' in src:return module
    anchor='  envVars = {\n'
    assert src.count(anchor)==1,'Container environment anchor changed'
    src=src.replace(anchor,anchor+'''    // ANA_PRG_NATIVE_EDGE_V1
    ANA_WHATSAPP_ACCESS_TOKEN: this.env.ANA_WHATSAPP_ACCESS_TOKEN,
    ANA_WHATSAPP_PHONE_NUMBER_ID: this.env.ANA_WHATSAPP_PHONE_NUMBER_ID,
    ANA_WHATSAPP_API_VERSION: this.env.ANA_WHATSAPP_API_VERSION || "v23.0",
''',1)
    src=src.replace('Koçluk Stüdyosu','ANA PRG · Eğitim Yönetimi')
    anchor='document.getElementById("edgeHomeCoachingStudio").onclick=()=>location.assign("/coaching");'
    assert src.count(anchor)==1,'Home navigation anchor changed'
    src=src.replace(anchor,'document.getElementById("edgeHomeCoachingStudio").onclick=()=>location.assign("/ana-prg");',1)
    # Old coaching overlay cannot intercept native ANA pages. Its dormant source
    # remains in the exact rollback snapshot, not the active application UI.
    return src.encode('utf-8')
