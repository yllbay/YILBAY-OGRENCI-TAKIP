from __future__ import annotations

import datetime as dt
import hashlib
import re
import secrets
from pathlib import Path
from typing import Literal, Optional

from fastapi import Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from auth import session_from_token
from db import DATA, connect

VERSION = "1.0.0"
LEVELS = {"KOLAY", "ORTA", "ZOR"}
RESOURCE_KINDS = {"PDF", "TEST", "VIDEO"}
SCOPE_TYPES = {"CLASS", "STUDENT"}
RESOURCE_ROOT = DATA / "CoachingResources"
MAX_PDF_BYTES = 100 * 1024 * 1024

def _row(con, sql, args=()):
    r = con.execute(sql, args).fetchone()
    return dict(r) if r else None

def _rows(con, sql, args=()):
    return [dict(r) for r in con.execute(sql, args)]

def _clean_name(value: str, label: str, max_len: int = 120) -> str:
    text = " ".join(str(value or "").strip().split())
    if len(text) < 1: raise HTTPException(400, f"{label} boş olamaz.")
    if len(text) > max_len: raise HTTPException(400, f"{label} en fazla {max_len} karakter olabilir.")
    return text

def _level(value: Optional[str], allow_none: bool = False) -> Optional[str]:
    if value is None or str(value).strip() == "":
        if allow_none: return None
        raise HTTPException(400, "Düzey seçin: KOLAY, ORTA veya ZOR.")
    level = str(value).strip().upper()
    if level not in LEVELS: raise HTTPException(400, "Düzey KOLAY, ORTA veya ZOR olmalıdır.")
    return level

def _scope(scope_type: str, scope_id: int) -> tuple[str, int]:
    st = str(scope_type or "").strip().upper()
    if st not in SCOPE_TYPES: raise HTTPException(400, "Kapsam CLASS veya STUDENT olmalıdır.")
    try: sid = int(scope_id)
    except Exception: raise HTTPException(400, "Kapsam kimliği geçersiz.")
    if sid <= 0: raise HTTPException(400, "Kapsam kimliği geçersiz.")
    return st, sid

def _ensure_student(con, student_id: int):
    r = _row(con, "SELECT id,name,number,active FROM coaching_students WHERE id=?", (student_id,))
    if not r or not r["active"]: raise HTTPException(404, "Öğrenci bulunamadı.")
    return r

def _ensure_class(con, class_id: int):
    r = _row(con, "SELECT * FROM coach3_classes WHERE id=? AND active=1", (class_id,))
    if not r: raise HTTPException(404, "Sınıf bulunamadı.")
    return r

def _ensure_curriculum_course(con, course_id: int):
    r = _row(con, "SELECT id,name,is_active FROM coaching_curriculum_courses WHERE id=?", (course_id,))
    if not r or not r["is_active"]: raise HTTPException(404, "Ders bulunamadı.")
    return r

def _validate_curriculum_path(con, course_id: int, unit_id: Optional[int], topic_id: Optional[int]):
    _ensure_curriculum_course(con, course_id)
    if unit_id is not None:
        u = _row(con, "SELECT id,course_id,is_active FROM coaching_curriculum_units WHERE id=?", (unit_id,))
        if not u or not u["is_active"] or int(u["course_id"]) != int(course_id):
            raise HTTPException(400, "Ünite seçilen derse ait değil.")
    if topic_id is not None:
        if unit_id is None: raise HTTPException(400, "Alt başlık için ünite seçilmelidir.")
        t = _row(con, "SELECT id,unit_id,is_active FROM coaching_curriculum_topics WHERE id=?", (topic_id,))
        if not t or not t["is_active"] or int(t["unit_id"]) != int(unit_id):
            raise HTTPException(400, "Alt başlık seçilen üniteye ait değil.")

