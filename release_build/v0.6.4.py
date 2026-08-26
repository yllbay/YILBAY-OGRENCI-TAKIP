from pathlib import Path

root=Path('/tmp/yilbay064/src')
server=root/'app/server.js'
s=server.read_text(encoding='utf-8')
start=s.index('function readWindowsCredential(')
end=s.index('function readSecrets(){', start)
new=r'''function readWindowsCredential(target=OPENAI_CREDENTIAL_TARGET){
  if(process.platform!=="win32") return {value:null,diagnostic:{method:"not-windows",found:false,userMatch:false,targetMatched:false,cmdkeySeen:false}};
  const now=Date.now();
  if(now-credentialCache.at<30000) return credentialCache.value;
  let cmdkeySeen=false;
  try{
    const listing=cp.execFileSync("cmdkey.exe",["/list"],{encoding:"utf8",windowsHide:true,timeout:4000,stdio:["ignore","pipe","ignore"]});
    cmdkeySeen=String(listing||"").toLowerCase().includes(String(target).toLowerCase());
  }catch{}
  const ps=`$ErrorActionPreference='Stop'
$src=@'
using System;
using System.Runtime.InteropServices;
public static class YilbayCredNative64 {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct CREDENTIAL {
    public UInt32 Flags; public UInt32 Type; public IntPtr TargetName; public IntPtr Comment;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
    public UInt32 CredentialBlobSize; public IntPtr CredentialBlob; public UInt32 Persist;
    public UInt32 AttributeCount; public IntPtr Attributes; public IntPtr TargetAlias; public IntPtr UserName;
  }
  [DllImport("advapi32.dll", EntryPoint="CredEnumerateW", CharSet=CharSet.Unicode, SetLastError=true)]
  [return: MarshalAs(UnmanagedType.Bool)]
  public static extern bool CredEnumerate(string Filter, UInt32 Flags, out UInt32 Count, out IntPtr Credentials);
  [DllImport("advapi32.dll", SetLastError=true)] public static extern void CredFree(IntPtr Buffer);
}
'@
Add-Type -TypeDefinition $src
$count=[uint32]0;$arr=[IntPtr]::Zero
$ok=[YilbayCredNative64]::CredEnumerate($null,0,[ref]$count,[ref]$arr)
if(-not $ok){[pscustomobject]@{ok=$false;win32=[Runtime.InteropServices.Marshal]::GetLastWin32Error();matched=$false}|ConvertTo-Json -Compress;exit 0}
try{
  $wanted='${target.replace(/'/g,"''")}'
  for($i=0;$i -lt [int]$count;$i++){
    $cp=[Runtime.InteropServices.Marshal]::ReadIntPtr($arr,$i*[IntPtr]::Size)
    if($cp -eq [IntPtr]::Zero){continue}
    $c=[Runtime.InteropServices.Marshal]::PtrToStructure($cp,[type][YilbayCredNative64+CREDENTIAL])
    $t=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.TargetName)
    if([string]::IsNullOrEmpty($t)){continue}
    $match=($t -eq $wanted) -or $t.EndsWith($wanted,[StringComparison]::OrdinalIgnoreCase)
    if(-not $match){continue}
    $u=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.UserName)
    $bytes=New-Object byte[] ([int]$c.CredentialBlobSize)
    if($c.CredentialBlobSize -gt 0 -and $c.CredentialBlob -ne [IntPtr]::Zero){[Runtime.InteropServices.Marshal]::Copy($c.CredentialBlob,$bytes,0,[int]$c.CredentialBlobSize)}
    $unicode=[Text.Encoding]::Unicode.GetString($bytes).Trim([char]0)
    $utf8=[Text.Encoding]::UTF8.GetString($bytes).Trim([char]0)
    $secret=$unicode
    if([string]::IsNullOrWhiteSpace($secret) -or $secret.Contains([char]0)){$secret=$utf8}
    [pscustomobject]@{ok=$true;matched=$true;target=$t;username=$u;secret=$secret;type=[int]$c.Type;persist=[int]$c.Persist;blobSize=[int]$c.CredentialBlobSize}|ConvertTo-Json -Compress
    exit 0
  }
  [pscustomobject]@{ok=$true;matched=$false;count=[int]$count}|ConvertTo-Json -Compress
}finally{if($arr -ne [IntPtr]::Zero){[YilbayCredNative64]::CredFree($arr)}}`;
  try{
    const encoded=Buffer.from(ps,"utf16le").toString("base64");
    const out=cp.execFileSync("powershell.exe",["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-EncodedCommand",encoded],{encoding:"utf8",windowsHide:true,timeout:8000,stdio:["ignore","pipe","pipe"]}).trim();
    const parsed=JSON.parse(out||"null");
    const user=String(parsed?.username||""); const secret=String(parsed?.secret||"");
    const matched=!!parsed?.matched; const userMatch=!OPENAI_CREDENTIAL_USERNAME||user===OPENAI_CREDENTIAL_USERNAME;
    const result={value:(matched&&secret&&userMatch)?{username:user,secret}:null,diagnostic:{method:"enumerate-native",found:matched&&!!secret,userMatch:matched?userMatch:false,targetMatched:matched,cmdkeySeen,credentialType:Number(parsed?.type||0),persist:Number(parsed?.persist||0),blobPresent:Number(parsed?.blobSize||0)>0,nativeOk:parsed?.ok===true,win32Error:Number(parsed?.win32||0)}};
    credentialCache={at:now,value:result}; return result;
  }catch{
    const result={value:null,diagnostic:{method:"enumerate-native-error",found:false,userMatch:false,targetMatched:false,cmdkeySeen,nativeOk:false}};
    credentialCache={at:now,value:result}; return result;
  }
}
'''
s=s[:start]+new+s[end:]
s=s.replace('version:"0.6.3"','version:"0.6.4"',1).replace('READY 0.6.3','READY 0.6.4',1)
server.write_text(s,encoding='utf-8')

app=root/'app/public/app.js'
a=app.read_text(encoding='utf-8')
a=a.replace('const STORAGE="yilbay_mvp_063";','const STORAGE="yilbay_mvp_064";\nconst PREV_STORAGE_063="yilbay_mvp_063";',1)
anchor=' const current=localStorage.getItem(STORAGE);\n if(current) return normalizeDb(JSON.parse(current));\n'
if anchor in a:
    a=a.replace(anchor,anchor+' const p63=localStorage.getItem(PREV_STORAGE_063);\n if(p63){const migrated=normalizeDb(JSON.parse(p63));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}\n',1)
app.write_text(a,encoding='utf-8')
(root/'VERSION').write_text('0.6.4\n',encoding='utf-8')
(root/'README.md').write_text('# YILBAY Öğrenci Takip — v0.6.4\n\nCredential Manager tüm credential türleriyle enumerate edilir; hedef son ek eşleşmesi desteklenir. cmdkey yalnızca güvenli varlık teşhisi için kullanılır. API anahtarı log/rapora yazılmaz.\n',encoding='utf-8')
