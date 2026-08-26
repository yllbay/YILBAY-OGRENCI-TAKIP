from pathlib import Path
import re
root=Path('/tmp/yilbay066/src')
server=root/'app/server.js'
s=server.read_text(encoding='utf-8')

start=s.find('function readWindowsCredential(')
end=s.find('\nfunction readSecrets()', start)
if start<0 or end<0: raise SystemExit('readWindowsCredential block not found')
new=r'''function readWindowsCredential(target=OPENAI_CREDENTIAL_TARGET){
  if(process.platform!=="win32") return null;
  const now=Date.now();
  if(now-credentialCache.at<30000) return credentialCache.value;
  const helper=path.join(__dirname,"credential_reader.exe");
  try{
    const out=cp.execFileSync(helper,[target,OPENAI_CREDENTIAL_USERNAME],{encoding:"buffer",windowsHide:true,timeout:5000,stdio:["ignore","pipe","ignore"]});
    const secret=Buffer.isBuffer(out)?out.toString("utf16le").replace(/\u0000+$/g,"").trim():"";
    const value=secret?{username:OPENAI_CREDENTIAL_USERNAME,secret,diagnostic:{method:"native-helper",found:true,userMatch:true,targetMatched:true,blobPresent:true,nativeOk:true}}:null;
    credentialCache={at:now,value};
    return value;
  }catch(e){
    credentialCache={at:now,value:null};
    return null;
  }
}
'''
s=s[:start]+new+s[end:]
s=re.sub(r'version:"0\.6\.[0-9]+"','version:"0.6.6"',s,count=1)
s=s.replace('READY 0.6.5','READY 0.6.6').replace('READY 0.6.4','READY 0.6.6').replace('READY 0.6.3','READY 0.6.6')
server.write_text(s,encoding='utf-8')

app=root/'app/public/app.js'
a=app.read_text(encoding='utf-8')
a=re.sub(r'const STORAGE="yilbay_mvp_\d+";','const STORAGE="yilbay_mvp_066";',a,count=1)
anchor=' const current=localStorage.getItem(STORAGE);\n if(current) return normalizeDb(JSON.parse(current));\n'
if anchor in a:
    migration=''' const current=localStorage.getItem(STORAGE);\n if(current) return normalizeDb(JSON.parse(current));\n for(const k of ["yilbay_mvp_065","yilbay_mvp_064","yilbay_mvp_063","yilbay_mvp_062","yilbay_mvp_061"]){const v=localStorage.getItem(k);if(v){const migrated=normalizeDb(JSON.parse(v));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}}\n'''
    a=a.replace(anchor,migration,1)
app.write_text(a,encoding='utf-8')
(root/'VERSION').write_text('0.6.6\n',encoding='utf-8')
(root/'README.md').write_text('''# YILBAY Öğrenci Takip — v0.6.6\n\n- Credential Manager erişiminde PowerShell tamamen kaldırıldı.\n- OpenAI anahtarı, bundled native `credential_reader.exe` ile Windows Credential Manager API üzerinden okunur.\n- Hedef: `YILBAY-OPENAI-API-HOME`; kullanıcı adı: `YILBAY-DEVELOPMENT-HOME`.\n- Anahtar diske, loga veya rapor ZIP dosyasına yazılmaz.\n- Avast PSE90 tetikleyen PowerShell credential yolu artık kullanılmaz.\n- v0.6.3/v0.6.4/v0.6.5 verileri v0.6.6 depolamasına taşınır.\n''',encoding='utf-8')
