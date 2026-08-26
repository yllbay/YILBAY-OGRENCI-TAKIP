from pathlib import Path
p=Path('/tmp/yilbay070/app/server.js')
s=p.read_text(encoding='utf-8')
if 'function readStoredSecrets()' not in s:
    anchor='function readWindowsCredential(){'
    if anchor not in s: raise SystemExit('readWindowsCredential anchor missing')
    func='''function readStoredSecrets(){\n  try{return JSON.parse(fs.readFileSync(secretFile,"utf8"))}catch{return {}}\n}\n'''
    s=s.replace(anchor,func+anchor,1)
p.write_text(s,encoding='utf-8')
print('readStoredSecrets restored')
