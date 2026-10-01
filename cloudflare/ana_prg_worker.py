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
    anchor='      const forwarded = new Request(request);\n'
    assert src.count(anchor)==1,'Worker forwarding anchor changed'
    src=src.replace(anchor,anchor+'''      // ANA_PRG_AUTHORIZED_RESTART_V1: no restart on an unauthenticated request.
      if (request.method === "POST" && new URL(request.url).pathname === "/api/ana-prg/system/restart") {
        const response = await container.fetch(forwarded);
        if (response.status !== 200) return response;
        const permit = await response.clone().json();
        if (permit.restart_allowed !== true) return response;
        await container.destroy();
        return Response.json({...permit,restarted:true},{headers:{"Cache-Control":"no-store"}});
      }
''',1)
    # Old coaching overlay cannot intercept native ANA pages. Its dormant source
    # remains in the exact rollback snapshot, not the active application UI.
    return src.encode('utf-8')
