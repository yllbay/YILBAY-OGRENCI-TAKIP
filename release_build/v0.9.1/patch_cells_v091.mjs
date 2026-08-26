import fs from 'fs';
import path from 'path';
const ROOT='/tmp/yilbay091';
const manifestPath=path.join(ROOT,'cells','micro-cell-manifest.json');
const m=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(m.version!=='0.9.0'||m.protocol!=='micro-cell-v2-ast') throw new Error('Expected verified v0.9.0 micro-cell source');
const all=[...m.frontend,...m.backend];
for(const e of all){const p=path.join(ROOT,e.file);let s=fs.readFileSync(p,'utf8');s=s.replaceAll('0.9.0','0.9.1');fs.writeFileSync(p,s,'utf8')}
const metaEntry=m.backend.find(x=>x.name==='driveMetadataFromFile');
if(!metaEntry) throw new Error('driveMetadataFromFile cell missing');
const metaPath=path.join(ROOT,metaEntry.file);
let meta=fs.readFileSync(metaPath,'utf8');
if(meta.includes('normalizeCourseName(course)')) throw new Error('normalization already present unexpectedly');
meta=meta.replace('return {course,topic,level,title:', 'course=normalizeCourseName(course);return {course,topic,level,title:');
if(!meta.includes('normalizeCourseName(course)')) throw new Error('drive metadata patch failed');
fs.writeFileSync(metaPath,meta,'utf8');
const helperRel='cells/micro/backend/036a-normalizecoursename.cell.js';
const helper=`function normalizeCourseName(value){const raw=String(value||'').trim().replace(/\\s+/g,' ');const key=raw.toLocaleLowerCase('tr-TR').replace(/[\\s_.-]+/g,'');const aliases={lgsmatematik:'LGS Matematik',tytmatematik:'TYT Matematik',aytmatematik:'AYT Matematik',lgsgeometri:'LGS Geometri',tytgeometri:'TYT Geometri',aytgeometri:'AYT Geometri',turkce:'Türkçe',paragraf:'Paragraf',problemler:'Problemler'};return aliases[key]||raw.replace(/\\b(lgs|tyt|ayt)\\b/gi,x=>x.toUpperCase())}\n`;
fs.writeFileSync(path.join(ROOT,helperRel),helper,'utf8');
const f=m.frontend.map(x=>fs.readFileSync(path.join(ROOT,x.file),'utf8')).join('');
const backend=[];
for(const e of m.backend){if(e.name==='driveMetadataFromFile') backend.push(fs.readFileSync(path.join(ROOT,helperRel),'utf8'));backend.push(fs.readFileSync(path.join(ROOT,e.file),'utf8'))}
fs.writeFileSync(path.join(ROOT,'app','public','app.js'),f,'utf8');
fs.writeFileSync(path.join(ROOT,'app','server.js'),backend.join(''),'utf8');
fs.writeFileSync(path.join(ROOT,'app','VERSION'),'0.9.1\n','utf8');
console.log('v0.9.1 source-cell patch applied');
