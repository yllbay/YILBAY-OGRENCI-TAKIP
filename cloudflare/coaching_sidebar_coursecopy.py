from pathlib import Path
import os

ROOT = Path(os.environ.get('GENESIS_APP_ROOT', '/app/APP'))
FRONT = ROOT / 'frontend' / 'dist'
if not FRONT.exists():
    # audit snapshot layout used only for local validation
    alt = ROOT / 'frontend'
    if alt.exists():
        FRONT = alt

html_path = FRONT / 'coaching-v2.html'
js_path = FRONT / 'coaching-v2.js'
css_path = FRONT / 'coaching-v2.css'
for p in (html_path, js_path, css_path):
    if not p.exists():
        raise SystemExit(f'GENESIS coaching file missing: {p}')

HTML_MARK = 'GENESIS_COACHING_SIDEBAR_COURSE_COPY_V1'
JS_MARK = 'GENESIS_COACHING_COURSE_COPY_V1'
CSS_MARK = 'GENESIS_COACHING_COURSE_COPY_V1'

html = html_path.read_text(encoding='utf-8')
if HTML_MARK not in html:
    # Replace the sidebar prefix structurally. This supports both the original
    # production sidebar and the previously deployed quick-action variant.
    aside_start = '<aside class="sidebar">'
    list_marker = '<div id="studentList" class="student-list"></div>'
    a = html.find(aside_start)
    b = html.find(list_marker, a)
    if a < 0 or b < 0:
        raise SystemExit('Coaching sidebar structural patch point not found')
    b += len(list_marker)
    new_prefix = '<aside class="sidebar"><!-- '+HTML_MARK+' --><label class="search"><span>⌕</span><input id="studentSearch" placeholder="Öğrenci ara" autocomplete="off"></label><div class="side-actions"><button id="addStudent" class="sidebar-action primary">+ Öğrenci Ekle</button><button id="addCourseWorkspace" class="sidebar-action">+ Ders Ekle</button></div>'+list_marker
    html = html[:a] + new_prefix + html[b:]
    old_main = '<main class="main"><div id="empty" class="empty">'
    if 'id="courseWorkspace"' not in html:
        new_main = '<main class="main"><section id="courseWorkspace" class="course-copy-shell" hidden></section><div id="empty" class="empty">'
        if old_main not in html:
            raise SystemExit('Coaching main patch point not found')
        html = html.replace(old_main, new_main, 1)
    html_path.write_text(html, encoding='utf-8')

