from pathlib import Path
import json,re,shutil

SRC=Path('/tmp/yilbay081')
APP=SRC/'app/public/app.js'
SERVER=SRC/'app/server.js'
CELLS=SRC/'cells'
MICRO=CELLS/'micro'


def split_top_level(src:str):
    out=[]; start=0; i=0; n=len(src); depth=0; par=0; br=0; state='code'; esc=False
    line_comment=False; block_comment=False; regex=False; regex_class=False
    def next_nonspace(j):
        while j<n and src[j].isspace(): j+=1
        return src[j] if j<n else ''
    prev_sig=''
    while i<n:
        c=src[i]; d=src[i+1] if i+1<n else ''
        if state=='sq':
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=="'": state='code'
            i+=1; continue
        if state=='dq':
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='"': state='code'
            i+=1; continue
        if state=='tpl':
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='`': state='code'
            i+=1; continue
        if line_comment:
            if c=='\n': line_comment=False
            i+=1; continue
        if block_comment:
            if c=='*' and d=='/': block_comment=False; i+=2; continue
            i+=1; continue
        if regex:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='[': regex_class=True
            elif c==']': regex_class=False
            elif c=='/' and not regex_class:
                regex=False
                i+=1
                while i<n and src[i].isalpha(): i+=1
                prev_sig='/'
                continue
            i+=1; continue
        if c=='/' and d=='/': line_comment=True; i+=2; continue
        if c=='/' and d=='*': block_comment=True; i+=2; continue
        if c=="'": state='sq'; i+=1; continue
        if c=='"': state='dq'; i+=1; continue
        if c=='`': state='tpl'; i+=1; continue
        if c=='/':
            # Regex literal heuristic; enough for current generated source.
            if prev_sig in ('','(','[','{','=',':',',',';','!','?','|','&'):
                regex=True; regex_class=False; i+=1; continue
        if c=='{': depth+=1
        elif c=='}': depth=max(0,depth-1)
        elif c=='(': par+=1
        elif c==')': par=max(0,par-1)
        elif c=='[': br+=1
        elif c==']': br=max(0,br-1)
        if not c.isspace(): prev_sig=c
        # A top-level semicolon is always a safe statement boundary.
        if c==';' and depth==0 and par==0 and br==0:
            seg=src[start:i+1]
            if seg.strip(): out.append(seg)
            start=i+1
        # Function declarations often end without a semicolon. Detect closing brace
        # followed by a new top-level declaration / assignment.
        elif c=='}' and depth==0 and par==0 and br==0:
            j=i+1
            while j<n and src[j].isspace(): j+=1
            tail=src[start:i+1].lstrip()
            nxt=src[j:j+32]
            if (tail.startswith('function ') or tail.startswith('async function ')) and re.match(r'(?:async\s+function|function|const|let|var|window\.|http\.)',nxt):
                seg=src[start:i+1]
                if seg.strip(): out.append(seg)
                start=i+1
        i+=1
    if src[start:].strip(): out.append(src[start:])
    return out


def safe_name(seg, idx, side):
    s=seg.strip()
    pats=[
      r'^async\s+function\s+([A-Za-z_$][\w$]*)',
      r'^function\s+([A-Za-z_$][\w$]*)',
      r'^window\.([A-Za-z_$][\w$]*)\s*=',
      r'^(?:const|let|var)\s+([A-Za-z_$][\w$]*)',
    ]
    name=None
    for p in pats:
        m=re.search(p,s)
        if m: name=m.group(1); break
    if not name:
        if s.startswith('http.createServer'): name='http-server-routes'
        else: name=f'statement-{idx:03d}'
    name=re.sub(r'[^A-Za-z0-9_-]+','-',name).strip('-').lower()
    return f'{idx:03d}-{name}.cell.js'


def write_side(path:Path, side:str):
    src=path.read_text(encoding='utf-8')
    parts=split_top_level(src)
    target=MICRO/side
    shutil.rmtree(target,ignore_errors=True); target.mkdir(parents=True,exist_ok=True)
    files=[]
    rebuilt=''
    for idx,seg in enumerate(parts,1):
        fn=safe_name(seg,idx,side)
        p=target/fn
        text=seg
        if not text.endswith('\n'): text+='\n'
        p.write_text(text,encoding='utf-8')
        files.append(str(p.relative_to(SRC)).replace('\\','/'))
        rebuilt+=text
    # semantic source equality after whitespace-only boundary normalization
    norm=lambda x: re.sub(r'\s+',' ',x).strip()
    if norm(rebuilt)!=norm(src):
        raise SystemExit(f'{side}: rebuilt bundle differs from source')
    return files,parts

frontend,fp=write_side(APP,'frontend')
backend,bp=write_side(SERVER,'backend')

# Design system remains a shared pure presentation cell; functions/actions are micro-celled.
design=[]
old_design=CELLS/'design-system/00-design-system.cell.css'
if old_design.exists(): design=[str(old_design.relative_to(SRC)).replace('\\','/')]

manifest={
 'protocol':'micro-cell-v1',
 'version':'0.8.1',
 'rule':'one-top-level-behavior-per-cell',
 'frontend':frontend,
 'backend':backend,
 'designSystem':design,
 'counts':{'frontend':len(frontend),'backend':len(backend),'totalJs':len(frontend)+len(backend)},
 'generatedFrom':['app/public/app.js','app/server.js'],
 'runtimeBundlesAreGenerated':True
}
(CELLS/'micro-cell-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

# Runtime bundle is now generated strictly from micro cells.
APP.write_text(''.join((SRC/f).read_text(encoding='utf-8') for f in frontend),encoding='utf-8')
SERVER.write_text(''.join((SRC/f).read_text(encoding='utf-8') for f in backend),encoding='utf-8')

# Version strings.
for p in [SRC/'VERSION']:
    p.write_text('0.8.1\n',encoding='utf-8')
for p in [APP,SERVER]:
    s=p.read_text(encoding='utf-8').replace('v0.8.0','v0.8.1').replace('version:"0.8.0"','version:"0.8.1"')
    p.write_text(s,encoding='utf-8')
# Re-split after version modification so cells remain canonical.
frontend,_=write_side(APP,'frontend')
backend,_=write_side(SERVER,'backend')
manifest['frontend']=frontend; manifest['backend']=backend
manifest['counts']={'frontend':len(frontend),'backend':len(backend),'totalJs':len(frontend)+len(backend)}
(CELLS/'micro-cell-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
APP.write_text(''.join((SRC/f).read_text(encoding='utf-8') for f in frontend),encoding='utf-8')
SERVER.write_text(''.join((SRC/f).read_text(encoding='utf-8') for f in backend),encoding='utf-8')
print(json.dumps(manifest['counts']))
