"""GENESIS Coaching Model V1.

Persistent class / responsibility / resource / difficulty / homework model.
Additive only: existing coaching_students, coaching_courses and coach2_* data stay intact.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
import threading
from contextlib import contextmanager
from typing import Literal, Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from db import connect
from auth import session_from_token

VERSION = "1.0.0"
_LOCK = threading.RLock()
Level = Literal["KOLAY", "ORTA", "ZOR"]
TargetType = Literal["CLASS", "STUDENT"]
ResourceType = Literal["PDF", "TEST", "VIDEO"]


def _row(con, sql, args=()):
    x = con.execute(sql, args).fetchone()
    return dict(x) if x else None


def _rows(con, sql, args=()):
    return [dict(x) for x in con.execute(sql, args)]


@contextmanager
def _write():
    with _LOCK:
        with connect() as con:
            con.execute("BEGIN IMMEDIATE")
            yield con


def _owner(request: Request):
    session = getattr(request.state, "genesis_session", None) or session_from_token(
        request.cookies.get("genesis_session")
    )
    if not session or session.get("role") not in ("ADMIN", "INSTITUTION"):
        raise HTTPException(403, "Koçluk alanı için GENESIS oturumu gerekli.")
    return True


def _student(con, sid: int):
    x = _row(con, "SELECT * FROM coaching_students WHERE id=? AND active=1", (sid,))
    if not x:
        raise HTTPException(404, "Öğrenci bulunamadı.")
    return x


def _class(con, cid: int):
    x = _row(con, "SELECT * FROM coach3_classes WHERE id=? AND active=1", (cid,))
    if not x:
        raise HTTPException(404, "Sınıf bulunamadı.")
    return x


def _topic(con, tid: int):
    x = _row(
        con,
        """SELECT t.id,t.name topic_name,u.id unit_id,u.name unit_name,
                  c.id course_id,c.name course_name
           FROM coaching_curriculum_topics t
           JOIN coaching_curriculum_units u ON u.id=t.unit_id
           JOIN coaching_curriculum_courses c ON c.id=u.course_id
           WHERE t.id=? AND t.is_active=1 AND u.is_active=1 AND c.is_active=1""",
        (tid,),
    )
    if not x:
        raise HTTPException(404, "Alt başlık bulunamadı.")
    return x


def _course(con, course_id: int):
    x = _row(
        con,
        "SELECT id,name FROM coaching_curriculum_courses WHERE id=? AND is_active=1",
        (course_id,),
    )
    if not x:
        raise HTTPException(404, "Ders bulunamadı.")
    return x


def ensure_schema():
    with connect() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS coach3_classes(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              grade_label TEXT NOT NULL DEFAULT '',
              difficulty_level TEXT NOT NULL DEFAULT 'ORTA'
                CHECK(difficulty_level IN ('KOLAY','ORTA','ZOR')),
              active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS ux_coach3_class_name
              ON coach3_classes(name) WHERE active=1;

            CREATE TABLE IF NOT EXISTS coach3_class_students(
              class_id INTEGER NOT NULL REFERENCES coach3_classes(id) ON DELETE RESTRICT,
              student_id INTEGER NOT NULL REFERENCES coaching_students(id) ON DELETE CASCADE,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY(class_id,student_id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS ux_coach3_student_single_class
              ON coach3_class_students(student_id);

            CREATE TABLE IF NOT EXISTS coach3_student_profiles(
              student_id INTEGER PRIMARY KEY REFERENCES coaching_students(id) ON DELETE CASCADE,
              difficulty_level TEXT
                CHECK(difficulty_level IS NULL OR difficulty_level IN ('KOLAY','ORTA','ZOR')),
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS coach3_class_courses(
              class_id INTEGER NOT NULL REFERENCES coach3_classes(id) ON DELETE CASCADE,
              curriculum_course_id INTEGER NOT NULL
                REFERENCES coaching_curriculum_courses(id) ON DELETE RESTRICT,
              coaching_enabled INTEGER NOT NULL DEFAULT 1,
              position INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY(class_id,curriculum_course_id)
            );

            CREATE TABLE IF NOT EXISTS coach3_responsibilities(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              target_type TEXT NOT NULL CHECK(target_type IN ('CLASS','STUDENT')),
              target_id INTEGER NOT NULL,
              curriculum_topic_id INTEGER NOT NULL
                REFERENCES coaching_curriculum_topics(id) ON DELETE RESTRICT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(target_type,target_id,curriculum_topic_id)
            );
            CREATE INDEX IF NOT EXISTS ix_coach3_resp_target
              ON coach3_responsibilities(target_type,target_id,curriculum_topic_id);

            CREATE TABLE IF NOT EXISTS coach3_resources(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              curriculum_topic_id INTEGER NOT NULL
                REFERENCES coaching_curriculum_topics(id) ON DELETE RESTRICT,
              title TEXT NOT NULL,
              resource_type TEXT NOT NULL CHECK(resource_type IN ('PDF','TEST','VIDEO')),
              difficulty_level TEXT NOT NULL CHECK(difficulty_level IN ('KOLAY','ORTA','ZOR')),
              storage_ref TEXT NOT NULL DEFAULT '',
              exam_id INTEGER REFERENCES exams(id) ON DELETE RESTRICT,
              duration_minutes INTEGER NOT NULL DEFAULT 30
                CHECK(duration_minutes BETWEEN 1 AND 600),
              active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS ix_coach3_resource_topic_level
              ON coach3_resources(curriculum_topic_id,difficulty_level,active,id);

            CREATE TABLE IF NOT EXISTS coach3_homework_assignments(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id INTEGER NOT NULL REFERENCES coaching_students(id) ON DELETE CASCADE,
              class_id INTEGER REFERENCES coach3_classes(id) ON DELETE SET NULL,
              resource_id INTEGER NOT NULL REFERENCES coach3_resources(id) ON DELETE RESTRICT,
              plan_date TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'PLANNED'
                CHECK(status IN ('PLANNED','DONE')),
              source TEXT NOT NULL DEFAULT 'AUTO'
                CHECK(source IN ('AUTO','MANUAL')),
              completed_at TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(student_id,resource_id,plan_date)
            );
            CREATE INDEX IF NOT EXISTS ix_coach3_homework_student_date
              ON coach3_homework_assignments(student_id,plan_date,status);
            """
        )


