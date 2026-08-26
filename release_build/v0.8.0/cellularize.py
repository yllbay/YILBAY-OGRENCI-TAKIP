from pathlib import Path
import json, shutil

ROOT=Path('/tmp/yilbay080')
APP=ROOT/'app'
PUB=APP/'public'
CELLS=ROOT/'cells'

front=(PUB/'app.js').read_text(encoding='utf-8')
server=(APP/'server.js').read_text(encoding='utf-8')

front=front.replace('v0.7.2','v0.8.0')
server=server.replace('version:"0.7.2"','version:"0.8.0"').replace('READY 0.7.2','READY 0.8.0')

def split_by_markers(text, specs):
    starts=[]
    for name,marker in specs:
        i=text.find(marker)
        if i<0: raise SystemExit(f'Marker bulunamadı: {name}: {marker}')
        starts.append((i,name,marker))
    if starts!=sorted(starts): raise SystemExit('Marker sırası bozuk')
    out=[]
    for n,(i,name,_) in enumerate(starts):
        j=starts[n+1][0] if n+1<len(starts) else len(text)
        out.append((name,text[i:j]))
    return out

front_specs=[
 ('00-core-store-ui','const STORAGE='),
 ('10-dashboard','function dashboard(){'),
 ('20-students-profile','function students(){'),
 ('30-curriculum','function curriculum(){'),
 ('40-resources','function resources(){'),
 ('50-exams','function exams(){'),
 ('60-assignments-results','function assignments(){'),
 ('70-planner','let selectedStudentId=null;'),
 ('80-api-client','async function apiJson(url,body=null){'),
 ('90-integrations','function integrations(){'),
 ('100-ai-planner','window.generateAiMasterPlan=async()=>{'),
 ('110-youtube','window.findTopicVideo=async(course,topic)=>{'),
 ('120-ai-homework','window.analyzeAssignment=id=>{'),
 ('130-ui-runtime','function q(id){return document.getElementById(id)}'),
]
front_cells=split_by_markers(front,front_specs)
# Son hücredeki doğrudan başlangıcı bundle bootstrap'a taşı.
front_cells[-1]=(front_cells[-1][0],front_cells[-1][1].replace('\ndashboard();','\n'))

server_specs=[
 ('00-runtime','const http=require('),
 ('10-secrets-integrations','const OPENAI_CREDENTIAL_TARGET='),
 ('20-cost-accounting','const OPENAI_PRICES='),
 ('30-http-openai-core','function json(res,status,obj){'),
 ('40-academic-planner','function flattenCurriculum(curriculum,courses){'),
 ('50-homework-vision','function normalizeHomeworkAnalysis(x={}){'),
 ('60-youtube','async function handleYoutube(req,res){'),
 ('70-routes','http.createServer(async(req,res)=>{'),
]
server_cells=split_by_markers(server,server_specs)

if CELLS.exists(): shutil.rmtree(CELLS)
(CELLS/'frontend').mkdir(parents=True)
(CELLS/'backend').mkdir(parents=True)

manifest={'version':'1.0','protocol':'CELL_PROTOCOL.md','runtimeVersion':'0.8.0','frontend':[],'backend':[],'rules':{'runtimeBundlesAreGenerated':True,'directBundleEditingForbidden':True}}

for order,(name,body) in enumerate(front_cells):
    p=CELLS/'frontend'/f'{name}.cell.js'
    p.write_text(f'/* CELL:{name} | layer:frontend | generated-from:v0.7.2 */\n'+body.strip()+"\n",encoding='utf-8')
    manifest['frontend'].append({'id':name,'path':str(p.relative_to(ROOT)).replace('\\','/'),'order':order})
for order,(name,body) in enumerate(server_cells):
    p=CELLS/'backend'/f'{name}.cell.js'
    p.write_text(f'/* CELL:{name} | layer:backend | generated-from:v0.7.2 */\n'+body.strip()+"\n",encoding='utf-8')
    manifest['backend'].append({'id':name,'path':str(p.relative_to(ROOT)).replace('\\','/'),'order':order})

(CELLS/'cell-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

# Runtime bundle hücrelerden otomatik üretilir. Elle düzenlenmez.
front_bundle='\n'.join((ROOT/x['path']).read_text(encoding='utf-8') for x in manifest['frontend'])+'\n/* CELL:bootstrap */\ndashboard();\n'
server_bundle='\n'.join((ROOT/x['path']).read_text(encoding='utf-8') for x in manifest['backend'])
(PUB/'app.js').write_text(front_bundle,encoding='utf-8')
(APP/'server.js').write_text(server_bundle,encoding='utf-8')
(ROOT/'VERSION').write_text('0.8.0\n',encoding='utf-8')

# Design system de bağımsız hücre olarak kaynaklanır; runtime styles.css buradan üretilir.
style=(PUB/'styles.css').read_text(encoding='utf-8')
(CELLS/'design-system').mkdir(parents=True)
(CELLS/'design-system'/'00-design-system.cell.css').write_text('/* CELL:design-system | shared visual contract */\n'+style,encoding='utf-8')
manifest['designSystem']=[{'id':'00-design-system','path':'cells/design-system/00-design-system.cell.css','order':0}]
(CELLS/'cell-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

# Hücre sözleşme kontrol betiği.
test='''const fs=require("fs"),path=require("path");\nconst root=path.resolve(__dirname,"..");\nconst m=JSON.parse(fs.readFileSync(path.join(root,"cells/cell-manifest.json"),"utf8"));\nlet bad=false;\nfor(const group of [m.frontend,m.backend,m.designSystem||[]]) for(const c of group){const p=path.join(root,c.path);if(!fs.existsSync(p)||!fs.statSync(p).size){console.error("CELL MISSING",c.id);bad=true}else console.log("CELL OK",c.id);if(p.endsWith(".js")){try{new Function(fs.readFileSync(p,"utf8"));console.log("CELL SYNTAX OK",c.id)}catch(e){console.error("CELL SYNTAX",c.id,e.message);bad=true}}}\nconst ids=[...m.frontend,...m.backend].map(x=>x.id);if(new Set(ids).size!==ids.length){console.error("DUPLICATE CELL ID");bad=true}\nprocess.exit(bad?1:0);\n'''
(APP/'cell-tests.js').write_text(test,encoding='utf-8')

readme='''# YILBAY Öğrenci Takip — v0.8.0\n\nHücresel geliştirme mimarisine geçiş.\n\n- Geliştirme kaynağı: `cells/`\n- Hücre manifesti: `cells/cell-manifest.json`\n- Runtime `app.js` ve `server.js` otomatik bundle'dır; elle düzenlenmez.\n- Her yeni özellik ayrı hücre olarak eklenir.\n- CELL_PROTOCOL.md proje standardıdır.\n'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')
print('cellularized',len(front_cells),'frontend',len(server_cells),'backend')
