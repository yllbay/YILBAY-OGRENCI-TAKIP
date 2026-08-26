from pathlib import Path
import re
p=Path('/tmp/yilbay070/app/server.js')
s=p.read_text(encoding='utf-8')
# Remove obsolete v0.4.x PowerShell bootstrap migration.
s,n1=re.subn(r'function scheduleBootstrapMigration\(\)\{.*?\}\s*scheduleBootstrapMigration\(\);','',s,flags=re.S)
# Remove obsolete v0.6.7 self-migration block; package bootstrap is already Node-based.
s,n2=re.subn(r'\(function installNodeBootstrap\(\)\{.*?\}\)\(\);','',s,flags=re.S)
if 'powershell.exe' in s.lower():
    raise SystemExit(f'powershell.exe remains; removed schedule={n1} install={n2}')
p.write_text(s,encoding='utf-8')
print(f'cleaned stale PowerShell blocks schedule={n1} install={n2}')
