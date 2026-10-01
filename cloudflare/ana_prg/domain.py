"""Pure program and Deneme business rules, ported from source @38."""
import datetime as dt
import hashlib, math, re, unicodedata

COURSES = {
 'TYT_MAT':'TYT Matematik','TYT_GEO':'TYT Geometri','TYT_TURKCE':'TYT Türkçe',
 'TYT_FIZIK':'TYT Fizik','TYT_KIMYA':'TYT Kimya','TYT_BIYOLOJI':'TYT Biyoloji',
 'TYT_TARIH':'TYT Tarih','TYT_COGRAFYA':'TYT Coğrafya','TYT_FELSEFE':'TYT Felsefe','TYT_DIN':'TYT Din',
 'AYT_MAT':'AYT Matematik','AYT_GEO':'AYT Geometri','AYT_FIZIK':'AYT Fizik',
 'AYT_KIMYA':'AYT Kimya','AYT_BIYOLOJI':'AYT Biyoloji','AYT_EDEBIYAT':'AYT Edebiyat',
 'AYT_TARIH1':'AYT Tarih-1','AYT_TARIH2':'AYT Tarih-2','AYT_COGRAFYA1':'AYT Coğrafya-1',
 'AYT_COGRAFYA2':'AYT Coğrafya-2','AYT_FELSEFE':'AYT Felsefe','AYT_DIN':'AYT Din'}
FORMATS = {
 'TYT':dict(label='TYT',subjects=[('TURKCE','Türkçe',40,33),('SOSYAL','Sosyal Bilimler',20,17),
                ('MATEMATIK','Temel Matematik',40,33),('FEN','Fen Bilimleri',20,17)],population=2187743,mean=.31,sd=.15),
 'AYT_SAY':dict(label='AYT Sayısal',subjects=[('MATEMATIK','Matematik',40,30),('FIZIK','Fizik',14,10),
                ('KIMYA','Kimya',13,10),('BIYOLOJI','Biyoloji',13,10)],population=1135718,mean=.16,sd=.14),
 'AYT_SOZ':dict(label='AYT Sözel',subjects=[('EDEBIYAT','Türk Dili ve Edebiyatı',24,18),('TARIH1','Tarih-1',10,7),
                ('COGRAFYA1','Coğrafya-1',6,5),('TARIH2','Tarih-2',11,8),('COGRAFYA2','Coğrafya-2',11,8),
                ('FELSEFE','Felsefe Grubu',12,9),('DIN','DKAB / Ek Felsefe',6,5)],population=1085698,mean=.20,sd=.14)}

def normalize_code(value):
    value=str(value).strip().translate(str.maketrans('ıİğĞşŞöÖüÜçÇ','iIgGsSoOuUcC')).upper()
    return re.sub(r'[^A-Z0-9_-]','',value)[:80]

def monday(value):
    try: d=dt.date.fromisoformat(str(value))
    except ValueError: raise ValueError('Hafta YYYY-MM-DD biçiminde olmalı.')
    if d.weekday()!=0: raise ValueError('Hafta başlangıcı pazartesi olmalı.')
    return d

def validate_key(kind,key,partial=False):
    if kind not in FORMATS: raise ValueError('Geçersiz sınav türü.')
    if not isinstance(key,dict): raise ValueError('Anahtar nesne olmalı.')
    allowed={s[0] for s in FORMATS[kind]['subjects']}
    if set(key)-allowed: raise ValueError('Anahtarda geçersiz ders var.')
    result={}
    for code,label,q,w in FORMATS[kind]['subjects']:
        if partial and code not in key: continue
        answers=key.get(code)
        if not isinstance(answers,list) or len(answers)!=q: raise ValueError(f'{label}: tam {q} cevap gerekir.')
        answers=[str(a).strip().upper() for a in answers]
        if any(a not in 'ABCDE' or len(a)!=1 for a in answers): raise ValueError(f'{label}: geçersiz anahtar cevabı.')
        result[code]=answers
    return result

def validate_answers(kind,answers):
    if kind not in FORMATS or not isinstance(answers,list): raise ValueError('Optik cevap listesi geçersiz.')
    counts={s[0]:s[2] for s in FORMATS[kind]['subjects']}
    if len(answers)!=sum(counts.values()): raise ValueError('Tam optik toplam soru sayısı uyuşmuyor.')
    mapped={}
    for a in answers:
        if not isinstance(a,dict): raise ValueError('Optik soru geçersiz.')
        code=a.get('subject');q=a.get('question_no');answer=str(a.get('answer') or '').strip().upper()
        if code not in counts or type(q) is not int or q<1 or q>counts[code]: raise ValueError('Optik ders/soru numarası geçersiz.')
        if (code,q) in mapped: raise ValueError('Optikte tekrar eden soru var.')
        if answer not in ('A','B','C','D','E',''): raise ValueError('Optik cevabı geçersiz.')
        mapped[code,q]=dict(subject=code,question_no=q,answer=answer)
    return [mapped[code,q] for code in counts for q in range(1,counts[code]+1)]

def cdf(x):
    t=1/(1+.2316419*abs(x));d=.3989423*math.exp(-x*x/2)
    p=1-d*t*(.3193815+t*(-.3565638+t*(1.781478+t*(-1.821256+t*1.330274))))
    return p if x>=0 else 1-p

def percentile(x,mean,sd): return max(.01,min(99.99,100*cdf((x-mean)/sd)))
def jsround(n,d=0):
    p=10**d
    return math.floor(n*p+.5)/p

def cohort(id): return 75000+int.from_bytes(hashlib.sha256(id.encode()).digest()[:4],'big')%175001