js = js_path.read_text(encoding='utf-8')
if JS_MARK not in js:
    needle_state = "const state={students:[],selected:null,dashboard:null,catalog:null,week:monday(nowDate()),tab:'overview',preview:null,examPreview:null,request:0};"
    if needle_state not in js:
        raise SystemExit('Coaching JS state patch point not found')
    course_code = r'''
// GENESIS_COACHING_COURSE_COPY_V1
// This workspace deliberately owns its own state and only uses read-only API calls.
// It must remain independent from the main GENESIS homepage implementation.
const courseCopy={open:false,loading:false,topics:[],questions:[],testTree:[],selectedTopic:null,expandedTopics:new Set(),expandedTests:new Set()};
function courseCopyFindTopic(id,xs=courseCopy.topics){for(const x of xs||[]){if(Number(x.id)===Number(id))return x;const y=courseCopyFindTopic(id,x.children||[]);if(y)return y}return null}
function courseCopyTopicRows(xs,depth=0){return (xs||[]).map(t=>{const kids=t.children||[],open=courseCopy.expandedTopics.has(Number(t.id));return `<div class="course-copy-node"><button class="course-copy-row ${courseCopy.selectedTopic===Number(t.id)?'on':''}" data-course-copy-topic="${t.id}" style="--course-copy-depth:${depth}"><span class="course-copy-twisty">${kids.length?(open?'▼':'▶'):''}</span><span class="course-copy-folder">▰</span><span>${esc(t.name)}</span></button>${kids.length&&open?`<div>${courseCopyTopicRows(kids,depth+1)}</div>`:''}</div>`}).join('')}
function courseCopyQuestionRows(){if(!courseCopy.selectedTopic)return '<div class="course-copy-empty">Bir konu seçin.</div>';if(!courseCopy.questions.length)return '<div class="course-copy-empty">Bu konuda kayıtlı soru yok.</div>';return courseCopy.questions.map((q,i)=>`<div class="course-copy-question"><span>${i+1}</span><div><b>${esc(q.label||q.question_no||q.source_question_no||('Soru '+(i+1)))}</b><small>${esc(q.difficulty||q.level||'Soru kaydı')}</small></div></div>`).join('')}
function courseCopyTestRows(xs,depth=0){return (xs||[]).map(c=>{const kids=c.children||[],exams=c.exams||[],has=kids.length||exams.length,open=courseCopy.expandedTests.has(Number(c.id));return `<div class="course-copy-node"><button class="course-copy-row" data-course-copy-test="${c.id}" style="--course-copy-depth:${depth}"><span class="course-copy-twisty">${has?(open?'▼':'▶'):''}</span><span class="course-copy-folder">▰</span><span>${esc(c.name)}</span></button>${has&&open?`<div>${courseCopyTestRows(kids,depth+1)}${exams.map(e=>`<div class="course-copy-exam" style="--course-copy-depth:${depth+1}"><span>▤</span><span>${esc(e.name)}</span><small>${Number(e.question_count||0)} soru</small></div>`).join('')}</div>`:''}</div>`}).join('')}
function renderCourseCopy(){const host=$('#courseWorkspace');if(!host)return;host.hidden=!courseCopy.open;if(!courseCopy.open)return;host.innerHTML=`<div class="course-copy-head"><div><div class="eyebrow">BAĞIMSIZ KOÇLUK ÇALIŞMA ALANI</div><h1>Ders Ekle</h1><p>Ana GENESIS ekranındaki konu, soru ve test menülerinin bağımsız kopyasıdır. Bu alanın state ve işlevleri ana sayfadan ayrıdır.</p></div><span class="course-copy-badge">Bağımsız Kopya</span></div>${courseCopy.loading?'<div class="course-copy-loading">Menüler yükleniyor…</div>':`<div class="course-copy-grid"><section class="course-copy-pane"><header><b>Konular</b><small>Konu Seç</small></header><div class="course-copy-scroll">${courseCopyTopicRows(courseCopy.topics)||'<div class="course-copy-empty">Konu bulunamadı.</div>'}</div></section><section class="course-copy-pane"><header><b>Konu Soruları</b><small>${esc(courseCopyFindTopic(courseCopy.selectedTopic)?.name||'Konu Seç')}</small></header><div class="course-copy-scroll">${courseCopyQuestionRows()}</div></section><section class="course-copy-pane"><header><b>Testler</b><small>Test Seç</small></header><div class="course-copy-scroll">${courseCopyTestRows(courseCopy.testTree)||'<div class="course-copy-empty">Test bulunamadı.</div>'}</div></section></div>`}`}
function closeCourseCopy(){courseCopy.open=false;const host=$('#courseWorkspace');if(host)host.hidden=true}
async function openCourseCopy(){courseCopy.open=true;courseCopy.loading=true;$('#empty').hidden=true;$('#dashboard').hidden=true;renderCourseCopy();try{const [topics,testTree]=await Promise.all([api('/api/topics'),api('/api/test-tree').catch(()=>[])]);courseCopy.topics=topics||[];courseCopy.testTree=testTree||[];courseCopy.loading=false;renderCourseCopy()}catch(e){courseCopy.loading=false;renderCourseCopy();toast(e.message,true)}}
async function selectCourseCopyTopic(id){const t=courseCopyFindTopic(id);if(!t)return;courseCopy.selectedTopic=Number(id);const kids=t.children||[];if(kids.length){courseCopy.expandedTopics.has(Number(id))?courseCopy.expandedTopics.delete(Number(id)):courseCopy.expandedTopics.add(Number(id))}try{courseCopy.questions=await api('/api/questions?topic_id='+encodeURIComponent(id))}catch{courseCopy.questions=[]}renderCourseCopy()}
function toggleCourseCopyTest(id){courseCopy.expandedTests.has(Number(id))?courseCopy.expandedTests.delete(Number(id)):courseCopy.expandedTests.add(Number(id));renderCourseCopy()}
'''
    js = js.replace(needle_state, needle_state + course_code, 1)

    old_select = "async function selectStudent(id){state.selected=id;state.preview=null;state.examPreview=null;state.tab='overview';state.week=monday(nowDate());$('#coachApp').classList.remove('show-students');renderStudents();await refreshDashboard()}"
    new_select = "async function selectStudent(id){closeCourseCopy();state.selected=id;state.preview=null;state.examPreview=null;state.tab='overview';state.week=monday(nowDate());$('#coachApp').classList.remove('show-students');renderStudents();await refreshDashboard()}"
    if old_select not in js:
        raise SystemExit('Coaching selectStudent patch point not found')
    js = js.replace(old_select, new_select, 1)

    old_click = "document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const d=b.dataset;\n if(d.student){action(()=>selectStudent(Number(d.student)));return}"
    new_click = "document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const d=b.dataset;\n if(d.courseCopyTopic){action(()=>selectCourseCopyTopic(Number(d.courseCopyTopic)));return}\n if(d.courseCopyTest){toggleCourseCopyTest(Number(d.courseCopyTest));return}\n if(d.student){action(()=>selectStudent(Number(d.student)));return}"
    if old_click not in js:
        raise SystemExit('Coaching delegated click patch point not found')
    js = js.replace(old_click, new_click, 1)

    original_handlers = "const handlers={addStudent:()=>studentForm(),emptyAdd:()=>studentForm(),homeBtn:()=>location.assign('/'),"
    quick_handlers = "const handlers={addStudent:()=>studentForm(),sideAddCourse:()=>{if(!state.selected||!state.dashboard){toast('Ders eklemek için önce bir öğrenci seçin.',true);return}/* GENESIS_COACHING_SIDEBAR_ACTIONS */setTab('courses');courseForm()},emptyAdd:()=>studentForm(),homeBtn:()=>location.assign('/'),"
    new_handlers = "const handlers={addStudent:()=>studentForm(),addCourseWorkspace:()=>action(openCourseCopy),emptyAdd:()=>studentForm(),homeBtn:()=>location.assign('/'),"
    if original_handlers in js:
        js = js.replace(original_handlers, new_handlers, 1)
    elif quick_handlers in js:
        js = js.replace(quick_handlers, new_handlers, 1)
    else:
        raise SystemExit('Coaching handler patch point not found')
    js_path.write_text(js, encoding='utf-8')

