from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Literal, Optional

from fastapi import File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from db import CURRENT_DB, DB, connect
from curriculum_step1 import _ensure_schema as _ensure_curriculum_schema

VERSION = "0.16.0"
LEVELS = {"EASY", "MEDIUM", "HARD"}


def _rows(con, sql, args=()):
    return [dict(r) for r in con.execute(sql, args)]


def _row(con, sql, args=()):
    r = con.execute(sql, args).fetchone()
    return dict(r) if r else None


def _clean(value, label, max_len=160):
    x = " ".join(str(value or "").strip().split())
    if not x:
        raise HTTPException(400, f"{label} boş olamaz.")
    if len(x) > max_len:
        raise HTTPException(400, f"{label} en fazla {max_len} karakter olabilir.")
    return x


def _level(value):
    x = str(value or "").strip().upper()
    if x not in LEVELS:
        raise HTTPException(400, "Düzey EASY, MEDIUM veya HARD olmalıdır.")
    return x


def _storage_root():
    db_path = Path(CURRENT_DB.get() or DB)
    root = db_path.parent / "CoachingResources"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _require_admin_session(request: Request):
    session = getattr(request.state, "genesis_session", None)
    if not session:
        raise HTTPException(401, "GENESIS oturumu gerekli.")
    role = str(session.get("role") or "")
    if role not in {"ADMIN", "INSTITUTION"}:
        raise HTTPException(403, "Koçluk yönetim yetkisi gerekli.")
    return session


