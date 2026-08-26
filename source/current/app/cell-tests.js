const fs=require("fs"),path=require("path");
const root=path.resolve(__dirname,"..");
const m=JSON.parse(fs.readFileSync(path.join(root,"cells/cell-manifest.json"),"utf8"));
let bad=false;
for(const group of [m.frontend,m.backend,m.designSystem||[]]) for(const c of group){const p=path.join(root,c.path);if(!fs.existsSync(p)||!fs.statSync(p).size){console.error("CELL MISSING",c.id);bad=true}else console.log("CELL OK",c.id);if(p.endsWith(".js")){try{new Function(fs.readFileSync(p,"utf8"));console.log("CELL SYNTAX OK",c.id)}catch(e){console.error("CELL SYNTAX",c.id,e.message);bad=true}}}
const ids=[...m.frontend,...m.backend].map(x=>x.id);if(new Set(ids).size!==ids.length){console.error("DUPLICATE CELL ID");bad=true}
process.exit(bad?1:0);
