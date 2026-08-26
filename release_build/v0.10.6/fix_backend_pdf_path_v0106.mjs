import fs from 'fs';
const p='/tmp/yilbay0106/app/server.js';
let s=fs.readFileSync(p,'utf8');
const bad="html.replace(/\\/g,'/')";
const good="html.split(path.sep).join('/')";
if(!s.includes(bad))throw new Error('malformed PDF path conversion not found');
s=s.replace(bad,good);
fs.writeFileSync(p,s,'utf8');
console.log('v0.10.6 PDF path conversion fixed without regex');