class ClassEdit(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    grade_label: str = Field(default="", max_length=60)
    difficulty_level: Level = "ORTA"


class ClassCoursesEdit(BaseModel):
    course_ids: list[int] = Field(default_factory=list, max_length=100)


class StudentProfileEdit(BaseModel):
    difficulty_level: Optional[Level] = None


class ResponsibilitiesEdit(BaseModel):
    target_type: TargetType
    target_id: int = Field(gt=0)
    topic_ids: list[int] = Field(default_factory=list, max_length=1000)


class ResourceEdit(BaseModel):
    curriculum_topic_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=220)
    resource_type: ResourceType
    difficulty_level: Level
    storage_ref: str = Field(default="", max_length=1000)
    exam_id: Optional[int] = None
    duration_minutes: int = Field(default=30, ge=1, le=600)
    active: bool = True


class AutoHomeworkRequest(BaseModel):
    target_type: TargetType
    target_id: int = Field(gt=0)
    week_start: Optional[str] = None
    max_items_per_student: int = Field(default=7, ge=1, le=28)


class HomeworkStatusEdit(BaseModel):
    status: Literal["PLANNED", "DONE"]


def _week_start(value: Optional[str]) -> dt.date:
    if value:
        try:
            d = dt.date.fromisoformat(value)
        except ValueError:
            raise HTTPException(400, "Geçerli bir hafta tarihi girin.")
    else:
        d = dt.date.today()
    return d - dt.timedelta(days=d.weekday())


def _class_for_student(con, sid: int):
    return _row(
        con,
        """SELECT c.* FROM coach3_class_students cs
           JOIN coach3_classes c ON c.id=cs.class_id
           WHERE cs.student_id=? AND c.active=1""",
        (sid,),
    )


