from pathlib import Path
root=Path('/tmp/yilbay063/src')
p=root/'app/server.js'
s=p.read_text(encoding='utf-8')
start=s.index('function readWindowsCredential(')
end=s.index('function readSecrets(){',start)
new=r'''function readWindowsCredential(target=OPENAI_CREDENTIAL_TARGET){
  if(process.platform!=="win32") return {value:null,diagnostic:{method:"not-windows",found:false,userMatch:false}};
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
  [DllImport("advapi32.dll", EntryPoint="CredEnumerateW", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool CredEnumerate(string filter, UInt32 flags, out UInt32 count, out IntPtr credentials);
  [DllImport("advapi32.dll", SetLastError=true)] public static extern void CredFree(IntPtr credentialPtr);
}
'@
Add-Type -TypeDefinition $src -ErrorAction SilentlyContinue
function Convert-Cred([IntPtr]$p,[string]$method){
  $c=[Runtime.InteropServices.Marshal]::PtrToStructure($p,[type][YilbayCredNative+CREDENTIAL])
  $t=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.TargetName)
  $u=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.UserName)
  $bytes=New-Object byte[] $c.CredentialBlobSize
  if($c.CredentialBlobSize -gt 0){[Runtime.InteropServices.Marshal]::Copy($c.CredentialBlob,$bytes,0,$c.CredentialBlobSize)}
  $secret=[Text.Encoding]::Unicode.GetString($bytes).Trim([char]0)
  if([string]::IsNullOrWhiteSpace($secret) -or $secret.Contains([char]0)){$secret=[Text.Encoding]::UTF8.GetString($bytes).Trim([char]0)}
  [pscustomobject]@{target=$t;username=$u;secret=$secret;method=$method}
}
$p=[IntPtr]::Zero
if([YilbayCredNative]::CredRead('${target.replace(/'/g,"''")}',1,0,[ref]$p)){
  try{Convert-Cred $p 'direct'}finally{[YilbayCredNative]::CredFree($p)}
  exit 0
}
$count=0;$arr=[IntPtr]::Zero
if([YilbayCredNative]::CredEnumerate($null,0,[ref]$count,[ref]$arr)){
  try{
    for($i=0;$i -lt $count;$i++){
      $cp=[Runtime.InteropServices.Marshal]::ReadIntPtr($arr,$i*[IntPtr]::Size)
      $c=[Runtime.InteropServices.Marshal]::PtrToStructure($cp,[type][YilbayCredNative+CREDENTIAL])
      $t=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.TargetName)
      if($t -eq '${target.replace(/'/g,"''")}' -or $t.EndsWith('${target.replace(/'/g,"''")}')){Convert-Cred $cp 'enumerate'; exit 0}
    }
  }finally{[YilbayCredNative]::CredFree($arr)}
}
exit 3`;
  try{
    const encoded=Buffer.from(ps,"utf16le").toString("base64");
    const out=cp.execFileSync("powershell.exe",["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-EncodedCommand",encoded],{encoding:"utf8",windowsHide:true,timeout:7000,stdio:["ignore","pipe","ignore"]}).trim();
    const parsed=JSON.parse(out||"null");
    const user=String(parsed?.username||""); const secret=String(parsed?.secret||"");
    const userMatch=!OPENAI_CREDENTIAL_USERNAME||user===OPENAI_CREDENTIAL_USERNAME;
    const result={value:(secret&&userMatch)?{username:user,secret}:null,diagnostic:{method:String(parsed?.method||"unknown"),found:!!secret,userMatch,targetMatched:String(parsed?.target||"").endsWith(target)}};
    credentialCache={at:now,value:result}; return result;
  }catch{
    const result={value:null,diagnostic:{method:"not-found",found:false,userMatch:false,targetMatched:false}};
    credentialCache={at:now,value:result}; return result;
  }
}
'''
s=s[:start]+new+s[end:]
s=s.replace('const cred=readWindowsCredential();','const credResult=readWindowsCredential();\n  const cred=credResult.value;',1)
s=s.replace('return {...stored,openaiApiKey,openaiApiSource,credentialTarget:OPENAI_CREDENTIAL_TARGET};','return {...stored,openaiApiKey,openaiApiSource,credentialTarget:OPENAI_CREDENTIAL_TARGET,credentialDiagnostic:credResult.diagnostic};',1)
s=s.replace('credentialTarget:OPENAI_CREDENTIAL_TARGET}', 'credentialTarget:OPENAI_CREDENTIAL_TARGET,credentialDiagnostic:s.credentialDiagnostic||null}',1)
s=s.replace('version:"0.6.2"','version:"0.6.3"',1).replace('READY 0.6.2','READY 0.6.3')
p.write_text(s,encoding='utf-8')
ap=root/'app/public/app.js'
a=ap.read_text(encoding='utf-8')
a=a.replace('const STORAGE="yilbay_mvp_062";','const STORAGE="yilbay_mvp_063";\nconst PREV_STORAGE_062="yilbay_mvp_062";',1)
anchor=' const current=localStorage.getItem(STORAGE);\n if(current) return normalizeDb(JSON.parse(current));\n'
if 'PREV_STORAGE_062' not in a[a.index('function load()'):]:
    a=a.replace(anchor,anchor+' const p62=localStorage.getItem(PREV_STORAGE_062);\n if(p62){const migrated=normalizeDb(JSON.parse(p62));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}\n',1)
ap.write_text(a,encoding='utf-8')
(root/'VERSION').write_text('0.6.3\n',encoding='utf-8')