def calculate(exam,student,answers,key,confidence=None,previous_tyt=None):
    kind=exam['kind'];cfg=FORMATS[kind];answers=validate_answers(kind,answers);key=validate_key(kind,key)
    by_subject={s[0]:[] for s in cfg['subjects']}
    for a in answers: by_subject[a['subject']].append(a['answer'])
    subjects={};totals=dict(correct=0,wrong=0,blank=0,net=0)
    for code,label,q,w in cfg['subjects']:
        d=y=b=0
        for a,k in zip(by_subject[code],key[code]):
            if not a:b+=1
            elif a==k:d+=1
            else:y+=1
        net=d-y/4
        subjects[code]=dict(label=label,questions=q,correct=d,wrong=y,blank=b,net=net)
        for k,v in zip(('correct','wrong','blank','net'),(d,y,b,net)): totals[k]+=v
    ratio=sum(max(0,min(1,subjects[c]['net']/q))*w for c,l,q,w in cfg['subjects'])/sum(s[3] for s in cfg['subjects'])
    score=jsround(100+400*ratio,3);pct=percentile(ratio,cfg['mean'],cfg['sd']);n=cohort(exam['id'])
    rank=max(1,min(n,math.floor((1-pct/100)*n+.5)+1))
    estimate_score=score;estimate_pct=pct;paired=None
    if kind!='TYT' and previous_tyt:
        tyt_ratio=max(0,min(1,(previous_tyt['demo']['score']-100)/400))
        combined=.4*tyt_ratio+.6*ratio
        estimate_score=jsround(100+400*combined,3)
        estimate_pct=percentile(combined,cfg['mean']*.6+.31*.4,.145)
        paired=previous_tyt['exam']['id']
    confidence=confidence if type(confidence) in (float,int) and 0<=confidence<=1 else None
    return dict(student=dict(id=student['id'],name=student['name']),exam={k:exam[k] for k in ('id','name','kind','date')},
        subjects=subjects,totals=totals,review_required=confidence is None or confidence<.90,confidence=confidence,
        demo=dict(participants=n,score=score,rank=rank,percentile_from_top=jsround(100-pct,3)),
        estimate=dict(reference_population=cfg['population'],score=estimate_score,
            rank=max(1,min(cfg['population'],math.floor((1-estimate_pct/100)*cfg['population']+.5)+1)),
            percentile_from_top=jsround(100-estimate_pct,3),paired_tyt_exam_id=paired,
            note='Kaynak programın 2026 referans parametreleriyle üretilen tahmin; resmi ÖSYM sonucu değildir.'),
        calculation_note='D/Y/B ve Net kodla hesaplanır. Net = D − Y/4. Demo ve 2026 eşdeğeri tahmindir; OBP içermez.')

def ordered_homework(rows):
    def norm(s):
        return ''.join(c for c in unicodedata.normalize('NFD',str(s).lower()) if not unicodedata.combining(c))
    return sorted(rows,key=lambda r:(norm(r.get('source','')),int(r.get('order',0)),int(r.get('test_no',0)),r['id']))

def build_plan(week,rules,homework,existing,previous,skip_past=True,today=None):
    start=monday(week);today=today or dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date()
    used={r.get('homework_id') for r in previous if r.get('auto')}
    plan=[];existing={(x['course'],int(x['day'])):x for x in existing}
    for rule in sorted(rules,key=lambda r:int(r.get('order',0))):
        pool=ordered_homework([h for h in homework if h.get('course')==rule['course'] and h.get('active',True)])
        for day in sorted(set(rule.get('days',list(range(7))))):
            if type(day) is not int or day<0 or day>6: raise ValueError('Program günü 0–6 olmalı.')
            date=start+dt.timedelta(days=day)
            if (rule['course'],day) in existing or (skip_past and date<today): continue
            selected=next((h for h in pool if h['id'] not in used),None)
            if not selected: continue
            used.add(selected['id'])
            plan.append(dict(id='SLOT-'+hashlib.sha256(f'{week}|{rule["course"]}|{day}'.encode()).hexdigest()[:24],
                week=week,course=rule['course'],day=day,date=date.isoformat(),homework_id=selected['id'],auto=True))
    return plan

def event_id(student,homework,date):
    return 'ASN-'+hashlib.sha256(f'{student}|{homework}|{date}'.encode()).hexdigest()[:24]

def item_analysis(kind,key,optics,results):
    key=validate_key(kind,key);items=[]
    scores={r['student_id']:r['report']['totals']['net'] for r in results}
    for code,label,q,w in FORMATS[kind]['subjects']:
        for number in range(1,q+1):
            d=y=b=0;points=[];totals=[];options={c:0 for c in ('A','B','C','D','E','')}
            for o in optics:
                a=next((a['answer'] for a in o.get('answers',[]) if a['subject']==code and a['question_no']==number),'')
                options[a]+=1;points.append(int(a==key[code][number-1]));totals.append(scores.get(o['student_id'],0))
                if not a:b+=1
                elif a==key[code][number-1]:d+=1
                else:y+=1
            n=d+y+b;discrimination=None
            if n>=4:
                mx=sum(points)/n;my=sum(totals)/n
                dx=sum((x-mx)**2 for x in points);dy=sum((x-my)**2 for x in totals)
                discrimination=sum((x-mx)*(y-my) for x,y in zip(points,totals))/math.sqrt(dx*dy) if dx*dy else 0
            items.append(dict(subject=code,question=number,correct=d,wrong=y,blank=b,n=n,p_index=d/n if n else 0,
                discrimination=discrimination,options=options,answer=key[code][number-1]))
    return items

def safe_csv_cell(value):
    s=str(value or '') if value is None else str(value)
    if isinstance(value,str) and re.match(r'^[\s\x00-\x1f]*[=+\-@]',s): s="'"+s
    return s