def _effective_level(con, sid: int) -> str:
    p = _row(con, "SELECT difficulty_level FROM coach3_student_profiles WHERE student_id=?", (sid,))
    if p and p.get("difficulty_level"):
        return p["difficulty_level"]
    c = _class_for_student(con, sid)
    return c["difficulty_level"] if c else "ORTA"


def _target_topics(con, target_type: str, target_id: int):
    direct = [
        x["curriculum_topic_id"]
        for x in _rows(
            con,
            """SELECT curriculum_topic_id FROM coach3_responsibilities
               WHERE target_type=? AND target_id=? ORDER BY id""",
            (target_type, target_id),
        )
    ]
    if direct:
        return direct
    if target_type == "STUDENT":
        c = _class_for_student(con, target_id)
        if c:
            inherited = [
                x["curriculum_topic_id"]
                for x in _rows(
                    con,
                    """SELECT curriculum_topic_id FROM coach3_responsibilities
                       WHERE target_type='CLASS' AND target_id=? ORDER BY id""",
                    (c["id"],),
                )
            ]
            if inherited:
                return inherited
            target_type, target_id = "CLASS", c["id"]
        else:
            return []
    if target_type == "CLASS":
        return [
            x["id"]
            for x in _rows(
                con,
                """SELECT t.id
                   FROM coach3_class_courses cc
                   JOIN coaching_curriculum_units u
                     ON u.course_id=cc.curriculum_course_id AND u.is_active=1
                   JOIN coaching_curriculum_topics t
                     ON t.unit_id=u.id AND t.is_active=1
                   WHERE cc.class_id=? AND cc.coaching_enabled=1
                   ORDER BY cc.position,u.sort_order,u.id,t.sort_order,t.id""",
                (target_id,),
            )
        ]
    return []


def _students_for_target(con, target_type: str, target_id: int):
    if target_type == "STUDENT":
        _student(con, target_id)
        return [target_id]
    _class(con, target_id)
    return [
        x["student_id"]
        for x in _rows(
            con,
            """SELECT cs.student_id FROM coach3_class_students cs
               JOIN coaching_students s ON s.id=cs.student_id AND s.active=1
               WHERE cs.class_id=? ORDER BY s.name,s.id""",
            (target_id,),
        )
    ]


def _resource_rows(con, topic_ids: list[int], level: str):
    if not topic_ids:
        return []
    marks = ",".join("?" for _ in topic_ids)
    return _rows(
        con,
        f"""SELECT r.*,t.name topic_name,u.name unit_name,c.name course_name
            FROM coach3_resources r
            JOIN coaching_curriculum_topics t ON t.id=r.curriculum_topic_id
            JOIN coaching_curriculum_units u ON u.id=t.unit_id
            JOIN coaching_curriculum_courses c ON c.id=u.course_id
            WHERE r.active=1 AND r.difficulty_level=?
              AND r.curriculum_topic_id IN ({marks})
            ORDER BY c.sort_order,c.id,u.sort_order,u.id,t.sort_order,t.id,r.id""",
        [level, *topic_ids],
    )


def _homework_week(con, sid: int, week: dt.date):
    end = week + dt.timedelta(days=6)
    return _rows(
        con,
        """SELECT h.*,r.title,r.resource_type,r.difficulty_level,r.storage_ref,
                  r.exam_id,r.duration_minutes,t.name topic_name,u.name unit_name,
                  c.name course_name
           FROM coach3_homework_assignments h
           JOIN coach3_resources r ON r.id=h.resource_id
           JOIN coaching_curriculum_topics t ON t.id=r.curriculum_topic_id
           JOIN coaching_curriculum_units u ON u.id=t.unit_id
           JOIN coaching_curriculum_courses c ON c.id=u.course_id
           WHERE h.student_id=? AND h.plan_date BETWEEN ? AND ?
           ORDER BY h.plan_date,h.id""",
        (sid, week.isoformat(), end.isoformat()),
    )


