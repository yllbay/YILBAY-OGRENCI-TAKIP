import fs from 'fs';
import path from 'path';
const ROOT='/tmp/yilbay097';
const manifestPath=path.join(ROOT,'cells','micro-cell-manifest.json');
const m=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(m.version!=='0.9.6'||m.protocol!=='micro-cell-v2-ast')throw new Error('Expected verified v0.9.6 source');
for(const e of [...m.frontend,...m.backend]){const p=path.join(ROOT,e.file);let s=fs.readFileSync(p,'utf8');s=s.replaceAll('0.9.6','0.9.7');fs.writeFileSync(p,s,'utf8')}

const listEntry=m.backend.find(x=>x.name==='driveListPdfIndex');
const handleEntry=m.backend.find(x=>x.name==='handleDriveIndex');
const indexEntry=m.frontend.find(x=>x.name==='indexGoogleDrive');
const statusEntry=m.frontend.find(x=>x.name==='loadDriveStatus');
if(!listEntry||!handleEntry||!indexEntry||!statusEntry)throw new Error('Drive cells missing');

const isKeyRel='cells/micro/backend/041a-isdriveanswerkeyfile.cell.js';
const pairKeyRel='cells/micro/backend/041b-drivepairkey.cell.js';
const pairRel='cells/micro/backend/041c-pairdriveanswerkeys.cell.js';
const isKeySrc=`function isDriveAnswerKeyFile(file){return /__(CEVAP|CEVAP[_ -]?ANAHTARI|ANSWER[_ -]?KEY)\\.pdf$/i.test(String(file?.name||''))}\n`;
const pairKeySrc=`function drivePairKey(name){return String(name||'').replace(/\\.pdf$/i,'').replace(/__(CEVAP|CEVAP[_ -]?ANAHTARI|ANSWER[_ -]?KEY)$/i,'').trim().toLocaleLowerCase('tr-TR').replace(/\\s+/g,' ')}\n`;
const pairSrc=`function pairDriveAnswerKeys(files){const keys=new Map(),sources=[];for(const f of files||[]){const k=drivePairKey(f.name);if(isDriveAnswerKeyFile(f)){const a=keys.get(k)||[];a.push(f);keys.set(k,a)}else sources.push(f)}let paired=0,ambiguous=0;const items=sources.map(f=>{const md=driveMetadataFromFile(f),candidates=keys.get(drivePairKey(f.name))||[];let answerKeyDriveFileId=md.answerKeyDriveFileId||'',answerKeyAutoMatched=false,answerKeyAmbiguous=false;if(!answerKeyDriveFileId&&candidates.length===1){answerKeyDriveFileId=candidates[0].id;answerKeyAutoMatched=true;paired++}else if(!answerKeyDriveFileId&&candidates.length>1){answerKeyAmbiguous=true;ambiguous++}return {...f,...md,answerKeyDriveFileId,answerKeyAutoMatched,answerKeyAmbiguous}});return {items,answerKeyCount:[...keys.values()].reduce((n,a)=>n+a.length,0),pairedAnswerKeyCount:paired,ambiguousAnswerKeyCount:ambiguous,unpairedAnswerKeyCount:[...keys.values()].reduce((n,a)=>n+a.length,0)-paired}}\n`;
fs.writeFileSync(path.join(ROOT,isKeyRel),isKeySrc,'utf8');
fs.writeFileSync(path.join(ROOT,pairKeyRel),pairKeySrc,'utf8');
fs.writeFileSync(path.join(ROOT,pairRel),pairSrc,'utf8');

const listPath=path.join(ROOT,listEntry.file);let list=fs.readFileSync(listPath,'utf8');
list=list.replace('return files.map(f=>({...f,...driveMetadataFromFile(f)}))','return pairDriveAnswerKeys(files)');
if(!list.includes('return pairDriveAnswerKeys(files)'))throw new Error('driveListPdfIndex patch failed');
fs.writeFileSync(listPath,list,'utf8');

const handlePath=path.join(ROOT,handleEntry.file);let handle=fs.readFileSync(handlePath,'utf8');
handle=handle.replace('const items=await driveListPdfIndex();return json(res,200,{ok:true,items,matchedCount:items.filter(x=>x.matched).length,unmatchedCount:items.filter(x=>!x.matched).length})','const result=await driveListPdfIndex(),items=result.items||[];return json(res,200,{ok:true,items,matchedCount:items.filter(x=>x.matched).length,unmatchedCount:items.filter(x=>!x.matched).length,answerKeyCount:result.answerKeyCount||0,pairedAnswerKeyCount:result.pairedAnswerKeyCount||0,ambiguousAnswerKeyCount:result.ambiguousAnswerKeyCount||0,unpairedAnswerKeyCount:result.unpairedAnswerKeyCount||0})');
if(!handle.includes('pairedAnswerKeyCount'))throw new Error('handleDriveIndex patch failed');
fs.writeFileSync(handlePath,handle,'utf8');

const indexPath=path.join(ROOT,indexEntry.file);let idx=fs.readFileSync(indexPath,'utf8');
idx=idx.replace('Yeni kaynak: ${added}\\nGüncellenen: ${updated}`)', 'Yeni kaynak: ${added}\\nGüncellenen: ${updated}\\nCevap anahtarı: ${d.answerKeyCount||0}\\nOtomatik eşleşen cevap anahtarı: ${d.pairedAnswerKeyCount||0}\\nBelirsiz eşleşme: ${d.ambiguousAnswerKeyCount||0}`)');
if(!idx.includes('Otomatik eşleşen cevap anahtarı'))throw new Error('indexGoogleDrive patch failed');
fs.writeFileSync(indexPath,idx,'utf8');

const statusPath=path.join(ROOT,statusEntry.file);let st=fs.readFileSync(statusPath,'utf8');
st=st.replace('<div class="integration-meta">Klasör:', '<div class="integration-meta"><div style="margin-bottom:8px"><b>Cevap anahtarı:</b> Kaynak dosya adının sonuna <code>__CEVAP</code> ekleyin.<br><span class="muted">Örn: <code>...__Test 01.pdf</code> → <code>...__Test 01__CEVAP.pdf</code></span></div>Klasör:');
if(!st.includes('__CEVAP'))throw new Error('loadDriveStatus hint patch failed');
fs.writeFileSync(statusPath,st,'utf8');

const frontend=m.frontend.map(e=>fs.readFileSync(path.join(ROOT,e.file),'utf8')).join('');
const backend=[];
for(const e of m.backend){if(e.name==='driveListPdfIndex')backend.push(isKeySrc,pairKeySrc,pairSrc);backend.push(fs.readFileSync(path.join(ROOT,e.file),'utf8'))}
fs.writeFileSync(path.join(ROOT,'app','public','app.js'),frontend,'utf8');
fs.writeFileSync(path.join(ROOT,'app','server.js'),backend.join(''),'utf8');
fs.writeFileSync(path.join(ROOT,'app','VERSION'),'0.9.7\n','utf8');
console.log('v0.9.7 automatic Drive answer-key pairing patch applied');
