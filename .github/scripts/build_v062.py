from pathlib import Path
import sys

root=Path('/tmp/yilbay062/src')
server=root/'app/server.js'
s=server.read_text(encoding='utf-8')
old='function readSecrets(){\n  try{return JSON.parse(fs.readFileSync(secretFile,"utf8"))}catch{return {}}\n}\n'
new=r'''const OPENAI_CREDENTIAL_TARGET="YILBAY-OPENAI-API-HOME";
const OPENAI_CREDENTIAL_USERNAME="YILBAY-DEVELOPMENT-HOME";
let credentialCache={at:0,value:null};
function readStoredSecrets(){
  try{return JSON.parse(fs.readFileSync(secretFile,"utf8"))}catch{return {}}
}
function readWindowsCredential(target=OPENAI_CREDENTIAL_TARGET){
  if(process.platform!=="win32") return null;
  const now=Date.now();
  if(now-credentialCache.at<30000) return credentialCache.value;
  const ps=`$ErrorActionPreference='Stop'
$src=@'
using System;
using System.Runtime.InteropServices;
public static class YilbayCredNative {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct CREDENTIAL {
    public UInt32 Flags; public UInt32 Type; public IntPtr TargetName; public IntPtr Comment;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
    public UInt32 CredentialBlobSize; public IntPtr CredentialBlob; public UInt32 Persist;
    public UInt32 AttributeCount; public IntPtr Attributes; public IntPtr TargetAlias; public IntPtr UserName;
  }
  [DllImport("advapi32.dll", EntryPoint="CredReadW", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool CredRead(string target, UInt32 type, UInt32 reservedFlag, out IntPtr credentialPtr);
  [DllImport("advapi32.dll", SetLastError=true)]
  public static extern void CredFree(IntPtr credentialPtr);
}
'@
Add-Type -TypeDefinition $src -ErrorAction SilentlyContinue
$p=[IntPtr]::Zero
if(-not [YilbayCredNative]::CredRead('${target.replace(/'/g,"''")}',1,0,[ref]$p)){ exit 3 }
try {
  $c=[Runtime.InteropServices.Marshal]::PtrToStructure($p,[type][YilbayCredNative+CREDENTIAL])
  $user=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.UserName)
  $bytes=New-Object byte[] $c.CredentialBlobSize
  if($c.CredentialBlobSize -gt 0){ [Runtime.InteropServices.Marshal]::Copy($c.CredentialBlob,$bytes,0,$c.CredentialBlobSize) }
  $secret=[Text.Encoding]::Unicode.GetString($bytes).Trim([char]0)
  [pscustomobject]@{username=$user;secret=$secret} | ConvertTo-Json -Compress
} finally { [YilbayCredNative]::CredFree($p) }`;
  try{
    const encoded=Buffer.from(ps,"utf16le").toString("base64");
    const out=cp.execFileSync("powershell.exe",["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-EncodedCommand",encoded],{encoding:"utf8",windowsHide:true,timeout:5000,stdio:["ignore","pipe","ignore"]}).trim();
    const parsed=JSON.parse(out||"null");
    const value=parsed&&parsed.secret?{username:String(parsed.username||""),secret:String(parsed.secret||"")} : null;
    credentialCache={at:now,value};
    return value;
  }catch{
    credentialCache={at:now,value:null};
    return null;
  }
}
function readSecrets(){
  const stored=readStoredSecrets();
  const cred=readWindowsCredential();
  const envKey=String(process.env.OPENAI_API_KEY||"").trim();
  const manual=String(stored.openaiApiKey||"").trim();
  let openaiApiKey="",openaiApiSource="none";
  if(cred?.secret && (!OPENAI_CREDENTIAL_USERNAME || cred.username===OPENAI_CREDENTIAL_USERNAME)){
    openaiApiKey=cred.secret; openaiApiSource="windows-credential-manager";
  }else if(envKey){ openaiApiKey=envKey; openaiApiSource="environment"; }
  else if(manual){ openaiApiKey=manual; openaiApiSource="manual"; }
  return {...stored,openaiApiKey,openaiApiSource,credentialTarget:OPENAI_CREDENTIAL_TARGET};
}
'''
if old not in s: sys.exit('readSecrets anchor missing')
s=s.replace(old,new,1)
s=s.replace('openai:{configured:!!s.openaiApiKey,model:s.openaiModel||"gpt-5.6-luna"}', 'openai:{configured:!!s.openaiApiKey,model:s.openaiModel||"gpt-5.6-luna",source:s.openaiApiSource||"none",credentialTarget:OPENAI_CREDENTIAL_TARGET}',1)
s=s.replace('version:"0.6.1"','version:"0.6.2"',1)
s=s.replace('b=await readJson(req,128*1024),old=readSecrets()','b=await readJson(req,128*1024),old=readStoredSecrets()',1)
s=s.replace('READY 0.6.1','READY 0.6.2',1)
server.write_text(s,encoding='utf-8')

app=root/'app/public/app.js'
a=app.read_text(encoding='utf-8')
a=a.replace('const STORAGE="yilbay_mvp_061";', 'const STORAGE="yilbay_mvp_062";\nconst PREV_STORAGE_061="yilbay_mvp_061";',1)
anchor=' const current=localStorage.getItem(STORAGE);\n if(current) return normalizeDb(JSON.parse(current));\n'
if anchor not in a: sys.exit('storage migration anchor missing')
a=a.replace(anchor,anchor+' const p61=localStorage.getItem(PREV_STORAGE_061);\n if(p61){const migrated=normalizeDb(JSON.parse(p61));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}\n',1)
oldcard='<div class="card integration-card"><div class="integration-head"><div><div class="cell-title">OpenAI</div><div class="cell-sub">Planlama + ödev vision analizi</div></div><span class="badge ${s.openai.configured?"good":"mid"}">${s.openai.configured?"Bağlı":"Anahtar gerekli"}</span></div><div class="integration-meta">Model: <b>${s.openai.model}</b></div></div>'
newcard='<div class="card integration-card"><div class="integration-head"><div><div class="cell-title">OpenAI</div><div class="cell-sub">Planlama + ödev vision analizi</div></div><span class="badge ${s.openai.configured?"good":"mid"}">${s.openai.configured?"Bağlı":"Anahtar gerekli"}</span></div><div class="integration-meta">Model: <b>${s.openai.model}</b><br>Kaynak: <b>${s.openai.source==="windows-credential-manager"?"Windows Kimlik Bilgileri Yöneticisi":s.openai.source==="environment"?"Ortam değişkeni":s.openai.source==="manual"?"Manuel ayar":"Yok"}</b>${s.openai.source==="windows-credential-manager"?` · ${s.openai.credentialTarget}`:""}</div></div>'
if oldcard not in a: sys.exit('integration card anchor missing')
a=a.replace(oldcard,newcard,1)
app.write_text(a,encoding='utf-8')
(root/'VERSION').write_text('0.6.2\n',encoding='utf-8')
(root/'README.md').write_text('# YILBAY Öğrenci Takip — v0.6.2\n\n- OpenAI anahtarı Windows Credential Manager kaydından otomatik okunur.\n- Hedef: `YILBAY-OPENAI-API-HOME`\n- Kullanıcı: `YILBAY-DEVELOPMENT-HOME`\n- Parola/API anahtarı yalnız bellekte kullanılır; log, rapor veya api_secrets.json içine kopyalanmaz.\n- Öncelik: Windows Credential Manager → OPENAI_API_KEY → manuel ayar.\n',encoding='utf-8')
print('PATCH_OK')