def _classes_payload(con):
    classes = _rows(
        con,
        """SELECT c.*,
             (SELECT count(*) FROM coach3_class_students cs
              JOIN coaching_students s ON s.id=cs.student_id AND s.active=1
              WHERE cs.class_id=c.id) student_count,
             (SELECT count(*) FROM coach3_class_courses cc
              WHERE cc.class_id=c.id AND cc.coaching_enabled=1) course_count
           FROM coach3_classes c WHERE c.active=1 ORDER BY c.name,c.id""",
    )
    for c in classes:
        c["students"] = _rows(
            con,
            """SELECT s.id,s.name,s.number,
                      p.difficulty_level difficulty_override
               FROM coach3_class_students cs
               JOIN coaching_students s ON s.id=cs.student_id AND s.active=1
               LEFT JOIN coach3_student_profiles p ON p.student_id=s.id
               WHERE cs.class_id=? ORDER BY s.name,s.id""",
            (c["id"],),
        )
        c["courses"] = _rows(
            con,
            """SELECT cc.curriculum_course_id id,cur.name,cc.coaching_enabled,cc.position
               FROM coach3_class_courses cc
               JOIN coaching_curriculum_courses cur ON cur.id=cc.curriculum_course_id
               WHERE cc.class_id=? ORDER BY cc.position,cur.name,cur.id""",
            (c["id"],),
        )
    return classes


