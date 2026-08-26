import fs from 'fs';
const p='/tmp/yilbay0110/app/server.js';let s=fs.readFileSync(p,'utf8');
const bad='Yalnız geçerli kısa JSON döndür.\n`}\n}\nfunction homeworkMathVerificationTargets';
const good='Yalnız geçerli kısa JSON döndür.\n`}\nfunction homeworkMathVerificationTargets';
if(!s.includes(bad))throw new Error('backend closure anchor');s=s.replace(bad,good);fs.writeFileSync(p,s,'utf8');console.log('v0.11.0 backend closure fixed');
