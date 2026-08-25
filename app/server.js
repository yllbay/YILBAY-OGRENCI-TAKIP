const http=require("http"),fs=require("fs"),path=require("path"),cp=require("child_process");
const port=Number(process.env.PORT||43127), pub=path.join(__dirname,"public");
const root=path.resolve(__dirname,"..");

function scheduleBootstrapMigration(){
  try{
    const runtime=path.join(root,"runtime");
    fs.mkdirSync(runtime,{recursive:true});
    const ps1=path.join(runtime,"bootstrap_migrate_041.ps1");
    const batPath=path.join(root,"PROGRAMI_CALISTIR.bat");
    const bat=`@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title YILBAY OGRENCI TAKIP SISTEMI

echo ================================================================
echo       YILBAY OGRENCI TAKIP SISTEMI - KALICI BASLATICI
echo ================================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap\\orchestrator.ps1"
set EXITCODE=%ERRORLEVEL%
exit /b %EXITCODE%
`;
    const esc=s=>s.replace(/'/g,"''");
    const script=`$ErrorActionPreference='SilentlyContinue'
$Root='${esc(root)}'
$Bat='${esc(batPath)}'
$Content=@'
${bat.replace(/\r/g,"")}
'@

for($i=0;$i -lt 900;$i++){
  $running=Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'powershell.exe' -and
    $_.CommandLine -like '*bootstrap\\orchestrator.ps1*' -and
    $_.CommandLine -like ('*'+$Root+'*')
  }
  if(-not $running){break}
  Start-Sleep -Milliseconds 500
}

[System.IO.File]::WriteAllText($Bat,$Content,(New-Object System.Text.UTF8Encoding($false)))

Start-Sleep -Milliseconds 300
Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'cmd.exe' -and
  $_.CommandLine -like '*PROGRAMI_CALISTIR.bat*' -and
  $_.CommandLine -like ('*'+$Root+'*')
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
`;
    fs.writeFileSync(ps1,script,"utf8");
    const child=cp.spawn("powershell.exe",["-NoProfile","-ExecutionPolicy","Bypass","-WindowStyle","Hidden","-File",ps1],{
      detached:true,stdio:"ignore",windowsHide:true
    });
    child.unref();
    console.log("BOOTSTRAP_MIGRATION_SCHEDULED");
  }catch(e){
    console.error("BOOTSTRAP_MIGRATION_ERROR",e.message);
  }
}
scheduleBootstrapMigration();

http.createServer((req,res)=>{
  const u=new URL(req.url,"http://127.0.0.1");
  if(u.pathname==="/health"){
    res.writeHead(200,{"Content-Type":"application/json; charset=utf-8"});
    return res.end(JSON.stringify({ok:true,version:"0.4.1",bootstrapMigration:"scheduled"}));
  }
  let p=u.pathname==="/"?"/index.html":u.pathname;
  const f=path.normalize(path.join(pub,p));
  if(!f.startsWith(pub)){res.writeHead(403);return res.end("Forbidden")}
  fs.readFile(f,(e,d)=>{
    if(e){res.writeHead(404);return res.end("Not found")}
    const ext=path.extname(f).toLowerCase();
    const types={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".json":"application/json; charset=utf-8"};
    res.writeHead(200,{"Content-Type":types[ext]||"application/octet-stream"});res.end(d);
  });
}).listen(port,"127.0.0.1",()=>console.log("READY 0.4.1"));
