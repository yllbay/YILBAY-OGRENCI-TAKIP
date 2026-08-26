import fs from 'fs';
import path from 'path';
const ROOT='/tmp/yilbay099';
const manifestPath=path.join(ROOT,'cells','micro-cell-manifest.json');
const m=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(m.version!=='0.9.8'||m.protocol!=='micro-cell-v2-ast')throw new Error('Expected verified v0.9.8 source');
for(const e of [...m.frontend,...m.backend]){const p=path.join(ROOT,e.file);let s=fs.readFileSync(p,'utf8');s=s.replaceAll('0.9.8','0.9.9');fs.writeFileSync(p,s,'utf8')}
const modalEntry=m.frontend.find(x=>x.name==='assignmentModal');
if(!modalEntry)throw new Error('assignmentModal cell missing');
const modalPath=path.join(ROOT,modalEntry.file);
const modalCell=`window.assignmentModal=()=>{modal(\`<h2>Yeni Atama</h2><div class="formgrid">\n<div class="field"><label>Öğrenci</label><select id="astudent">\${db.students.map(s=>\`<option value="\${s.id}">\${s.name}</option>\`).join("")}</select></div>\n<div class="field"><label>Atama türü</label><select id="akind" onchange="refreshAssignmentItems()"><option>PDF Kaynak</option><option>Online Sınav</option></select></div>\n<div class="field" style="grid-column:1/-1"><label>İçerik</label><select id="aitem"></select></div>\n</div><div class="modal-actions"><button class="btn primary" onclick="addAssignment()">Ata</button> <button class="btn ghost" onclick="closeModal()">İptal</button></div>\`);refreshAssignmentItems()}\n`;
fs.writeFileSync(modalPath,modalCell,'utf8');
const frontend=m.frontend.map(e=>fs.readFileSync(path.join(ROOT,e.file),'utf8')).join('');
const backend=m.backend.map(e=>fs.readFileSync(path.join(ROOT,e.file),'utf8')).join('');
fs.writeFileSync(path.join(ROOT,'app','public','app.js'),frontend,'utf8');
fs.writeFileSync(path.join(ROOT,'app','server.js'),backend,'utf8');
fs.writeFileSync(path.join(ROOT,'app','VERSION'),'0.9.9\n','utf8');
console.log('v0.9.9 assignment modal initialization patch applied');