css = css_path.read_text(encoding='utf-8')
if CSS_MARK not in css:
    css += r'''

/* GENESIS_COACHING_COURSE_COPY_V1 */
.side-actions{display:grid;gap:8px;margin:0 0 12px}.sidebar-action{width:100%;min-height:42px;text-align:left;padding:9px 12px}.sidebar-action.primary{font-weight:800}.course-copy-shell{min-height:100%;width:100%}.course-copy-head{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;padding:20px 22px;margin-bottom:14px;border:1px solid #34486f;border-radius:18px;background:linear-gradient(120deg,#172744,#101b32 65%,#211b3f)}.course-copy-head h1{margin:5px 0 6px;font-size:25px}.course-copy-head p{margin:0;max-width:760px;color:var(--muted);line-height:1.55;font-size:12px}.course-copy-badge{white-space:nowrap;border:1px solid #6554a1;border-radius:999px;padding:7px 10px;background:#46357866;color:#c7b9ff;font-size:10px;font-weight:800;letter-spacing:.5px}.course-copy-loading,.course-copy-empty{display:grid;place-items:center;min-height:150px;color:var(--muted);font-size:12px;text-align:center;padding:18px}.course-copy-grid{display:grid;grid-template-columns:minmax(220px,.9fr) minmax(280px,1.1fr) minmax(220px,.9fr);gap:10px;min-height:520px}.course-copy-pane{min-width:0;display:flex;flex-direction:column;border:1px solid var(--line);border-radius:15px;overflow:hidden;background:#0c172a}.course-copy-pane>header{display:flex;justify-content:space-between;align-items:center;gap:8px;min-height:58px;padding:11px 13px;border-bottom:1px solid var(--line);background:#111f37}.course-copy-pane>header b{font-size:13px}.course-copy-pane>header small{color:var(--muted);font-size:10px;max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.course-copy-scroll{overflow:auto;flex:1;min-height:0;padding:8px}.course-copy-row{--course-copy-depth:0;width:100%;display:grid;grid-template-columns:17px 18px minmax(0,1fr);align-items:center;gap:6px;text-align:left;padding:8px 8px 8px calc(8px + var(--course-copy-depth)*15px);margin:0 0 3px;border:1px solid transparent;border-radius:8px;background:transparent;color:var(--text);min-height:36px;font-size:11px}.course-copy-row:hover{background:#172641;border-color:#2f456a}.course-copy-row.on{background:#342863;border-color:#6b56af}.course-copy-twisty{font-size:9px;color:#96a9cd}.course-copy-folder{color:#f0be4f;font-size:13px}.course-copy-question{display:grid;grid-template-columns:34px minmax(0,1fr);gap:9px;align-items:center;padding:9px;border-bottom:1px solid #203250}.course-copy-question>span{width:30px;height:30px;display:grid;place-items:center;border-radius:8px;background:#1c2c49;color:#aebde0;font-size:10px}.course-copy-question b{display:block;font-size:11px}.course-copy-question small{display:block;color:var(--muted);font-size:9px;margin-top:4px}.course-copy-exam{--course-copy-depth:0;display:grid;grid-template-columns:18px minmax(0,1fr) auto;gap:7px;align-items:center;padding:8px 8px 8px calc(28px + var(--course-copy-depth)*15px);font-size:10px;color:#d5def2}.course-copy-exam small{color:var(--muted);font-size:9px}.side-heading{display:none!important}
@media(max-width:1050px){.course-copy-grid{grid-template-columns:1fr;min-height:0}.course-copy-pane{min-height:260px}.course-copy-head{flex-direction:column}.course-copy-badge{align-self:flex-start}}
@media(max-width:700px){.side-actions{grid-template-columns:1fr 1fr}.sidebar-action{text-align:center}.course-copy-head{padding:16px}.course-copy-head h1{font-size:21px}.course-copy-pane{min-height:230px}}
'''
    css_path.write_text(css, encoding='utf-8')

# Final assertions: make accidental coupling or re-run drift fail loudly.
html = html_path.read_text(encoding='utf-8')
js = js_path.read_text(encoding='utf-8')
css = css_path.read_text(encoding='utf-8')
checks = [
    (HTML_MARK in html, 'HTML marker missing'),
    ('<span>ÖĞRENCİLER</span>' not in html, 'Old Öğrenciler heading still present'),
    (html.index('id="studentSearch"') < html.index('id="addStudent"') < html.index('id="addCourseWorkspace"') < html.index('id="studentList"'), 'Sidebar control order is wrong'),
    ('id="courseWorkspace"' in html, 'Course workspace host missing'),
    (JS_MARK in js, 'JS marker missing'),
    ("api('/api/topics')" in js and "api('/api/test-tree')" in js and "/api/questions?topic_id=" in js, 'Read-only course copy API wiring missing'),
    ('addCourseWorkspace:()=>action(openCourseCopy)' in js, 'Ders Ekle handler missing'),
    (CSS_MARK in css, 'CSS marker missing'),
]
for ok,msg in checks:
    if not ok: raise SystemExit(msg)
print('coaching sidebar + independent course copy patch: OK')
