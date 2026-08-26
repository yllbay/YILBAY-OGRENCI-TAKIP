from pathlib import Path
import os, shutil
root=Path('/tmp/yilbay067/src')
server=root/'app/server.js'
appjs=root/'app/public/app.js'
version=root/'VERSION'
text=server.read_text(encoding='utf-8')
text=text.replace('0.6.5','0.6.7')
migration=r'''
(function installNodeBootstrap(){
  if(process.platform!=="win32") return;
  try{
    const _fs=require("fs"),_path=require("path");
    const _root=_path.resolve(__dirname,"..");
    const _src=_path.join(__dirname,"bootstrap","orchestrator_node.js");
    const _dst=_path.join(_root,"bootstrap","orchestrator.js");
    if(_fs.existsSync(_src)){
      _fs.mkdirSync(_path.dirname(_dst),{recursive:true});
      _fs.copyFileSync(_src,_dst);
      const bat='@echo off\r\nsetlocal\r\nwhere node >nul 2>nul\r\nif %ERRORLEVEL%==0 (\r\n  node "%~dp0bootstrap\\orchestrator.js"\r\n  exit /b %ERRORLEVEL%\r\n)\r\necho Node.js bulunamadi. Eski baslatma yontemine geciliyor.\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap\\orchestrator.ps1"\r\nexit /b %ERRORLEVEL%\r\n';
      _fs.writeFileSync(_path.join(_root,"PROGRAMI_CALISTIR.bat"),bat,"utf8");
      _fs.writeFileSync(_path.join(_root,"BOOTSTRAP_VERSION"),'2.0.0-node\n','utf8');
      console.log('NODE_BOOTSTRAP_MIGRATION_READY');
    }
  }catch(e){ console.error('NODE_BOOTSTRAP_MIGRATION_ERROR',e.message); }
})();
'''
text += '\n'+migration
server.write_text(text,encoding='utf-8')
if appjs.exists():
    s=appjs.read_text(encoding='utf-8').replace('0.6.5','0.6.7')
    appjs.write_text(s,encoding='utf-8')
version.write_text('0.6.7\n',encoding='utf-8')
(root/'app/bootstrap').mkdir(parents=True,exist_ok=True)
workspace=Path(os.environ['GITHUB_WORKSPACE'])
shutil.copy2(workspace/'release_build/v0.6.7/orchestrator_node.js',root/'app/bootstrap/orchestrator_node.js')
print('patched v0.6.7')
