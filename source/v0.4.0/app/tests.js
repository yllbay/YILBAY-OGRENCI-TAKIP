const fs=require("fs"),path=require("path");
const req=["server.js","public/index.html","public/styles.css","public/app.js"];
let bad=false;
for(const f of req){const p=path.join(__dirname,f);if(!fs.existsSync(p)||!fs.statSync(p).size){console.error("MISSING",f);bad=true}else console.log("OK",f)}
for(const f of ["server.js","public/app.js"]){try{new Function(fs.readFileSync(path.join(__dirname,f),"utf8"));console.log("SYNTAX OK",f)}catch(e){console.error("SYNTAX",f,e.message);bad=true}}
process.exit(bad?1:0);
