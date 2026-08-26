import fs from 'fs';
import path from 'path';
const ROOT='/tmp/yilbay095';
const manifestPath=path.join(ROOT,'cells','micro-cell-manifest.json');
const m=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(m.version!=='0.9.4'||m.protocol!=='micro-cell-v2-ast')throw new Error('Expected verified v0.9.4 source');
for(const e of [...m.frontend,...m.backend]){const p=path.join(ROOT,e.file);let s=fs.readFileSync(p,'utf8');s=s.replaceAll('0.9.4','0.9.5');fs.writeFileSync(p,s,'utf8')}

const finalEntry=m.frontend[m.frontend.length-1];
if(!finalEntry||!fs.readFileSync(path.join(ROOT,finalEntry.file),'utf8').includes('dashboard()'))throw new Error('dashboard init cell missing');
const profileRel='cells/micro/frontend/087a-applyviewportprofile.cell.js';
const resizeRel='cells/micro/frontend/087b-viewportresize-listener.cell.js';
const initRel='cells/micro/frontend/087c-applyviewportprofile-init.cell.js';
const profile=`function applyViewportProfile(){const w=Math.max(0,Math.round(window.innerWidth||document.documentElement.clientWidth||0)),h=Math.max(0,Math.round(window.innerHeight||document.documentElement.clientHeight||0)),dpr=Math.max(1,Number(window.devicePixelRatio)||1),root=document.documentElement;let density='normal';if(w<900)density='narrow';else if(h<800||w<1400)density='compact';root.dataset.uiDensity=density;root.style.setProperty('--viewport-w',w+'px');root.style.setProperty('--viewport-h',h+'px');root.style.setProperty('--device-scale',String(dpr));return {width:w,height:h,dpr,density}}\n`;
const resize=`window.addEventListener('resize',applyViewportProfile,{passive:true})\n`;
const init=`applyViewportProfile()\n`;
fs.writeFileSync(path.join(ROOT,profileRel),profile,'utf8');fs.writeFileSync(path.join(ROOT,resizeRel),resize,'utf8');fs.writeFileSync(path.join(ROOT,initRel),init,'utf8');

const frontend=[];
for(const e of m.frontend){if(e===finalEntry){frontend.push(profile,resize,init)}frontend.push(fs.readFileSync(path.join(ROOT,e.file),'utf8'))}
const backend=m.backend.map(e=>fs.readFileSync(path.join(ROOT,e.file),'utf8')).join('');
fs.writeFileSync(path.join(ROOT,'app','public','app.js'),frontend.join(''),'utf8');
fs.writeFileSync(path.join(ROOT,'app','server.js'),backend,'utf8');
fs.writeFileSync(path.join(ROOT,'app','VERSION'),'0.9.5\n','utf8');

const design=path.join(ROOT,'cells','design-system','00-design-system.cell.css');
let css=fs.readFileSync(design,'utf8');
const adaptive=`\n/* CELL:adaptive-viewport | shared visual contract */\n:root{--topbar-h:clamp(56px,6.4vh,68px);--sidebar-fluid:clamp(210px,14vw,260px);--page-pad-x:clamp(14px,2vw,32px);--page-pad-y:clamp(14px,2.2vh,28px);--ui-gap:clamp(10px,1vw,14px);--modal-pad:clamp(14px,2vw,24px)}\nhtml,body{width:100%;max-width:100%;min-width:0;min-height:100%;overflow-x:hidden}\n.top{height:var(--topbar-h);padding-left:var(--page-pad-x);padding-right:var(--page-pad-x)}\n.layout{grid-template-columns:var(--sidebar-fluid) minmax(0,1fr);min-height:calc(100dvh - var(--topbar-h))}\naside{top:var(--topbar-h);height:calc(100dvh - var(--topbar-h));min-width:0}\nmain{padding:var(--page-pad-y) var(--page-pad-x) clamp(24px,4vh,44px);min-width:0;max-width:100%}\n.page{width:100%;max-width:min(1600px,100%);min-width:0}\n.grid{grid-template-columns:repeat(auto-fit,minmax(min(210px,100%),1fr));gap:var(--ui-gap)}\n.integration-grid{grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr));gap:var(--ui-gap)}\n.formgrid{grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr));gap:var(--ui-gap)}\n.weekgrid{grid-template-columns:repeat(auto-fit,minmax(min(180px,100%),1fr));gap:var(--ui-gap)}\n.profile-hero{grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr));gap:var(--ui-gap)}\n.table-wrap{width:100%;max-width:100%;overflow:auto;overscroll-behavior-inline:contain}\ntable{max-width:none}\n.modalbg{padding:clamp(8px,2vw,24px);overflow:hidden}\n.modal{width:min(760px,calc(100vw - clamp(16px,4vw,48px)));max-width:100%;max-height:calc(100dvh - clamp(16px,4vh,48px));padding:var(--modal-pad);overscroll-behavior:contain}\nimg,video,canvas,svg{max-width:100%}\ninput,select,textarea{max-width:100%}\nhtml[data-ui-density='compact']{--topbar-h:56px;--page-pad-y:14px;--ui-gap:10px}\nhtml[data-ui-density='compact'] .card{padding:14px}\nhtml[data-ui-density='compact'] .kpi-card{min-height:92px}\nhtml[data-ui-density='compact'] .page-head{margin-bottom:14px}\nhtml[data-ui-density='compact'] .page-title h1{font-size:clamp(20px,2vw,24px)}\nhtml[data-ui-density='compact'] aside{padding-top:10px;padding-bottom:10px}\n@media(max-height:720px) and (min-width:761px){.nav{padding-top:7px;padding-bottom:7px}.nav-section{padding-top:8px}.card{padding:12px}.section{margin-top:16px}.modal-actions{margin-top:12px;padding-top:12px}}\n@media(max-width:1100px){:root{--sidebar-fluid:clamp(190px,20vw,220px)}.page-title h1{font-size:clamp(21px,2.4vw,26px)}}\n@media(max-width:760px){.layout{grid-template-columns:1fr;min-height:calc(100dvh - var(--topbar-h))}aside{height:auto;top:auto;max-width:100vw}.top-right{min-width:0}.version{max-width:34vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.modal-actions{flex-wrap:wrap}.modal-actions .btn{flex:1 1 140px}}\n@media(max-width:480px){:root{--page-pad-x:10px;--modal-pad:12px}.top{gap:8px}.brandmark{width:30px;height:30px}.brand{font-size:13px}.page-actions .btn,.toolbar-group .btn{flex:1 1 auto}.card{padding:12px}.empty{padding:20px 12px}}\n`;
if(!css.includes('CELL:adaptive-viewport'))css+=adaptive;
fs.writeFileSync(design,css,'utf8');
fs.writeFileSync(path.join(ROOT,'app','public','styles.css'),css.replace('/* CELL:design-system | shared visual contract */\n',''),'utf8');
console.log('v0.9.5 adaptive viewport patch applied');
