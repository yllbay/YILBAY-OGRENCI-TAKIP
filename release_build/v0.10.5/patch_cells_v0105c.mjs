import './patch_cells_v0105b.mjs';
import fs from 'fs';
const p='/tmp/yilbay0105/app/server.js';
let s=fs.readFileSync(p,'utf8');
s=s.replace('Üst düzey öğrenci karnesinde strengths, recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve summary üret.','Üst düzey öğrenci karnesini reasoningProfile içinde strengths, recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve summary alanlarıyla üret.');
if(!s.includes('reasoningProfile içinde strengths'))throw new Error('reasoningProfile instruction patch failed');
fs.writeFileSync(p,s,'utf8');
const root='/tmp/yilbay0105',m=JSON.parse(fs.readFileSync(root+'/cells/micro-cell-manifest.json','utf8'));
const h=m.backend.find(x=>x.name==='handleHomework');if(h){const hp=root+'/'+h.file;let hs=fs.readFileSync(hp,'utf8');hs=hs.replace('Üst düzey öğrenci karnesinde strengths, recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve summary üret.','Üst düzey öğrenci karnesini reasoningProfile içinde strengths, recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve summary alanlarıyla üret.');fs.writeFileSync(hp,hs,'utf8')}
console.log('v0.10.5 reasoningProfile instruction aligned');