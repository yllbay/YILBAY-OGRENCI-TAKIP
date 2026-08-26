from pathlib import Path
root=Path('/tmp/yilbay068/src')
boot=root/'app/bootstrap/orchestrator_node.js'
server=root/'app/server.js'
appjs=root/'app/public/app.js'
version=root/'VERSION'

s=boot.read_text(encoding='utf-8-sig')
anchor='function sha256(p){return crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex")}\n'
parse='function parseJson(s){return JSON.parse(String(s).replace(/^\\uFEFF/,""))}\n'
if 'function parseJson(' not in s:
    if anchor not in s: raise SystemExit('sha256 anchor missing')
    s=s.replace(anchor,anchor+parse)
s=s.replace('return JSON.parse(b.toString("utf8"))','return parseJson(b.toString("utf8"))')
s=s.replace('const j=JSON.parse(fs.readFileSync(p,"utf8"));','const j=parseJson(fs.readFileSync(p,"utf8"));')
s=s.replace('const cfg=JSON.parse(fs.readFileSync(p,"utf8")),local=cfg.current_app_version||"0.0.0";','const cfg=parseJson(fs.readFileSync(p,"utf8")),local=cfg.current_app_version||"0.0.0";')
s=s.replace('man=JSON.parse((await fetchBuffer(cfg.manifest_url,15000)).toString("utf8"))','man=parseJson((await fetchBuffer(cfg.manifest_url,15000)).toString("utf8"))')
boot.write_text(s,encoding='utf-8')

ss=server.read_text(encoding='utf-8-sig').replace('0.6.7','0.6.8')
server.write_text(ss,encoding='utf-8')
if appjs.exists():
    a=appjs.read_text(encoding='utf-8-sig').replace('0.6.7','0.6.8')
    appjs.write_text(a,encoding='utf-8')
version.write_text('0.6.8\n',encoding='utf-8')
print('patched v0.6.8 BOM-safe bootstrap')