def ensure_schema():
    # V3 depends on the canonical Step-1 curriculum tables. The Step-1 module
    # creates them lazily on first curriculum request, so ensure them here too
    # before creating/querying V3 foreign-key tables.
    _ensure_curriculum_schema()
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS coach3_classes(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          name_key TEXT NOT NULL UNIQUE,
          grade_label TEXT NOT NULL DEFAULT '',
          difficulty_level TEXT NOT NULL CHECK(difficulty_level IN ('EASY','MEDIUM','HARD')),
          note TEXT NOT NULL DEFAULT '',
          active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS coach3_student_class(
          student_id INTEGER PRIMARY KEY REFERENCES coaching_students(id) ON DELETE CASCADE,
          class_id INTEGER NOT NULL REFERENCES coach3_classes(id) ON DELETE RESTRICT,
          assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_student_class_class ON coach3_student_class(class_id,student_id);
        CREATE TABLE IF NOT EXISTS coach3_student_profiles(
          student_id INTEGER PRIMARY KEY REFERENCES coaching_students(id) ON DELETE CASCADE,
          difficulty_override TEXT CHECK(difficulty_override IS NULL OR difficulty_override IN ('EASY','MEDIUM','HARD')),
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS coach3_course_assignments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          scope_type TEXT NOT NULL CHECK(scope_type IN ('CLASS','STUDENT')),
          scope_id INTEGER NOT NULL,
          curriculum_course_id INTEGER NOT NULL REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
          weekly_sessions INTEGER NOT NULL DEFAULT 3 CHECK(weekly_sessions BETWEEN 1 AND 14),
          minutes INTEGER NOT NULL DEFAULT 60 CHECK(minutes BETWEEN 10 AND 300),
          daily_exam INTEGER NOT NULL DEFAULT 1,
          active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(scope_type,scope_id,curriculum_course_id)
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_course_scope ON coach3_course_assignments(scope_type,scope_id,active);
        CREATE TABLE IF NOT EXISTS coach3_responsibilities(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          scope_type TEXT NOT NULL CHECK(scope_type IN ('CLASS','STUDENT')),
          scope_id INTEGER NOT NULL,
          curriculum_course_id INTEGER NOT NULL REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
          unit_id INTEGER NOT NULL DEFAULT 0,
          topic_id INTEGER NOT NULL DEFAULT 0,
          active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(scope_type,scope_id,curriculum_course_id,unit_id,topic_id)
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_resp_scope ON coach3_responsibilities(scope_type,scope_id,active);
        CREATE TABLE IF NOT EXISTS coach3_resources(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          curriculum_course_id INTEGER NOT NULL REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
          unit_id INTEGER NOT NULL DEFAULT 0,
          topic_id INTEGER NOT NULL DEFAULT 0,
          title TEXT NOT NULL,
          kind TEXT NOT NULL CHECK(kind IN ('PDF','TEST','VIDEO')),
          difficulty TEXT NOT NULL CHECK(difficulty IN ('EASY','MEDIUM','HARD')),
          estimated_minutes INTEGER NOT NULL DEFAULT 60 CHECK(estimated_minutes BETWEEN 5 AND 600),
          source_kind TEXT NOT NULL DEFAULT 'UPLOAD',
          stored_path TEXT NOT NULL DEFAULT '',
          original_name TEXT NOT NULL DEFAULT '',
          sha256 TEXT NOT NULL DEFAULT '',
          exam_id INTEGER,
          url TEXT NOT NULL DEFAULT '',
          active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_resources_lookup
          ON coach3_resources(curriculum_course_id,unit_id,topic_id,difficulty,active);
        CREATE TABLE IF NOT EXISTS coach3_homework_assignments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id INTEGER NOT NULL REFERENCES coaching_students(id) ON DELETE CASCADE,
          class_id INTEGER REFERENCES coach3_classes(id) ON DELETE SET NULL,
          resource_id INTEGER NOT NULL REFERENCES coach3_resources(id) ON DELETE RESTRICT,
          curriculum_course_id INTEGER NOT NULL REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
          unit_id INTEGER NOT NULL DEFAULT 0,
          topic_id INTEGER NOT NULL DEFAULT 0,
          week_start TEXT NOT NULL,
          plan_date TEXT NOT NULL,
          slot_no INTEGER NOT NULL DEFAULT 1,
          minutes INTEGER NOT NULL DEFAULT 60,
          assigned_level TEXT NOT NULL CHECK(assigned_level IN ('EASY','MEDIUM','HARD')),
          source TEXT NOT NULL DEFAULT 'AUTO',
          status TEXT NOT NULL DEFAULT 'PLANNED' CHECK(status IN ('PLANNED','DONE')),
          completed_at TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(student_id,week_start,resource_id)
        );
        CREATE INDEX IF NOT EXISTS ix_coach3_homework_student_week
          ON coach3_homework_assignments(student_id,week_start,plan_date,status);
        """)


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    grade_label: str = Field(default="", max_length=80)
    difficulty_level: Literal["EASY", "MEDIUM", "HARD"]
    note: str = Field(default="", max_length=1000)


class ClassEdit(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    grade_label: Optional[str] = Field(default=None, max_length=80)
    difficulty_level: Optional[Literal["EASY", "MEDIUM", "HARD"]] = None
    note: Optional[str] = Field(default=None, max_length=1000)
    active: Optional[bool] = None


class StudentCreateV3(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    number: str = Field(default="", max_length=60)
    note: str = Field(default="", max_length=1000)
    class_id: Optional[int] = None
    difficulty_override: Optional[Literal["EASY", "MEDIUM", "HARD"]] = None


class StudentClassEdit(BaseModel):
    class_id: Optional[int] = None
    difficulty_override: Optional[Literal["EASY", "MEDIUM", "HARD"]] = None


class CourseAssignmentEdit(BaseModel):
    curriculum_course_id: int
    weekly_sessions: int = Field(default=3, ge=1, le=14)
    minutes: int = Field(default=60, ge=10, le=300)
    daily_exam: bool = True
    active: bool = True


class ResponsibilitySet(BaseModel):
    curriculum_course_id: int
    selections: list[dict] = Field(default_factory=list, max_length=1000)


class ResourceLink(BaseModel):
    curriculum_course_id: int
    unit_id: int = 0
    topic_id: int = 0
    title: str = Field(min_length=1, max_length=200)
    kind: Literal["TEST", "VIDEO"]
    difficulty: Literal["EASY", "MEDIUM", "HARD"]
    estimated_minutes: int = Field(default=60, ge=5, le=600)
    exam_id: Optional[int] = None
    url: str = Field(default="", max_length=2000)


class HomeworkGenerate(BaseModel):
    week_start: Optional[str] = None
    replace_unfinished: bool = False


class HomeworkStatus(BaseModel):
    status: Literal["PLANNED", "DONE"]


def _require_class(con, cid):
    c = _row(con, "SELECT * FROM coach3_classes WHERE id=? AND active=1", (cid,))
    if not c:
        raise HTTPException(404, "Sınıf bulunamadı.")
    return c


def _require_student(con, sid):
    s = _row(con, "SELECT * FROM coaching_students WHERE id=? AND active=1", (sid,))
    if not s:
        raise HTTPException(404, "Öğrenci bulunamadı.")
    return s


def _require_curriculum_course(con, course_id):
    c = _row(con, "SELECT * FROM coaching_curriculum_courses WHERE id=? AND is_active=1", (course_id,))
    if not c:
        raise HTTPException(404, "Müfredat dersi bulunamadı.")
    return c


def _validate_curriculum_path(con, course_id, unit_id=0, topic_id=0):
    course = _require_curriculum_course(con, course_id)
    unit = topic = None
    if unit_id:
        unit = _row(con, "SELECT * FROM coaching_curriculum_units WHERE id=? AND course_id=? AND is_active=1", (unit_id, course_id))
        if not unit:
            raise HTTPException(400, "Ünite seçilen derse ait değil.")
    if topic_id:
        if not unit_id:
            raise HTTPException(400, "Alt başlık için ünite seçilmelidir.")
        topic = _row(con, "SELECT * FROM coaching_curriculum_topics WHERE id=? AND unit_id=? AND is_active=1", (topic_id, unit_id))
        if not topic:
            raise HTTPException(400, "Alt başlık seçilen üniteye ait değil.")
    return course, unit, topic


def _class_for_student(con, sid):
    return _row(con, """SELECT c.* FROM coach3_student_class m JOIN coach3_classes c ON c.id=m.class_id
        WHERE m.student_id=? AND c.active=1""", (sid,))


def _student_override(con, sid):
    r = _row(con, "SELECT difficulty_override FROM coach3_student_profiles WHERE student_id=?", (sid,))
    return r["difficulty_override"] if r else None


def _effective_level(con, sid):
    override = _student_override(con, sid)
    if override:
        return override
    c = _class_for_student(con, sid)
    return c["difficulty_level"] if c else None


def _scope_exists(con, scope_type, scope_id):
    if scope_type == "CLASS":
        _require_class(con, scope_id)
    elif scope_type == "STUDENT":
        _require_student(con, scope_id)
    else:
        raise HTTPException(400, "Geçersiz sorumluluk kapsamı.")


def _curriculum_tree(con):
    courses = _rows(con, "SELECT id,name,sort_order FROM coaching_curriculum_courses WHERE is_active=1 ORDER BY sort_order,name,id")
    units = _rows(con, "SELECT id,course_id,name,sort_order FROM coaching_curriculum_units WHERE is_active=1 ORDER BY sort_order,name,id")
    topics = _rows(con, "SELECT id,unit_id,name,sort_order FROM coaching_curriculum_topics WHERE is_active=1 ORDER BY sort_order,name,id")
    tmap = {}
    for t in topics:
        tmap.setdefault(t["unit_id"], []).append(t)
    umap = {}
    for u in units:
        u["topics"] = tmap.get(u["id"], [])
        umap.setdefault(u["course_id"], []).append(u)
    for c in courses:
        c["units"] = umap.get(c["id"], [])
    return courses


def _effective_courses(con, sid):
    cls = _class_for_student(con, sid)
    result = {}
    if cls:
        for x in _rows(con, """SELECT a.*,c.name curriculum_course_name FROM coach3_course_assignments a
            JOIN coaching_curriculum_courses c ON c.id=a.curriculum_course_id
            WHERE a.scope_type='CLASS' AND a.scope_id=? AND a.active=1 AND c.is_active=1
            ORDER BY c.sort_order,c.name""", (cls["id"],)):
            x["inherited_from"] = "CLASS"
            result[x["curriculum_course_id"]] = x
    for x in _rows(con, """SELECT a.*,c.name curriculum_course_name FROM coach3_course_assignments a
        JOIN coaching_curriculum_courses c ON c.id=a.curriculum_course_id
        WHERE a.scope_type='STUDENT' AND a.scope_id=? AND a.active=1 AND c.is_active=1
        ORDER BY c.sort_order,c.name""", (sid,)):
        x["inherited_from"] = "STUDENT"
        result[x["curriculum_course_id"]] = x
    return list(result.values())


def _effective_responsibilities(con, sid):
    cls = _class_for_student(con, sid)
    seen = set()
    out = []
    scopes = []
    if cls:
        scopes.append(("CLASS", cls["id"]))
    scopes.append(("STUDENT", sid))
    for scope_type, scope_id in scopes:
        for x in _rows(con, """SELECT r.*,c.name course_name,u.name unit_name,t.name topic_name
            FROM coach3_responsibilities r
            JOIN coaching_curriculum_courses c ON c.id=r.curriculum_course_id
            LEFT JOIN coaching_curriculum_units u ON u.id=NULLIF(r.unit_id,0)
            LEFT JOIN coaching_curriculum_topics t ON t.id=NULLIF(r.topic_id,0)
            WHERE r.scope_type=? AND r.scope_id=? AND r.active=1
            ORDER BY c.sort_order,c.name,u.sort_order,u.name,t.sort_order,t.name""", (scope_type, scope_id)):
            key = (x["curriculum_course_id"], x["unit_id"], x["topic_id"])
            if key in seen:
                continue
            seen.add(key)
            x["inherited_from"] = scope_type
            out.append(x)
    return out


def _resource_matches(resp, resource):
    if resp["curriculum_course_id"] != resource["curriculum_course_id"]:
        return False
    if resp["topic_id"]:
        return resp["topic_id"] == resource["topic_id"]
    if resp["unit_id"]:
        return resp["unit_id"] == resource["unit_id"]
    return True


def _week_start(value):
    try:
        d = dt.date.fromisoformat(value) if value else dt.date.today()
    except Exception:
        raise HTTPException(400, "Hafta tarihi geçersiz.")
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def _homework_for_week(con, sid, week):
    return _rows(con, """SELECT h.*,r.title resource_title,r.kind resource_kind,r.difficulty,
        c.name course_name,u.name unit_name,t.name topic_name
        FROM coach3_homework_assignments h
        JOIN coach3_resources r ON r.id=h.resource_id
        JOIN coaching_curriculum_courses c ON c.id=h.curriculum_course_id
        LEFT JOIN coaching_curriculum_units u ON u.id=NULLIF(h.unit_id,0)
        LEFT JOIN coaching_curriculum_topics t ON t.id=NULLIF(h.topic_id,0)
        WHERE h.student_id=? AND h.week_start=? ORDER BY h.plan_date,h.slot_no,h.id""", (sid, week))


def _generate_homework(con, sid, week, replace_unfinished=False):
    student = _require_student(con, sid)
    cls = _class_for_student(con, sid)
    level = _effective_level(con, sid)
    if not level:
        raise HTTPException(409, "Önce öğrenci veya sınıf için Kolay / Orta / Zor düzeyi belirleyin.")
    courses = _effective_courses(con, sid)
    if not courses:
        raise HTTPException(409, "Önce sınıf veya öğrenci için koçluk dersi atayın.")
    responsibilities = _effective_responsibilities(con, sid)
    if not responsibilities:
        raise HTTPException(409, "Önce sınıf veya öğrenci için ünite / alt başlık sorumluluğu seçin.")
    if replace_unfinished:
        con.execute("DELETE FROM coach3_homework_assignments WHERE student_id=? AND week_start=? AND status='PLANNED'", (sid, week))
    existing = _homework_for_week(con, sid, week)
    if existing and not replace_unfinished:
        return {"student": student, "class": cls, "level": level, "week_start": week, "assignments": existing, "created": 0, "warnings": ["Bu hafta için mevcut otomatik ödevler korundu."]}

    cfg = _row(con, "SELECT day_minutes_json,max_sessions FROM coach2_settings WHERE student_id=?", (sid,))
    budgets = json.loads(cfg["day_minutes_json"]) if cfg and cfg.get("day_minutes_json") else [120,120,120,120,120,180,120]
    max_sessions = int(cfg["max_sessions"]) if cfg else 4
    loads = [0] * 7
    counts = [0] * 7
    created = 0
    warnings = []
    recent = {r["resource_id"] for r in _rows(con, "SELECT DISTINCT resource_id FROM coach3_homework_assignments WHERE student_id=? AND week_start<?", (sid, week))}
    resp_by_course = {}
    for r in responsibilities:
        resp_by_course.setdefault(r["curriculum_course_id"], []).append(r)

    for course in courses:
        cid = course["curriculum_course_id"]
        rset = resp_by_course.get(cid, [])
        if not rset:
            warnings.append(course["curriculum_course_name"] + ": sorumluluk seçilmedi.")
            continue
        resources = _rows(con, """SELECT * FROM coach3_resources
            WHERE curriculum_course_id=? AND difficulty=? AND active=1
            ORDER BY id""", (cid, level))
        resources = [r for r in resources if any(_resource_matches(resp, r) for resp in rset)]
        if not resources:
            warnings.append(course["curriculum_course_name"] + f": {level} düzeyinde uygun içerik yok.")
            continue
        resources.sort(key=lambda r: (r["id"] in recent, r["id"]))
        wanted = int(course["weekly_sessions"])
        for i in range(wanted):
            if i >= len(resources):
                warnings.append(course["curriculum_course_name"] + ": içerik sayısı oturum sayısından az; aynı kaynak tekrar edilmedi.")
                break
            resource = resources[i]
            duration = int(resource.get("estimated_minutes") or course["minutes"] or 60)
            eligible = [d for d in range(7) if counts[d] < max_sessions and loads[d] + duration <= budgets[d]]
            if not eligible:
                warnings.append(course["curriculum_course_name"] + ": haftalık kapasite doldu.")
                break
            day = min(eligible, key=lambda d: (loads[d] / max(1, budgets[d]), counts[d], d))
            counts[day] += 1
            loads[day] += duration
            plan_date = (dt.date.fromisoformat(week) + dt.timedelta(days=day)).isoformat()
            try:
                con.execute("""INSERT INTO coach3_homework_assignments(
                    student_id,class_id,resource_id,curriculum_course_id,unit_id,topic_id,week_start,plan_date,slot_no,minutes,assigned_level)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (
                    sid, cls["id"] if cls else None, resource["id"], cid, resource["unit_id"], resource["topic_id"],
                    week, plan_date, counts[day], duration, level
                ))
                created += 1
            except Exception as exc:
                if "UNIQUE" not in str(exc).upper():
                    raise
    return {"student": student, "class": cls, "level": level, "week_start": week, "assignments": _homework_for_week(con, sid, week), "created": created, "warnings": warnings}


def install_coaching_model_v3(app):
    ensure_schema()

    @app.get("/api/coaching/v3/curriculum")
    def curriculum(request: Request):
        _require_admin_session(request)
        with connect() as con:
            return {"courses": _curriculum_tree(con)}

    @app.get("/api/coaching/v3/classes")
    def classes(request: Request, include_inactive: bool = False):
        _require_admin_session(request)
        with connect() as con:
            where = "" if include_inactive else "WHERE c.active=1"
            data = _rows(con, f"""SELECT c.*,
                (SELECT count(*) FROM coach3_student_class m JOIN coaching_students s ON s.id=m.student_id WHERE m.class_id=c.id AND s.active=1) student_count,
                (SELECT count(*) FROM coach3_course_assignments a WHERE a.scope_type='CLASS' AND a.scope_id=c.id AND a.active=1) course_count
                FROM coach3_classes c {where} ORDER BY c.name,c.id""")
            return {"classes": data}

    @app.post("/api/coaching/v3/classes")
    def create_class(body: ClassCreate, request: Request):
        _require_admin_session(request)
        name = _clean(body.name, "Sınıf adı", 120)
        with connect() as con:
            if _row(con, "SELECT id FROM coach3_classes WHERE name_key=?", (name.casefold(),)):
                raise HTTPException(409, "Bu sınıf zaten mevcut.")
            cur = con.execute("INSERT INTO coach3_classes(name,name_key,grade_label,difficulty_level,note) VALUES(?,?,?,?,?)",
                              (name, name.casefold(), body.grade_label.strip(), body.difficulty_level, body.note.strip()))
            return _row(con, "SELECT * FROM coach3_classes WHERE id=?", (cur.lastrowid,))

    @app.patch("/api/coaching/v3/classes/{cid}")
    def edit_class(cid: int, body: ClassEdit, request: Request):
        _require_admin_session(request)
        with connect() as con:
            c = _require_class(con, cid)
            values = body.model_dump(exclude_none=True)
            if "name" in values:
                name = _clean(values.pop("name"), "Sınıf adı", 120)
                clash = _row(con, "SELECT id FROM coach3_classes WHERE name_key=? AND id<>?", (name.casefold(), cid))
                if clash:
                    raise HTTPException(409, "Bu sınıf adı zaten kullanılıyor.")
                c["name"] = name
                c["name_key"] = name.casefold()
            for k, v in values.items():
                c[k] = int(v) if k == "active" else v
            con.execute("""UPDATE coach3_classes SET name=?,name_key=?,grade_label=?,difficulty_level=?,note=?,active=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                        (c["name"], c["name_key"], c["grade_label"], c["difficulty_level"], c["note"], c["active"], cid))
            return _row(con, "SELECT * FROM coach3_classes WHERE id=?", (cid,))

    @app.get("/api/coaching/v3/classes/{cid}")
    def class_detail(cid: int, request: Request):
        _require_admin_session(request)
        with connect() as con:
            c = _require_class(con, cid)
            students = _rows(con, """SELECT s.*,p.difficulty_override FROM coach3_student_class m
                JOIN coaching_students s ON s.id=m.student_id LEFT JOIN coach3_student_profiles p ON p.student_id=s.id
                WHERE m.class_id=? AND s.active=1 ORDER BY s.name,s.id""", (cid,))
            courses = _rows(con, """SELECT a.*,cc.name curriculum_course_name FROM coach3_course_assignments a
                JOIN coaching_curriculum_courses cc ON cc.id=a.curriculum_course_id
                WHERE a.scope_type='CLASS' AND a.scope_id=? AND a.active=1 ORDER BY cc.sort_order,cc.name""", (cid,))
            responsibilities = _rows(con, """SELECT r.*,cc.name course_name,u.name unit_name,t.name topic_name FROM coach3_responsibilities r
                JOIN coaching_curriculum_courses cc ON cc.id=r.curriculum_course_id
                LEFT JOIN coaching_curriculum_units u ON u.id=NULLIF(r.unit_id,0)
                LEFT JOIN coaching_curriculum_topics t ON t.id=NULLIF(r.topic_id,0)
                WHERE r.scope_type='CLASS' AND r.scope_id=? AND r.active=1 ORDER BY cc.sort_order,cc.name,u.sort_order,t.sort_order""", (cid,))
            return {"class": c, "students": students, "courses": courses, "responsibilities": responsibilities}

    @app.post("/api/coaching/v3/students")
    def create_student(body: StudentCreateV3, request: Request):
        _require_admin_session(request)
        name = _clean(body.name, "Öğrenci adı", 120)
        number = body.number.strip()
        with connect() as con:
            if number and _row(con, "SELECT id FROM coaching_students WHERE number=? AND active=1", (number,)):
                raise HTTPException(409, "Bu öğrenci numarası zaten kayıtlı.")
            if body.class_id is not None:
                _require_class(con, body.class_id)
            cur = con.execute("INSERT INTO coaching_students(name,number,note) VALUES(?,?,?)", (name, number, body.note.strip()))
            sid = int(cur.lastrowid)
            if body.class_id is not None:
                con.execute("INSERT INTO coach3_student_class(student_id,class_id) VALUES(?,?)", (sid, body.class_id))
            if body.difficulty_override:
                con.execute("INSERT INTO coach3_student_profiles(student_id,difficulty_override) VALUES(?,?)", (sid, body.difficulty_override))
            return {"student": _row(con, "SELECT * FROM coaching_students WHERE id=?", (sid,)), "class": _class_for_student(con, sid), "effective_level": _effective_level(con, sid)}

    @app.patch("/api/coaching/v3/students/{sid}/profile")
    def edit_student_profile(sid: int, body: StudentClassEdit, request: Request):
        _require_admin_session(request)
        with connect() as con:
            _require_student(con, sid)
            if body.class_id is None:
                con.execute("DELETE FROM coach3_student_class WHERE student_id=?", (sid,))
            else:
                _require_class(con, body.class_id)
                con.execute("INSERT INTO coach3_student_class(student_id,class_id) VALUES(?,?) ON CONFLICT(student_id) DO UPDATE SET class_id=excluded.class_id,assigned_at=CURRENT_TIMESTAMP", (sid, body.class_id))
            con.execute("INSERT INTO coach3_student_profiles(student_id,difficulty_override) VALUES(?,?) ON CONFLICT(student_id) DO UPDATE SET difficulty_override=excluded.difficulty_override,updated_at=CURRENT_TIMESTAMP", (sid, body.difficulty_override))
            return {"student_id": sid, "class": _class_for_student(con, sid), "difficulty_override": _student_override(con, sid), "effective_level": _effective_level(con, sid)}

    @app.put("/api/coaching/v3/{scope_type}/{scope_id}/courses")
    def set_course(scope_type: str, scope_id: int, body: CourseAssignmentEdit, request: Request):
        _require_admin_session(request)
        scope_type = scope_type.upper()
        with connect() as con:
            _scope_exists(con, scope_type, scope_id)
            _require_curriculum_course(con, body.curriculum_course_id)
            con.execute("""INSERT INTO coach3_course_assignments(scope_type,scope_id,curriculum_course_id,weekly_sessions,minutes,daily_exam,active)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(scope_type,scope_id,curriculum_course_id) DO UPDATE SET
                weekly_sessions=excluded.weekly_sessions,minutes=excluded.minutes,daily_exam=excluded.daily_exam,active=excluded.active,updated_at=CURRENT_TIMESTAMP""",
                (scope_type, scope_id, body.curriculum_course_id, body.weekly_sessions, body.minutes, 1 if body.daily_exam else 0, 1 if body.active else 0))
            return {"ok": True}

    @app.delete("/api/coaching/v3/{scope_type}/{scope_id}/courses/{course_id}")
    def remove_course(scope_type: str, scope_id: int, course_id: int, request: Request):
        _require_admin_session(request)
        scope_type = scope_type.upper()
        with connect() as con:
            _scope_exists(con, scope_type, scope_id)
            con.execute("UPDATE coach3_course_assignments SET active=0,updated_at=CURRENT_TIMESTAMP WHERE scope_type=? AND scope_id=? AND curriculum_course_id=?", (scope_type, scope_id, course_id))
            return {"ok": True}

    @app.put("/api/coaching/v3/{scope_type}/{scope_id}/responsibilities")
    def set_responsibilities(scope_type: str, scope_id: int, body: ResponsibilitySet, request: Request):
        _require_admin_session(request)
        scope_type = scope_type.upper()
        with connect() as con:
            _scope_exists(con, scope_type, scope_id)
            _require_curriculum_course(con, body.curriculum_course_id)
            normalized = []
            for item in body.selections:
                unit_id = int(item.get("unit_id") or 0)
                topic_id = int(item.get("topic_id") or 0)
                _validate_curriculum_path(con, body.curriculum_course_id, unit_id, topic_id)
                normalized.append((unit_id, topic_id))
            con.execute("UPDATE coach3_responsibilities SET active=0,updated_at=CURRENT_TIMESTAMP WHERE scope_type=? AND scope_id=? AND curriculum_course_id=?", (scope_type, scope_id, body.curriculum_course_id))
            for unit_id, topic_id in normalized:
                con.execute("""INSERT INTO coach3_responsibilities(scope_type,scope_id,curriculum_course_id,unit_id,topic_id,active)
                    VALUES(?,?,?,?,?,1) ON CONFLICT(scope_type,scope_id,curriculum_course_id,unit_id,topic_id) DO UPDATE SET active=1,updated_at=CURRENT_TIMESTAMP""",
                    (scope_type, scope_id, body.curriculum_course_id, unit_id, topic_id))
            return {"ok": True, "count": len(normalized)}

    @app.get("/api/coaching/v3/resources")
    def resources(request: Request, course_id: Optional[int] = None, unit_id: Optional[int] = None, topic_id: Optional[int] = None, include_inactive: bool = False):
        _require_admin_session(request)
        sql = """SELECT r.*,c.name course_name,u.name unit_name,t.name topic_name FROM coach3_resources r
            JOIN coaching_curriculum_courses c ON c.id=r.curriculum_course_id
            LEFT JOIN coaching_curriculum_units u ON u.id=NULLIF(r.unit_id,0)
            LEFT JOIN coaching_curriculum_topics t ON t.id=NULLIF(r.topic_id,0) WHERE 1=1"""
        args = []
        if not include_inactive:
            sql += " AND r.active=1"
        if course_id is not None:
            sql += " AND r.curriculum_course_id=?"; args.append(course_id)
        if unit_id is not None:
            sql += " AND r.unit_id=?"; args.append(unit_id)
        if topic_id is not None:
            sql += " AND r.topic_id=?"; args.append(topic_id)
        sql += " ORDER BY c.sort_order,c.name,u.sort_order,t.sort_order,r.id"
        with connect() as con:
            return {"resources": _rows(con, sql, args)}

    @app.post("/api/coaching/v3/resources/upload")
    async def upload_resource(request: Request,
                              curriculum_course_id: int = Form(...), unit_id: int = Form(0), topic_id: int = Form(0),
                              title: str = Form(...), kind: str = Form("PDF"), difficulty: str = Form(...),
                              estimated_minutes: int = Form(60), file: UploadFile = File(...)):
        _require_admin_session(request)
        kind = str(kind or "PDF").upper()
        if kind not in {"PDF", "TEST"}:
            raise HTTPException(400, "Dosya yükleme türü PDF veya TEST olmalıdır.")
        difficulty = _level(difficulty)
        title = _clean(title, "İçerik adı", 200)
        if estimated_minutes < 5 or estimated_minutes > 600:
            raise HTTPException(400, "Tahmini süre 5-600 dakika arasında olmalıdır.")
        original = Path(file.filename or "document.pdf").name
        if not original.lower().endswith(".pdf"):
            raise HTTPException(400, "Yalnız PDF dosyası yüklenebilir.")
        data = await file.read()
        if not data or len(data) > 50 * 1024 * 1024:
            raise HTTPException(400, "PDF boş veya 50 MB sınırını aşıyor.")
        if not data.startswith(b"%PDF"):
            raise HTTPException(400, "Dosya geçerli bir PDF değil.")
        digest = hashlib.sha256(data).hexdigest()
        with connect() as con:
            _validate_curriculum_path(con, curriculum_course_id, unit_id, topic_id)
            existing = _row(con, """SELECT * FROM coach3_resources WHERE curriculum_course_id=? AND unit_id=? AND topic_id=? AND sha256=? AND active=1""",
                            (curriculum_course_id, unit_id, topic_id, digest))
            if existing:
                return {"ok": True, "resource": existing, "duplicate": True}
            folder = _storage_root() / str(curriculum_course_id) / str(unit_id or 0) / str(topic_id or 0)
            folder.mkdir(parents=True, exist_ok=True)
            stored = folder / f"{digest[:16]}.pdf"
            if not stored.exists():
                stored.write_bytes(data)
            rel = str(stored.relative_to(_storage_root()))
            cur = con.execute("""INSERT INTO coach3_resources(curriculum_course_id,unit_id,topic_id,title,kind,difficulty,estimated_minutes,source_kind,stored_path,original_name,sha256)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (curriculum_course_id, unit_id, topic_id, title, kind, difficulty, estimated_minutes, "UPLOAD", rel, original, digest))
            resource = _row(con, "SELECT * FROM coach3_resources WHERE id=?", (cur.lastrowid,))
            return {"ok": True, "resource": resource, "duplicate": False}

    @app.post("/api/coaching/v3/resources/link")
    def link_resource(body: ResourceLink, request: Request):
        _require_admin_session(request)
        with connect() as con:
            _validate_curriculum_path(con, body.curriculum_course_id, body.unit_id, body.topic_id)
            if body.kind == "TEST":
                if not body.exam_id or not _row(con, "SELECT id FROM exams WHERE id=?", (body.exam_id,)):
                    raise HTTPException(404, "Sınav bulunamadı.")
            if body.kind == "VIDEO" and not re.match(r"^https?://", body.url or "", re.I):
                raise HTTPException(400, "Video için geçerli http/https adresi girin.")
            cur = con.execute("""INSERT INTO coach3_resources(curriculum_course_id,unit_id,topic_id,title,kind,difficulty,estimated_minutes,source_kind,exam_id,url)
                VALUES(?,?,?,?,?,?,?,?,?,?)""", (body.curriculum_course_id, body.unit_id, body.topic_id, body.title.strip(), body.kind, body.difficulty, body.estimated_minutes, "EXAM" if body.kind == "TEST" else "URL", body.exam_id, body.url.strip()))
            return {"ok": True, "resource": _row(con, "SELECT * FROM coach3_resources WHERE id=?", (cur.lastrowid,))}

    @app.get("/api/coaching/v3/resources/{rid}/file")
    def resource_file(rid: int, request: Request):
        _require_admin_session(request)
        with connect() as con:
            r = _row(con, "SELECT * FROM coach3_resources WHERE id=? AND active=1", (rid,))
        if not r or r["source_kind"] != "UPLOAD" or not r["stored_path"]:
            raise HTTPException(404, "PDF kaynağı bulunamadı.")
        root = _storage_root().resolve()
        path = (root / r["stored_path"]).resolve()
        if root not in path.parents or not path.is_file():
            raise HTTPException(404, "PDF dosyası bulunamadı.")
        return FileResponse(path, media_type="application/pdf", filename=r["original_name"] or (r["title"] + ".pdf"))

    @app.get("/api/coaching/v3/students/{sid}/model")
    def student_model(sid: int, request: Request, week_start: Optional[str] = None):
        _require_admin_session(request)
        week = _week_start(week_start)
        with connect() as con:
            student = _require_student(con, sid)
            cls = _class_for_student(con, sid)
            return {"student": student, "class": cls, "difficulty_override": _student_override(con, sid),
                    "effective_level": _effective_level(con, sid), "courses": _effective_courses(con, sid),
                    "responsibilities": _effective_responsibilities(con, sid),
                    "homework": _homework_for_week(con, sid, week), "week_start": week}

    @app.post("/api/coaching/v3/students/{sid}/homework/auto")
    def auto_homework(sid: int, body: HomeworkGenerate, request: Request):
        _require_admin_session(request)
        week = _week_start(body.week_start)
        with connect() as con:
            con.execute("BEGIN IMMEDIATE")
            return _generate_homework(con, sid, week, body.replace_unfinished)

    @app.patch("/api/coaching/v3/homework/{hid}")
    def homework_status(hid: int, body: HomeworkStatus, request: Request):
        _require_admin_session(request)
        with connect() as con:
            h = _row(con, "SELECT * FROM coach3_homework_assignments WHERE id=?", (hid,))
            if not h:
                raise HTTPException(404, "Ödev bulunamadı.")
            completed = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds") if body.status == "DONE" else None
            con.execute("UPDATE coach3_homework_assignments SET status=?,completed_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (body.status, completed, hid))
            return {"ok": True, "status": body.status}

    app.state.coaching_model_v3_installed = True
    return {"version": VERSION}
