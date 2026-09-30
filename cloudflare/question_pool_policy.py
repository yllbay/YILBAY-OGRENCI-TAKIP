"""Append-only question content and explicitly scoped Question Studio writes."""
from __future__ import annotations
import contextvars
import hashlib
import json
import re
import sqlite3

MARKER = 'GENESIS_QUESTION_POOL_APPEND_ONLY_V1'
WRITE_SCOPE = contextvars.ContextVar('genesis_pool_write_scope', default=None)
SCHEMA_SCOPE = contextvars.ContextVar('genesis_pool_schema_scope', default=False)
_original_connect = sqlite3.connect


def protected_table(name):
    name = str(name).lower()
    return (name in {'source_documents', 'crop_sessions', 'test_classes', 'exams',
                     'exam_questions', 'answer_key_runs', 'answer_key_entries'}
            or 'question' in name or 'topic' in name or name.startswith('test_')
            or name.startswith('exam_')) and name != 'question_asset_replication'


def question_write_route(method, path):
    if method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        return False
    return bool(re.fullmatch(
        r'/api/(topics|sources/upload|sources/\d+/release|crops(?:/.*)?|'
        r'answerkey/(?:analyze|ai-analyze)|classes(?:/.*)?|exams(?:/.*)?|'
        r'screen-capture(?:/.*)?|windows-capture(?:/.*)?|windows-overlay(?:/.*)?)', path))


def locked_route(method, path):
    return (method in {'PUT', 'PATCH', 'DELETE'} and bool(re.fullmatch(r'/api/(topics|classes)/\d+', path))
            or method == 'POST' and bool(re.fullmatch(r'/api/(topics|classes)/\d+/move', path))
            or method in {'POST', 'PUT', 'PATCH', 'DELETE'} and
               (path.startswith('/api/questions/') or path == '/api/maintenance/stale-prepared'))


def _record_insert(table, row_id):
    scope = WRITE_SCOPE.get()
    if scope is not None:
        scope['new_rows'].setdefault(table, set()).add(row_id)
    return 1


def _write_allowed(table, row_id, operation):
    scope = WRITE_SCOPE.get()
    if scope is None:
        return 0
    if operation == 'INSERT':
        return 1
    if table in {'questions', 'topics', 'source_documents', 'test_classes'}:
        return int(row_id in scope['new_rows'].get(table, set()))
    return 1


def guarded_connect(*args, **kwargs):
    con = _original_connect(*args, **kwargs)
    con.create_function('genesis_pool_write_allowed', 3, _write_allowed)
    con.create_function('genesis_pool_record_insert', 2, _record_insert)
    def authorize(action, arg1, arg2, database, trigger):
        table = arg2 if action == sqlite3.SQLITE_ALTER_TABLE else arg1
        if protected_table(table):
            if action in {sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE}:
                return sqlite3.SQLITE_OK if SCHEMA_SCOPE.get() else sqlite3.SQLITE_DENY
            if action in {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE}:
                return sqlite3.SQLITE_OK if WRITE_SCOPE.get() is not None else sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    con.set_authorizer(authorize)
    return con


def enable():
    if sqlite3.connect is not guarded_connect:
        sqlite3.connect = guarded_connect


def install_triggers(con):
    """Guards live in SQLite too: an uninstrumented connection cannot bypass them."""
    names = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
    for table in names:
        if not protected_table(table):
            continue
        q = '"' + table.replace('"', '""') + '"'
        columns = {r[1] for r in con.execute(f'pragma table_info({q})')}
        identity = 'id' if 'id' in columns else 'rowid'
        for operation in ('INSERT', 'UPDATE', 'DELETE'):
            row = 'NEW' if operation == 'INSERT' else 'OLD'
            condition = f"genesis_pool_write_allowed('{table}',{row}.{identity},'{operation}')=0"
            if operation == 'INSERT' and 'id' in columns:
                condition += f' OR EXISTS(SELECT 1 FROM {q} WHERE id=NEW.id)'
            if table == 'crop_sessions' and operation != 'INSERT':
                # Drafts can be edited/cancelled; finalized crop metadata stays immutable.
                condition += " OR OLD.status='FINALIZED'"
            con.execute(f'''CREATE TRIGGER IF NOT EXISTS "genesis_pool_{table}_{operation.lower()}"
                BEFORE {operation} ON {q} WHEN {condition}
                BEGIN SELECT RAISE(ABORT,'QUESTION_POOL_IMMUTABLE'); END''')
        con.execute(f'''CREATE TRIGGER IF NOT EXISTS "genesis_pool_{table}_inserted"
            AFTER INSERT ON {q} BEGIN
            SELECT genesis_pool_record_insert('{table}',NEW.{identity}); END''')


def fingerprint(con):
    tables = {}
    names = sorted(r[0] for r in con.execute("select name from sqlite_master where type='table'"))
    for table in names:
        if not protected_table(table):
            continue
        q = '"' + table.replace('"', '""') + '"'
        columns = [r[1] for r in con.execute(f'pragma table_info({q})')]
        rows = [list(row) for row in con.execute(f'select * from {q}')]
        rows.sort(key=lambda row: json.dumps(row, ensure_ascii=False, default=str))
        raw = json.dumps({'columns': columns, 'rows': rows}, ensure_ascii=False,
                         separators=(',', ':'), default=str).encode()
        tables[table] = {'count': len(rows), 'sha256': hashlib.sha256(raw).hexdigest()}
    raw = json.dumps(tables, sort_keys=True, separators=(',', ':')).encode()
    return {'marker': MARKER, 'protected_tables': tables, 'sha256': hashlib.sha256(raw).hexdigest()}


def immutable_rows(con):
    result = {}
    for table in ('topics', 'questions', 'source_documents', 'test_classes'):
        try:
            rows = con.execute(f'select * from "{table}"').fetchall()
        except sqlite3.OperationalError:
            continue
        result[table] = {row[0]: tuple(row) for row in rows}
    # Once finalized, a crop is as immutable as its question.
    try:
        rows = con.execute("select * from crop_sessions where status='FINALIZED'").fetchall()
        result['crop_sessions'] = {row[0]: tuple(row) for row in rows}
    except sqlite3.OperationalError:
        pass
    return result


def assert_preserved(before, con):
    current = immutable_rows(con)
    for table, rows in before.items():
        for row_id, row in rows.items():
            if current.get(table, {}).get(row_id) != row:
                raise RuntimeError('QUESTION_POOL_IMMUTABLE: existing protected row changed')
