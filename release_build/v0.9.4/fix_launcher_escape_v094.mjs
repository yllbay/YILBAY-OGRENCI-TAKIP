import fs from 'fs';
const p='/tmp/yilbay094/app/server.js';
let s=fs.readFileSync(p,'utf8');
s=s.replaceAll('%~dp0bootstrap\\orchestrator_node.js','%~dp0bootstrap/orchestrator_node.js');
s=s.replaceAll('%~dp0bootstrap\orchestrator_node.js','%~dp0bootstrap/orchestrator_node.js');
if(!s.includes('%~dp0bootstrap/orchestrator_node.js'))throw new Error('launcher path escape fix failed');
fs.writeFileSync(p,s,'utf8');
console.log('launcher escape fixed');