def install_coaching_model_v1(app):
    if getattr(app.state, "coaching_model_v1_installed", False):
        return {"version": VERSION}
    ensure_schema()

    @app.get("/api/coaching/model/classes")
    def classes(_: bool = Depends(_owner)):
        with connect() as con:
            return {"classes": _classes_payload(con)}

    @app.post("/api/coaching/model/classes")
    def create_class(body: ClassEdit, _: bool = Depends(_owner)):
        with _write() as con:
            try:
                cur = con.execute(
                    """INSERT INTO coach3_classes(name,grade_label,difficulty_level)
                       VALUES(?,?,?)""",
                    (body.name.strip(), body.grade_label.strip(), body.difficulty_level),
                )
            except sqlite3.IntegrityError:
                raise HTTPException(409, "Bu sınıf adı zaten kayıtlı.")
            return _class(con, int(cur.lastrowid))

    @app.put("/api/coaching/model/classes/{cid}")
    def update_class(cid: int, body: ClassEdit, _: bool = Depends(_owner)):
        with _write() as con:
            _class(con, cid)
            try:
                con.execute(
                    """UPDATE coach3_classes SET name=?,grade_label=?,difficulty_level=?,
                       updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (body.name.strip(), body.grade_label.strip(), body.difficulty_level, cid),
                )
            except sqlite3.IntegrityError:
                raise HTTPException(409, "Bu sınıf adı zaten kayıtlı.")
            return _class(con, cid)

    @app.delete("/api/coaching/model/classes/{cid}")
    def archive_class(cid: int, _: bool = Depends(_owner)):
        with _write() as con:
            _class(con, cid)
            con.execute(
                "UPDATE coach3_classes SET active=0,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (cid,),
            )
            return {"ok": True}

    @app.post("/api/coaching/model/classes/{cid}/students/{sid}")
    def assign_student(cid: int, sid: int, _: bool = Depends(_owner)):
        with _write() as con:
            _class(con, cid)
            _student(con, sid)
            con.execute("DELETE FROM coach3_class_students WHERE student_id=?", (sid,))
            con.execute(
                "INSERT INTO coach3_class_students(class_id,student_id) VALUES(?,?)",
                (cid, sid),
            )
            return {"ok": True, "class_id": cid, "student_id": sid}

    @app.delete("/api/coaching/model/classes/{cid}/students/{sid}")
    def remove_student(cid: int, sid: int, _: bool = Depends(_owner)):
        with _write() as con:
            _class(con, cid)
            _student(con, sid)
            con.execute(
                "DELETE FROM coach3_class_students WHERE class_id=? AND student_id=?",
                (cid, sid),
            )
            return {"ok": True}

    @app.get("/api/coaching/model/classes/{cid}/courses")
    def get_class_courses(cid: int, _: bool = Depends(_owner)):
        with connect() as con:
            _class(con, cid)
            return {
                "courses": _rows(
                    con,
                    """SELECT cc.curriculum_course_id id,c.name,cc.coaching_enabled,cc.position
                       FROM coach3_class_courses cc
                       JOIN coaching_curriculum_courses c ON c.id=cc.curriculum_course_id
                       WHERE cc.class_id=? ORDER BY cc.position,c.name,c.id""",
                    (cid,),
                )
            }

    @app.put("/api/coaching/model/classes/{cid}/courses")
    def set_class_courses(cid: int, body: ClassCoursesEdit, _: bool = Depends(_owner)):
        ids = list(dict.fromkeys(int(x) for x in body.course_ids))
        with _write() as con:
            _class(con, cid)
            for x in ids:
                _course(con, x)
            con.execute("DELETE FROM coach3_class_courses WHERE class_id=?", (cid,))
            con.executemany(
                """INSERT INTO coach3_class_courses(class_id,curriculum_course_id,position)
                   VALUES(?,?,?)""",
                [(cid, x, i) for i, x in enumerate(ids)],
            )
            return {"ok": True, "course_ids": ids}

    @app.put("/api/coaching/model/students/{sid}/profile")
    def set_student_profile(sid: int, body: StudentProfileEdit, _: bool = Depends(_owner)):
        with _write() as con:
            _student(con, sid)
            con.execute(
                """INSERT INTO coach3_student_profiles(student_id,difficulty_level,updated_at)
                   VALUES(?,?,CURRENT_TIMESTAMP)
                   ON CONFLICT(student_id) DO UPDATE SET
                     difficulty_level=excluded.difficulty_level,
                     updated_at=CURRENT_TIMESTAMP""",
                (sid, body.difficulty_level),
            )
            return {
                "ok": True,
                "student_id": sid,
                "difficulty_level": body.difficulty_level,
                "effective_level": _effective_level(con, sid),
            }

    @app.get("/api/coaching/model/responsibilities")
    def get_responsibilities(
        target_type: TargetType,
        target_id: int,
        _: bool = Depends(_owner),
    ):
        with connect() as con:
            if target_type == "CLASS":
                _class(con, target_id)
            else:
                _student(con, target_id)
            direct = _rows(
                con,
                """SELECT r.curriculum_topic_id topic_id,t.name topic_name,u.name unit_name,
                          c.name course_name
                   FROM coach3_responsibilities r
                   JOIN coaching_curriculum_topics t ON t.id=r.curriculum_topic_id
                   JOIN coaching_curriculum_units u ON u.id=t.unit_id
                   JOIN coaching_curriculum_courses c ON c.id=u.course_id
                   WHERE r.target_type=? AND r.target_id=?
                   ORDER BY c.sort_order,c.id,u.sort_order,u.id,t.sort_order,t.id""",
                (target_type, target_id),
            )
            effective = _target_topics(con, target_type, target_id)
            return {"direct": direct, "effective_topic_ids": effective}

    @app.put("/api/coaching/model/responsibilities")
    def set_responsibilities(body: ResponsibilitiesEdit, _: bool = Depends(_owner)):
        ids = list(dict.fromkeys(int(x) for x in body.topic_ids))
        with _write() as con:
            if body.target_type == "CLASS":
                _class(con, body.target_id)
            else:
                _student(con, body.target_id)
            for x in ids:
                _topic(con, x)
            con.execute(
                "DELETE FROM coach3_responsibilities WHERE target_type=? AND target_id=?",
                (body.target_type, body.target_id),
            )
            con.executemany(
                """INSERT INTO coach3_responsibilities(target_type,target_id,curriculum_topic_id)
                   VALUES(?,?,?)""",
                [(body.target_type, body.target_id, x) for x in ids],
            )
            return {"ok": True, "topic_ids": ids}

    @app.get("/api/coaching/model/resources")
    def resources(
        topic_id: Optional[int] = None,
        difficulty_level: Optional[Level] = None,
        _: bool = Depends(_owner),
    ):
        where = ["r.active=1"]
        args: list[object] = []
        if topic_id is not None:
            where.append("r.curriculum_topic_id=?")
            args.append(topic_id)
        if difficulty_level is not None:
            where.append("r.difficulty_level=?")
            args.append(difficulty_level)
        with connect() as con:
            return {
                "resources": _rows(
                    con,
                    """SELECT r.*,t.name topic_name,u.name unit_name,c.name course_name
                       FROM coach3_resources r
                       JOIN coaching_curriculum_topics t ON t.id=r.curriculum_topic_id
                       JOIN coaching_curriculum_units u ON u.id=t.unit_id
                       JOIN coaching_curriculum_courses c ON c.id=u.course_id
                       WHERE """
                    + " AND ".join(where)
                    + " ORDER BY c.sort_order,c.id,u.sort_order,u.id,t.sort_order,t.id,r.id",
                    args,
                )
            }

    @app.post("/api/coaching/model/resources")
    def create_resource(body: ResourceEdit, _: bool = Depends(_owner)):
        with _write() as con:
            _topic(con, body.curriculum_topic_id)
            if body.exam_id is not None and not _row(con, "SELECT id FROM exams WHERE id=?", (body.exam_id,)):
                raise HTTPException(404, "Sınav kaynağı bulunamadı.")
            cur = con.execute(
                """INSERT INTO coach3_resources(
                     curriculum_topic_id,title,resource_type,difficulty_level,
                     storage_ref,exam_id,duration_minutes,active)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (
                    body.curriculum_topic_id,
                    body.title.strip(),
                    body.resource_type,
                    body.difficulty_level,
                    body.storage_ref.strip(),
                    body.exam_id,
                    body.duration_minutes,
                    1 if body.active else 0,
                ),
            )
            return _row(con, "SELECT * FROM coach3_resources WHERE id=?", (cur.lastrowid,))

    @app.put("/api/coaching/model/resources/{rid}")
    def update_resource(rid: int, body: ResourceEdit, _: bool = Depends(_owner)):
        with _write() as con:
            if not _row(con, "SELECT id FROM coach3_resources WHERE id=?", (rid,)):
                raise HTTPException(404, "İçerik bulunamadı.")
            _topic(con, body.curriculum_topic_id)
            if body.exam_id is not None and not _row(con, "SELECT id FROM exams WHERE id=?", (body.exam_id,)):
                raise HTTPException(404, "Sınav kaynağı bulunamadı.")
            con.execute(
                """UPDATE coach3_resources SET curriculum_topic_id=?,title=?,resource_type=?,
                   difficulty_level=?,storage_ref=?,exam_id=?,duration_minutes=?,active=?,
                   updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (
                    body.curriculum_topic_id,
                    body.title.strip(),
                    body.resource_type,
                    body.difficulty_level,
                    body.storage_ref.strip(),
                    body.exam_id,
                    body.duration_minutes,
                    1 if body.active else 0,
                    rid,
                ),
            )
            return _row(con, "SELECT * FROM coach3_resources WHERE id=?", (rid,))

    @app.get("/api/coaching/model/students/{sid}/context")
    def student_context(sid: int, week_start: Optional[str] = None, _: bool = Depends(_owner)):
        week = _week_start(week_start)
        with connect() as con:
            s = _student(con, sid)
            c = _class_for_student(con, sid)
            profile = _row(
                con,
                "SELECT difficulty_level FROM coach3_student_profiles WHERE student_id=?",
                (sid,),
            )
            return {
                "student": {"id": s["id"], "name": s["name"], "number": s["number"]},
                "class": c,
                "difficulty_override": profile["difficulty_level"] if profile else None,
                "effective_level": _effective_level(con, sid),
                "effective_topic_ids": _target_topics(con, "STUDENT", sid),
                "homework": _homework_week(con, sid, week),
            }

    @app.get("/api/coaching/model/students/{sid}/week")
    def student_week(sid: int, week_start: Optional[str] = None, _: bool = Depends(_owner)):
        week = _week_start(week_start)
        with connect() as con:
            _student(con, sid)
            return {
                "week_start": week.isoformat(),
                "week_end": (week + dt.timedelta(days=6)).isoformat(),
                "effective_level": _effective_level(con, sid),
                "homework": _homework_week(con, sid, week),
            }

    def _auto_preview(con, body: AutoHomeworkRequest):
        week = _week_start(body.week_start)
        students = _students_for_target(con, body.target_type, body.target_id)
        if not students:
            return {
                "week_start": week.isoformat(),
                "students": [],
                "assignments": [],
                "warnings": ["Seçilen hedefte öğrenci bulunmuyor."],
            }
        all_rows = []
        warnings = []
        for sid in students:
            level = _effective_level(con, sid)
            topics = _target_topics(con, "STUDENT", sid)
            resources = _resource_rows(con, topics, level)
            existing_ids = {
                x["resource_id"]
                for x in _homework_week(con, sid, week)
            }
            resources = [r for r in resources if r["id"] not in existing_ids]
            if not topics:
                warnings.append(f"Öğrenci #{sid}: sorumluluk konusu bulunmuyor.")
            elif not resources:
                warnings.append(f"Öğrenci #{sid}: {level} düzeyinde uygun içerik bulunmuyor.")
            for i, r in enumerate(resources[: body.max_items_per_student]):
                all_rows.append(
                    {
                        "student_id": sid,
                        "class_id": (_class_for_student(con, sid) or {}).get("id"),
                        "resource_id": r["id"],
                        "title": r["title"],
                        "resource_type": r["resource_type"],
                        "difficulty_level": r["difficulty_level"],
                        "course_name": r["course_name"],
                        "unit_name": r["unit_name"],
                        "topic_name": r["topic_name"],
                        "duration_minutes": r["duration_minutes"],
                        "plan_date": (week + dt.timedelta(days=i % 7)).isoformat(),
                    }
                )
        return {
            "week_start": week.isoformat(),
            "week_end": (week + dt.timedelta(days=6)).isoformat(),
            "students": students,
            "assignments": all_rows,
            "warnings": warnings,
        }

    @app.post("/api/coaching/model/homework/preview")
    def auto_homework_preview(body: AutoHomeworkRequest, _: bool = Depends(_owner)):
        with connect() as con:
            return _auto_preview(con, body)

    @app.post("/api/coaching/model/homework/apply")
    def auto_homework_apply(body: AutoHomeworkRequest, _: bool = Depends(_owner)):
        with _write() as con:
            data = _auto_preview(con, body)
            created = 0
            for a in data["assignments"]:
                try:
                    con.execute(
                        """INSERT INTO coach3_homework_assignments(
                             student_id,class_id,resource_id,plan_date,source)
                           VALUES(?,?,?,?, 'AUTO')""",
                        (a["student_id"], a["class_id"], a["resource_id"], a["plan_date"]),
                    )
                    created += 1
                except sqlite3.IntegrityError:
                    pass
            return {
                "ok": True,
                "created": created,
                "week_start": data["week_start"],
                "warnings": data["warnings"],
            }

    @app.patch("/api/coaching/model/homework/{hid}")
    def update_homework(hid: int, body: HomeworkStatusEdit, _: bool = Depends(_owner)):
        with _write() as con:
            x = _row(con, "SELECT * FROM coach3_homework_assignments WHERE id=?", (hid,))
            if not x:
                raise HTTPException(404, "Ödev bulunamadı.")
            con.execute(
                """UPDATE coach3_homework_assignments
                   SET status=?,completed_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (
                    body.status,
                    dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
                    if body.status == "DONE"
                    else None,
                    hid,
                ),
            )
            return {"ok": True}

    app.state.coaching_model_v1_installed = True
    return {"version": VERSION}
