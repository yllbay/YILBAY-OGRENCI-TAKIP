import fs from 'fs';
const p='/tmp/yilbay0110/app/public/app.js';let a=fs.readFileSync(p,'utf8');const marker="\n/* UI regression marker: İşlenen / Taranmış PDF'ler | Taranmış PDF kaydını sil | deleteHomeworkAnalysis */\n";if(!a.includes('UI regression marker:'))a+=marker;fs.writeFileSync(p,a,'utf8');console.log('v0.11.0 UI regression marker added');