def ensure_schema():
    RESOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS coach3_classes(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          level TEXT NOT NULL DEFAULT 'ORTA' CHECK(level IN ('KOLAY','ORTA','ZOR')),
          active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ux_coach3_class_name_active ON coach3_classes(lower(name)) WHERE active=1;
        CREATE TABLE IF NOT EXISTS coach3_class_students(
          class_id INTEGER NOT NULL REFERENCES coach3_classes(id) ON DELETE CASCADE,
          student_id INTEGER NOT NULL REFERENCES coaching_students(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(class_id,student_id)
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_class_students_student ON coach3_class_students(student_id,class_id);
        CREATE TABLE IF NOT EXISTS coach3_student_levels(
          student_id INTEGER PRIMARY KEY REFERENCES coaching_students(id) ON DELETE CASCADE,
          level TEXT CHECK(level IN ('KOLAY','ORTA','ZOR')),
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS coach3_class_courses(
          class_id INTEGER NOT NULL REFERENCES coach3_classes(id) ON DELETE CASCADE,
          curriculum_course_id INTEGER NOT NULL REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
          coaching_enabled INTEGER NOT NULL DEFAULT 0,
          sort_order INTEGER NOT NULL DEFAULT 0,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(class_id,curriculum_course_id)
        );
        CREATE TABLE IF NOT EXISTS coach3_student_course_overrides(
          student_id INTEGER NOT NULL REFERENCES coaching_students(id) ON DELETE CASCADE,
          curriculum_course_id INTEGER NOT NULL REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
          coaching_enabled INTEGER NOT NULL CHECK(coaching_enabled IN (0,1)),
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(student_id,curriculum_course_id)
        );
        CREATE TABLE IF NOT EXISTS coach3_responsibilities(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          scope_type TEXT NOT NULL CHECK(scope_type IN ('CLASS','STUDENT')),
          scope_id INTEGER NOT NULL,
          curriculum_course_id INTEGER NOT NULL REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
          unit_id INTEGER REFERENCES coaching_curriculum_units(id) ON DELETE RESTRICT,
          topic_id INTEGER REFERENCES coaching_curriculum_topics(id) ON DELETE RESTRICT,
          enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(scope_type,scope_id,curriculum_course_id,unit_id,topic_id)
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_resp_scope ON coach3_responsibilities(scope_type,scope_id,curriculum_course_id);
        CREATE TABLE IF NOT EXISTS coach3_resources(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          kind TEXT NOT NULL CHECK(kind IN ('PDF','TEST','VIDEO')),
          title TEXT NOT NULL,
          difficulty TEXT NOT NULL CHECK(difficulty IN ('KOLAY','ORTA','ZOR')),
          curriculum_course_id INTEGER NOT NULL REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
          unit_id INTEGER REFERENCES coaching_curriculum_units(id) ON DELETE RESTRICT,
          topic_id INTEGER REFERENCES coaching_curriculum_topics(id) ON DELETE RESTRICT,
          stored_path TEXT,
          original_name TEXT,
          sha256 TEXT,
          size_bytes INTEGER,
          exam_id INTEGER REFERENCES exams(id) ON DELETE RESTRICT,
          video_url TEXT,
          active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_resources_path ON coach3_resources(curriculum_course_id,unit_id,topic_id,difficulty,kind,active);
        CREATE UNIQUE INDEX IF NOT EXISTS ux_coach3_pdf_sha ON coach3_resources(sha256) WHERE kind='PDF' AND active=1 AND sha256 IS NOT NULL;
        CREATE TABLE IF NOT EXISTS coach3_homework_assignments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id INTEGER NOT NULL REFERENCES coaching_students(id) ON DELETE CASCADE,
          class_id INTEGER REFERENCES coach3_classes(id) ON DELETE SET NULL,
          resource_id INTEGER NOT NULL REFERENCES coach3_resources(id) ON DELETE RESTRICT,
          plan_date TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PLANNED' CHECK(status IN ('PLANNED','DONE')),
          assignment_source TEXT NOT NULL DEFAULT 'MANUAL' CHECK(assignment_source IN ('MANUAL','AUTO')),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          completed_at TEXT,
          UNIQUE(student_id,resource_id,plan_date)
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_homework_student_day ON coach3_homework_assignments(student_id,plan_date,status);
        """)

class ClassEdit(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    level: Literal["KOLAY", "ORTA", "ZOR"] = "ORTA"

class StudentLevelEdit(BaseModel):
    level: Optional[Literal["KOLAY", "ORTA", "ZOR"]] = None

class ClassStudentsEdit(BaseModel):
    student_ids: list[int] = Field(default_factory=list, max_length=500)

class ClassCoursesEdit(BaseModel):
    course_ids: list[int] = Field(default_factory=list, max_length=100)
    coaching_course_ids: list[int] = Field(default_factory=list, max_length=100)

class StudentCourseOverrideEdit(BaseModel):
    curriculum_course_id: int
    coaching_enabled: bool

class ResponsibilitiesEdit(BaseModel):
    scope_type: Literal["CLASS", "STUDENT"]
    scope_id: int
    curriculum_course_id: int
    unit_ids: list[int] = Field(default_factory=list, max_length=500)
    topic_ids: list[int] = Field(default_factory=list, max_length=2000)

class TestResourceEdit(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    difficulty: Literal["KOLAY", "ORTA", "ZOR"]
    curriculum_course_id: int
    unit_id: Optional[int] = None
    topic_id: Optional[int] = None
    exam_id: int

class VideoResourceEdit(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    difficulty: Literal["KOLAY", "ORTA", "ZOR"] = "ORTA"
    curriculum_course_id: int
    unit_id: Optional[int] = None
    topic_id: Optional[int] = None
    video_url: str = Field(min_length=8, max_length=1000)

class HomeworkEdit(BaseModel):
    student_id: int
    resource_id: int
    plan_date: str
    class_id: Optional[int] = None

def _curriculum_tree(con):
    courses = _rows(con, "SELECT id,name,sort_order FROM coaching_curriculum_courses WHERE is_active=1 ORDER BY sort_order,name,id")
    units = _rows(con, "SELECT id,course_id,name,sort_order FROM coaching_curriculum_units WHERE is_active=1 ORDER BY sort_order,name,id")
    topics = _rows(con, "SELECT id,unit_id,name,sort_order FROM coaching_curriculum_topics WHERE is_active=1 ORDER BY sort_order,name,id")
    topics_by_unit = {}
    for t in topics: topics_by_unit.setdefault(int(t["unit_id"]), []).append(t)
    units_by_course = {}
    for u in units:
        u["topics"] = topics_by_unit.get(int(u["id"]), [])
        units_by_course.setdefault(int(u["course_id"]), []).append(u)
    for c in courses: c["units"] = units_by_course.get(int(c["id"]), [])
    return courses

def _classes(con):
    return _rows(con, """SELECT c.*,
      (SELECT count(*) FROM coach3_class_students cs WHERE cs.class_id=c.id) student_count,
      (SELECT count(*) FROM coach3_class_courses cc WHERE cc.class_id=c.id) course_count,
      (SELECT count(*) FROM coach3_class_courses cc WHERE cc.class_id=c.id AND cc.coaching_enabled=1) coaching_course_count
    FROM coach3_classes c WHERE c.active=1 ORDER BY c.name,c.id""")

def _students(con):
    data = _rows(con, """SELECT s.id,s.name,s.number,s.note,
      (SELECT count(*) FROM coaching_courses c WHERE c.student_id=s.id) legacy_course_count,
      l.level student_level
    FROM coaching_students s LEFT JOIN coach3_student_levels l ON l.student_id=s.id
    WHERE s.active=1 ORDER BY s.name,s.id""")
    memberships = _rows(con, """SELECT cs.student_id,c.id class_id,c.name class_name,c.level class_level
      FROM coach3_class_students cs JOIN coach3_classes c ON c.id=cs.class_id AND c.active=1 ORDER BY c.name,c.id""")
    by_student = {}
    for m in memberships: by_student.setdefault(int(m["student_id"]), []).append({k: m[k] for k in ("class_id","class_name","class_level")})
    for s in data:
        s["classes"] = by_student.get(int(s["id"]), [])
        s["effective_level"] = s["student_level"] or (s["classes"][0]["class_level"] if s["classes"] else "ORTA")
    return data

def _validate_scope_exists(con, scope_type: str, scope_id: int):
    _ensure_class(con, scope_id) if scope_type == "CLASS" else _ensure_student(con, scope_id)

def _effective_student(con, student_id: int):
    student = _ensure_student(con, student_id)
    classes = _rows(con, """SELECT c.* FROM coach3_class_students cs JOIN coach3_classes c ON c.id=cs.class_id
      WHERE cs.student_id=? AND c.active=1 ORDER BY c.name,c.id""", (student_id,))
    lvl = _row(con, "SELECT level FROM coach3_student_levels WHERE student_id=?", (student_id,))
    effective_level = (lvl or {}).get("level") or (classes[0]["level"] if classes else "ORTA")
    inherited = {}
    if classes:
        q = ",".join("?" for _ in classes); ids = [c["id"] for c in classes]
        for r in _rows(con, f"SELECT curriculum_course_id,max(coaching_enabled) coaching_enabled FROM coach3_class_courses WHERE class_id IN ({q}) GROUP BY curriculum_course_id", ids):
            inherited[int(r["curriculum_course_id"])] = bool(r["coaching_enabled"])
    for r in _rows(con, "SELECT curriculum_course_id,coaching_enabled FROM coach3_student_course_overrides WHERE student_id=?", (student_id,)):
        inherited[int(r["curriculum_course_id"])] = bool(r["coaching_enabled"])
    coaching_course_ids = sorted([cid for cid, enabled in inherited.items() if enabled])
    scope_rows = []
    for c in classes: scope_rows.extend(_rows(con, "SELECT * FROM coach3_responsibilities WHERE scope_type='CLASS' AND scope_id=?", (c["id"],)))
    scope_rows.extend(_rows(con, "SELECT * FROM coach3_responsibilities WHERE scope_type='STUDENT' AND scope_id=?", (student_id,)))
    effective_resp = {}
    for r in scope_rows:
        key = (int(r["curriculum_course_id"]), r["unit_id"], r["topic_id"])
        if r["scope_type"] == "STUDENT" or key not in effective_resp: effective_resp[key] = bool(r["enabled"])
    responsibilities = [{"curriculum_course_id":k[0],"unit_id":k[1],"topic_id":k[2]} for k,enabled in effective_resp.items() if enabled]
    return {"student":student,"classes":classes,"student_level":(lvl or {}).get("level"),"effective_level":effective_level,
            "coaching_course_ids":coaching_course_ids,"responsibilities":responsibilities}

def _resource_rows(con, course_id=None, unit_id=None, topic_id=None, difficulty=None, kind=None):
    sql = """SELECT r.*,c.name course_name,u.name unit_name,t.name topic_name,e.name exam_name
      FROM coach3_resources r JOIN coaching_curriculum_courses c ON c.id=r.curriculum_course_id
      LEFT JOIN coaching_curriculum_units u ON u.id=r.unit_id
      LEFT JOIN coaching_curriculum_topics t ON t.id=r.topic_id
      LEFT JOIN exams e ON e.id=r.exam_id WHERE r.active=1"""
    args=[]
    if course_id is not None: sql+=" AND r.curriculum_course_id=?"; args.append(course_id)
    if unit_id is not None: sql+=" AND r.unit_id=?"; args.append(unit_id)
    if topic_id is not None: sql+=" AND r.topic_id=?"; args.append(topic_id)
    if difficulty: sql+=" AND r.difficulty=?"; args.append(_level(difficulty))
    if kind:
        k=str(kind).upper()
        if k not in RESOURCE_KINDS: raise HTTPException(400,"İçerik türü geçersiz.")
        sql+=" AND r.kind=?"; args.append(k)
    sql+=" ORDER BY c.name,u.name,t.name,r.kind,r.title,r.id"
    return _rows(con,sql,args)

def _owner(request: Request):
    session = getattr(request.state,"genesis_session",None) or session_from_token(request.cookies.get("genesis_session"))
    if not session or session.get("role") not in ("ADMIN","INSTITUTION"):
        raise HTTPException(403,"Koçluk alanı için GENESIS oturumu gerekli.")
    return True

def install_coaching_data_model_v1(app):
    if getattr(app.state,"coaching_data_model_v1_installed",False): return {"version":VERSION}
    ensure_schema()

    @app.get("/api/coaching/v3/model")
    def model(_:bool=Depends(_owner)):
        with connect() as con:
            return {"ok":True,"version":VERSION,"classes":_classes(con),"students":_students(con),"curriculum":_curriculum_tree(con),
                    "resource_count":int(_row(con,"SELECT count(*) n FROM coach3_resources WHERE active=1")["n"])}

    @app.post("/api/coaching/v3/classes")
    def create_class(body:ClassEdit,_:bool=Depends(_owner)):
        name=_clean_name(body.name,"Sınıf adı")
        with connect() as con:
            try: cur=con.execute("INSERT INTO coach3_classes(name,level) VALUES(?,?)",(name,_level(body.level)))
            except Exception as exc:
                if "UNIQUE" in str(exc).upper(): raise HTTPException(409,"Bu sınıf zaten mevcut.")
                raise
            return _row(con,"SELECT * FROM coach3_classes WHERE id=?",(cur.lastrowid,))

    @app.put("/api/coaching/v3/classes/{class_id}")
    def update_class(class_id:int,body:ClassEdit,_:bool=Depends(_owner)):
        with connect() as con:
            _ensure_class(con,class_id)
            try: con.execute("UPDATE coach3_classes SET name=?,level=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            (_clean_name(body.name,"Sınıf adı"),_level(body.level),class_id))
            except Exception as exc:
                if "UNIQUE" in str(exc).upper(): raise HTTPException(409,"Bu sınıf adı zaten kullanılıyor.")
                raise
            return _row(con,"SELECT * FROM coach3_classes WHERE id=?",(class_id,))

    @app.delete("/api/coaching/v3/classes/{class_id}")
    def deactivate_class(class_id:int,_:bool=Depends(_owner)):
        with connect() as con:
            _ensure_class(con,class_id); con.execute("UPDATE coach3_classes SET active=0,updated_at=CURRENT_TIMESTAMP WHERE id=?",(class_id,))
            return {"ok":True}

    @app.put("/api/coaching/v3/classes/{class_id}/students")
    def replace_class_students(class_id:int,body:ClassStudentsEdit,_:bool=Depends(_owner)):
        ids=sorted(set(int(x) for x in body.student_ids))
        with connect() as con:
            _ensure_class(con,class_id)
            for sid in ids: _ensure_student(con,sid)
            con.execute("DELETE FROM coach3_class_students WHERE class_id=?",(class_id,))
            con.executemany("INSERT INTO coach3_class_students(class_id,student_id) VALUES(?,?)",[(class_id,sid) for sid in ids])
            return {"ok":True,"class_id":class_id,"student_ids":ids}

    @app.put("/api/coaching/v3/students/{student_id}/level")
    def set_student_level(student_id:int,body:StudentLevelEdit,_:bool=Depends(_owner)):
        with connect() as con:
            _ensure_student(con,student_id)
            if body.level is None:
                con.execute("DELETE FROM coach3_student_levels WHERE student_id=?",(student_id,))
                return {"ok":True,"student_id":student_id,"level":None}
            level=_level(body.level)
            con.execute("""INSERT INTO coach3_student_levels(student_id,level) VALUES(?,?)
              ON CONFLICT(student_id) DO UPDATE SET level=excluded.level,updated_at=CURRENT_TIMESTAMP""",(student_id,level))
            return {"ok":True,"student_id":student_id,"level":level}

    @app.put("/api/coaching/v3/classes/{class_id}/courses")
    def replace_class_courses(class_id:int,body:ClassCoursesEdit,_:bool=Depends(_owner)):
        course_ids=sorted(set(int(x) for x in body.course_ids)); coaching_ids=set(int(x) for x in body.coaching_course_ids)
        if not coaching_ids.issubset(set(course_ids)): raise HTTPException(400,"Koçluk dersi önce sınıf dersi olarak seçilmelidir.")
        with connect() as con:
            _ensure_class(con,class_id)
            for cid in course_ids: _ensure_curriculum_course(con,cid)
            con.execute("DELETE FROM coach3_class_courses WHERE class_id=?",(class_id,))
            con.executemany("INSERT INTO coach3_class_courses(class_id,curriculum_course_id,coaching_enabled,sort_order) VALUES(?,?,?,?)",
                            [(class_id,cid,1 if cid in coaching_ids else 0,pos) for pos,cid in enumerate(course_ids)])
            return {"ok":True,"class_id":class_id,"course_ids":course_ids,"coaching_course_ids":sorted(coaching_ids)}

    @app.put("/api/coaching/v3/students/{student_id}/course-override")
    def set_course_override(student_id:int,body:StudentCourseOverrideEdit,_:bool=Depends(_owner)):
        with connect() as con:
            _ensure_student(con,student_id); _ensure_curriculum_course(con,body.curriculum_course_id)
            con.execute("""INSERT INTO coach3_student_course_overrides(student_id,curriculum_course_id,coaching_enabled)
              VALUES(?,?,?) ON CONFLICT(student_id,curriculum_course_id) DO UPDATE SET
              coaching_enabled=excluded.coaching_enabled,updated_at=CURRENT_TIMESTAMP""",
              (student_id,body.curriculum_course_id,1 if body.coaching_enabled else 0))
            return {"ok":True}

    @app.delete("/api/coaching/v3/students/{student_id}/course-override/{course_id}")
    def delete_course_override(student_id:int,course_id:int,_:bool=Depends(_owner)):
        with connect() as con:
            _ensure_student(con,student_id)
            con.execute("DELETE FROM coach3_student_course_overrides WHERE student_id=? AND curriculum_course_id=?",(student_id,course_id))
            return {"ok":True}

    @app.put("/api/coaching/v3/responsibilities")
    def replace_responsibilities(body:ResponsibilitiesEdit,_:bool=Depends(_owner)):
        st,sid=_scope(body.scope_type,body.scope_id)
        with connect() as con:
            _validate_scope_exists(con,st,sid); _ensure_curriculum_course(con,body.curriculum_course_id)
            units=sorted(set(int(x) for x in body.unit_ids)); topics=sorted(set(int(x) for x in body.topic_ids))
            for uid in units: _validate_curriculum_path(con,body.curriculum_course_id,uid,None)
            topic_rows=[]
            for tid in topics:
                t=_row(con,"""SELECT t.id,t.unit_id,u.course_id FROM coaching_curriculum_topics t
                    JOIN coaching_curriculum_units u ON u.id=t.unit_id WHERE t.id=? AND t.is_active=1 AND u.is_active=1""",(tid,))
                if not t or int(t["course_id"])!=int(body.curriculum_course_id): raise HTTPException(400,"Alt başlık seçilen derse ait değil.")
                topic_rows.append((tid,int(t["unit_id"])))
            con.execute("DELETE FROM coach3_responsibilities WHERE scope_type=? AND scope_id=? AND curriculum_course_id=?",(st,sid,body.curriculum_course_id))
            for uid in units:
                con.execute("INSERT INTO coach3_responsibilities(scope_type,scope_id,curriculum_course_id,unit_id,topic_id,enabled) VALUES(?,?,?,?,NULL,1)",
                            (st,sid,body.curriculum_course_id,uid))
            for tid,uid in topic_rows:
                con.execute("INSERT INTO coach3_responsibilities(scope_type,scope_id,curriculum_course_id,unit_id,topic_id,enabled) VALUES(?,?,?,?,?,1)",
                            (st,sid,body.curriculum_course_id,uid,tid))
            return {"ok":True,"scope_type":st,"scope_id":sid,"curriculum_course_id":body.curriculum_course_id,"unit_ids":units,"topic_ids":topics}

    @app.get("/api/coaching/v3/students/{student_id}/effective")
    def effective(student_id:int,_:bool=Depends(_owner)):
        with connect() as con:
            out=_effective_student(con,student_id); allowed=set(out["coaching_course_ids"])
            out["resources"]=[r for r in _resource_rows(con,difficulty=out["effective_level"]) if int(r["curriculum_course_id"]) in allowed]
            return out

    @app.get("/api/coaching/v3/resources")
    def list_resources(course_id:Optional[int]=None,unit_id:Optional[int]=None,topic_id:Optional[int]=None,
                       difficulty:Optional[str]=None,kind:Optional[str]=None,_:bool=Depends(_owner)):
        with connect() as con: return {"resources":_resource_rows(con,course_id,unit_id,topic_id,difficulty,kind)}

    @app.post("/api/coaching/v3/resources/pdf")
    async def upload_pdf(file:UploadFile=File(...),title:str=Form(""),difficulty:str=Form(...),
                         curriculum_course_id:int=Form(...),unit_id:Optional[int]=Form(None),
                         topic_id:Optional[int]=Form(None),_:bool=Depends(_owner)):
        name=_clean_name(title or file.filename or "PDF","İçerik adı",180); level=_level(difficulty)
        original=Path(file.filename or "document.pdf").name
        if not original.lower().endswith(".pdf"): raise HTTPException(400,"Yalnız PDF dosyası yüklenebilir.")
        with connect() as con: _validate_curriculum_path(con,curriculum_course_id,unit_id,topic_id)
        tmp=RESOURCE_ROOT/("upload-"+secrets.token_hex(16)+".tmp"); digest=hashlib.sha256(); size=0
        try:
            with tmp.open("wb") as out:
                while True:
                    chunk=await file.read(1024*1024)
                    if not chunk: break
                    size+=len(chunk)
                    if size>MAX_PDF_BYTES: raise HTTPException(413,"PDF en fazla 100 MB olabilir.")
                    digest.update(chunk); out.write(chunk)
            with tmp.open("rb") as fh:
                if fh.read(5)!=b"%PDF-": raise HTTPException(400,"Dosya geçerli bir PDF değil.")
            sha=digest.hexdigest()
            with connect() as con:
                if _row(con,"SELECT id FROM coach3_resources WHERE kind='PDF' AND sha256=? AND active=1",(sha,)):
                    raise HTTPException(409,"Bu PDF daha önce yüklenmiş.")
                cur=con.execute("""INSERT INTO coach3_resources(kind,title,difficulty,curriculum_course_id,unit_id,topic_id,original_name,sha256,size_bytes)
                    VALUES('PDF',?,?,?,?,?,?,?,?)""",(name,level,curriculum_course_id,unit_id,topic_id,original,sha,size))
                rid=int(cur.lastrowid); final=RESOURCE_ROOT/f"{rid:08d}-{sha[:12]}.pdf"; tmp.replace(final)
                con.execute("UPDATE coach3_resources SET stored_path=? WHERE id=?",(str(final),rid))
                return _row(con,"SELECT * FROM coach3_resources WHERE id=?",(rid,))
        finally:
            try: await file.close()
            except Exception: pass
            if tmp.exists(): tmp.unlink(missing_ok=True)

    @app.post("/api/coaching/v3/resources/test")
    def add_test_resource(body:TestResourceEdit,_:bool=Depends(_owner)):
        with connect() as con:
            _validate_curriculum_path(con,body.curriculum_course_id,body.unit_id,body.topic_id)
            if not _row(con,"SELECT id FROM exams WHERE id=?",(body.exam_id,)): raise HTTPException(404,"Test bulunamadı.")
            cur=con.execute("""INSERT INTO coach3_resources(kind,title,difficulty,curriculum_course_id,unit_id,topic_id,exam_id)
              VALUES('TEST',?,?,?,?,?,?)""",(_clean_name(body.title,"İçerik adı",180),_level(body.difficulty),
              body.curriculum_course_id,body.unit_id,body.topic_id,body.exam_id))
            return _row(con,"SELECT * FROM coach3_resources WHERE id=?",(cur.lastrowid,))

    @app.post("/api/coaching/v3/resources/video")
    def add_video_resource(body:VideoResourceEdit,_:bool=Depends(_owner)):
        url=body.video_url.strip()
        if not re.match(r"^https?://",url,flags=re.I): raise HTTPException(400,"Video adresi http:// veya https:// ile başlamalıdır.")
        with connect() as con:
            _validate_curriculum_path(con,body.curriculum_course_id,body.unit_id,body.topic_id)
            cur=con.execute("""INSERT INTO coach3_resources(kind,title,difficulty,curriculum_course_id,unit_id,topic_id,video_url)
              VALUES('VIDEO',?,?,?,?,?,?)""",(_clean_name(body.title,"İçerik adı",180),_level(body.difficulty),
              body.curriculum_course_id,body.unit_id,body.topic_id,url))
            return _row(con,"SELECT * FROM coach3_resources WHERE id=?",(cur.lastrowid,))

    @app.delete("/api/coaching/v3/resources/{resource_id}")
    def deactivate_resource(resource_id:int,_:bool=Depends(_owner)):
        with connect() as con:
            if not _row(con,"SELECT id FROM coach3_resources WHERE id=? AND active=1",(resource_id,)): raise HTTPException(404,"İçerik bulunamadı.")
            con.execute("UPDATE coach3_resources SET active=0,updated_at=CURRENT_TIMESTAMP WHERE id=?",(resource_id,))
            return {"ok":True}

    @app.get("/api/coaching/v3/resources/{resource_id}/pdf")
    def resource_pdf(resource_id:int,_:bool=Depends(_owner)):
        with connect() as con: r=_row(con,"SELECT * FROM coach3_resources WHERE id=? AND active=1 AND kind='PDF'",(resource_id,))
        if not r or not r.get("stored_path"): raise HTTPException(404,"PDF bulunamadı.")
        path=Path(r["stored_path"])
        if not path.is_file(): raise HTTPException(404,"PDF dosyası depolamada bulunamadı.")
        return FileResponse(path,media_type="application/pdf",filename=r.get("original_name") or path.name)

    @app.post("/api/coaching/v3/homework")
    def assign_homework(body:HomeworkEdit,_:bool=Depends(_owner)):
        try: day=dt.date.fromisoformat(body.plan_date)
        except Exception: raise HTTPException(400,"Ödev tarihi geçersiz.")
        with connect() as con:
            _ensure_student(con,body.student_id)
            if body.class_id is not None:
                _ensure_class(con,body.class_id)
                if not _row(con,"SELECT 1 ok FROM coach3_class_students WHERE class_id=? AND student_id=?",(body.class_id,body.student_id)):
                    raise HTTPException(400,"Öğrenci seçilen sınıfta değil.")
            if not _row(con,"SELECT id FROM coach3_resources WHERE id=? AND active=1",(body.resource_id,)): raise HTTPException(404,"İçerik bulunamadı.")
            try:
                cur=con.execute("""INSERT INTO coach3_homework_assignments(student_id,class_id,resource_id,plan_date,assignment_source)
                  VALUES(?,?,?,?, 'MANUAL')""",(body.student_id,body.class_id,body.resource_id,day.isoformat()))
            except Exception as exc:
                if "UNIQUE" in str(exc).upper(): raise HTTPException(409,"Bu içerik aynı gün için zaten atanmış.")
                raise
            return _row(con,"SELECT * FROM coach3_homework_assignments WHERE id=?",(cur.lastrowid,))

    @app.get("/api/coaching/v3/students/{student_id}/homework")
    def student_homework(student_id:int,week_start:Optional[str]=None,_:bool=Depends(_owner)):
        with connect() as con:
            _ensure_student(con,student_id)
            if week_start:
                try: start=dt.date.fromisoformat(week_start)
                except Exception: raise HTTPException(400,"Hafta başlangıcı geçersiz.")
            else:
                now=dt.date.today(); start=now-dt.timedelta(days=now.weekday())
            end=start+dt.timedelta(days=6)
            data=_rows(con,"""SELECT h.*,r.kind,r.title,r.difficulty,r.curriculum_course_id,r.unit_id,r.topic_id,
                c.name course_name,u.name unit_name,t.name topic_name
              FROM coach3_homework_assignments h JOIN coach3_resources r ON r.id=h.resource_id
              JOIN coaching_curriculum_courses c ON c.id=r.curriculum_course_id
              LEFT JOIN coaching_curriculum_units u ON u.id=r.unit_id
              LEFT JOIN coaching_curriculum_topics t ON t.id=r.topic_id
              WHERE h.student_id=? AND h.plan_date BETWEEN ? AND ? ORDER BY h.plan_date,h.id""",
              (student_id,start.isoformat(),end.isoformat()))
            return {"student_id":student_id,"week_start":start.isoformat(),"week_end":end.isoformat(),"homework":data}

    app.state.coaching_data_model_v1_installed=True
    return {"version":VERSION}
