import fs from 'fs';
import path from 'path';
const ROOT='/tmp/yilbay092';
const manifestPath=path.join(ROOT,'cells','micro-cell-manifest.json');
const m=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(m.version!=='0.9.1'||m.protocol!=='micro-cell-v2-ast') throw new Error('Expected verified v0.9.1 micro-cell source');
const all=[...m.frontend,...m.backend];
for(const e of all){const p=path.join(ROOT,e.file);let s=fs.readFileSync(p,'utf8');s=s.replaceAll('0.9.1','0.9.2');fs.writeFileSync(p,s,'utf8')}
const indexEntry=m.frontend.find(x=>x.name==='indexGoogleDrive');
if(!indexEntry) throw new Error('indexGoogleDrive cell missing');
const indexPath=path.join(ROOT,indexEntry.file);
let index=fs.readFileSync(indexPath,'utf8');
const old='const existing=db.resources.find(r=>r.driveFileId===x.id);const next={type:"PDF",course:x.course,topic:x.topic,level:x.level,title:x.title||x.name,url:x.webViewLink||"",driveFileId:x.id,driveModifiedTime:x.modifiedTime||null,driveSource:true};if(existing){Object.assign(existing,next);updated++}else{db.resources.push({id:Date.now()+added,...next});added++}';
const repl='const result=upsertDriveResource(x,Date.now()+added);if(result==="added")added++;else if(result==="updated")updated++';
if(!index.includes(old)) throw new Error('indexGoogleDrive upsert block marker missing');
index=index.replace(old,repl);
fs.writeFileSync(indexPath,index,'utf8');
const helperRel='cells/micro/frontend/082a-upsertdriveresource.cell.js';
const helper=`function upsertDriveResource(x,newId){const next={type:'PDF',course:x.course,topic:x.topic,level:x.level,title:x.title||x.name,url:x.webViewLink||'',driveFileId:x.id,driveModifiedTime:x.modifiedTime||null,driveSource:true};const matches=db.resources.map((r,i)=>({r,i})).filter(z=>z.r.driveFileId===x.id);if(matches.length){Object.assign(matches[0].r,next);for(let i=matches.length-1;i>=1;i--)db.resources.splice(matches[i].i,1);return 'updated'}db.resources.push({id:newId,...next});return 'added'}\n`;
fs.writeFileSync(path.join(ROOT,helperRel),helper,'utf8');
const frontend=[];
for(const e of m.frontend){if(e.name==='indexGoogleDrive')frontend.push(fs.readFileSync(path.join(ROOT,helperRel),'utf8'));frontend.push(fs.readFileSync(path.join(ROOT,e.file),'utf8'))}
const backend=m.backend.map(x=>fs.readFileSync(path.join(ROOT,x.file),'utf8')).join('');
fs.writeFileSync(path.join(ROOT,'app','public','app.js'),frontend.join(''),'utf8');
fs.writeFileSync(path.join(ROOT,'app','server.js'),backend,'utf8');
fs.writeFileSync(path.join(ROOT,'app','VERSION'),'0.9.2\n','utf8');
console.log('v0.9.2 source-cell patch applied');
