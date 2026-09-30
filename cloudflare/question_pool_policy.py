"""Only deliberate authenticated user requests may change Question Studio data."""
from __future__ import annotations
import contextvars
import hashlib
import hmac
import json
import re
import secrets
import sqlite3

MARKER = 'GENESIS_QUESTION_POOL_USER_OWNED_V2'
WRITE_SCOPE = contextvars.ContextVar('genesis_pool_write_scope', default=None)
SCHEMA_SCOPE = contextvars.ContextVar('genesis_pool_schema_scope', default=False)
JOURNAL_TABLES = {'pool_user_changes', 'pool_asset_deletions'}
_intent_secret = secrets.token_bytes(32)
_original_connect = sqlite3.connect


def protected_table(name):
    name = str(name).lower()
    if name.startswith(('coach2_', 'coach3_', 'coaching_')):
        return False
    return (name in {'source_documents', 'crop_sessions', 'test_classes', 'exams',
                     'exam_questions', 'answer_key_runs', 'answer_key_entries'}
            or 'question' in name or 'topic' in name or name.startswith('test_')
            or name.startswith('exam_')) and name != 'question_asset_replication'


def question_write_route(method, path):
    if method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        return False
    return bool(re.fullmatch(
        r'/api/(topics(?:/\d+(?:/move)?)?|sources/upload|sources/\d+/release|crops(?:/.*)?|'
        r'questions/(?:delete-all|\d+(?:/(?:move|learning-outcome))?)|'
        r'answerkey/(?:analyze|ai-analyze)|classes(?:/\d+(?:/move)?)?|exams(?:/.*)?|'
        r'screen-capture(?:/.*)?|windows-capture(?:/.*)?|windows-overlay(?:/.*)?)', path))


def locked_route(method, path):
    return method != 'GET' and path == '/api/maintenance/stale-prepared'


def intent_token(session_token):
    return hmac.new(_intent_secret, session_token.encode(), hashlib.sha256).hexdigest()


def valid_intent(session_token, supplied):
    return bool(session_token and supplied and hmac.compare_digest(intent_token(session_token), supplied))


def human_scope():
    scope = WRITE_SCOPE.get()
    return scope if scope and scope.get('actor') and scope.get('user_intent') else None


def _write_allowed(table, row_id, operation):
    return int(human_scope() is not None)


def guarded_connect(*args, **kwargs):
    con = _original_connect(*args, **kwargs)
    con.create_function('genesis_pool_write_allowed', 3, _write_allowed)
    con.create_function('genesis_pool_record_insert', 2, lambda *args: 1)
    con.create_function('genesis_pool_actor', 0, lambda: (human_scope() or {}).get('actor', ''))
    con.create_function('genesis_pool_action', 0, lambda: (human_scope() or {}).get('path', ''))
    def authorize(action, arg1, arg2, database, trigger):
        table = arg2 if action in {sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_CREATE_TRIGGER,
                                  sqlite3.SQLITE_DROP_TRIGGER} else arg1
        if protected_table(table) or table in JOURNAL_TABLES:
            if action in {sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE,
                          sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_DROP_TRIGGER}:
                return sqlite3.SQLITE_OK if SCHEMA_SCOPE.get() else sqlite3.SQLITE_DENY
            if action in {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE}:
                if table in JOURNAL_TABLES:
                    permitted = (action == sqlite3.SQLITE_INSERT and trigger and
                                 trigger.startswith('genesis_pool_') and human_scope())
                else:
                    permitted = human_scope()
                return sqlite3.SQLITE_OK if permitted else sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    con.set_authorizer(authorize)
    return con


def enable():
    if sqlite3.connect is not guarded_connect:
        sqlite3.connect = guarded_connect


def _quote(name):
    return '"' + name.replace('"', '""') + '"'


def _schema(con, table):
    columns = list(con.execute(f'pragma table_info({_quote(table)})'))
    names = [r[1] for r in columns]
    pk = [r[1] for r in sorted(columns, key=lambda r: r[5]) if r[5]] or ['rowid']
    return names, pk


def install_triggers(con):
    """Upgrade only schema/guards, never rewrite or normalize existing content."""
    con.execute('''CREATE TABLE IF NOT EXISTS pool_user_changes(
        seq INTEGER PRIMARY KEY AUTOINCREMENT, table_name TEXT NOT NULL,
        row_key TEXT NOT NULL, before_json TEXT, after_json TEXT,
        actor TEXT NOT NULL, action TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    con.execute('''CREATE TABLE IF NOT EXISTS pool_asset_deletions(
        seq INTEGER PRIMARY KEY AUTOINCREMENT, asset_key TEXT NOT NULL,
        actor TEXT NOT NULL, action TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    names = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
    for name, in con.execute("select name from sqlite_master where type='trigger' and name like 'genesis_pool_%'").fetchall():
        con.execute(f'DROP TRIGGER {_quote(name)}')
    for table in names:
        if not protected_table(table):
            continue
        q = _quote(table)
        columns, pk = _schema(con, table)
        def array(row, fields):
            return 'json_array(' + ','.join(row + '.' + _quote(c) for c in fields) + ')'
        for operation in ('INSERT', 'UPDATE', 'DELETE'):
            row = 'NEW' if operation == 'INSERT' else 'OLD'
            key = array(row, pk)
            condition = f"genesis_pool_write_allowed('{table}',{key},'{operation}')=0"
            if operation == 'INSERT':
                match = ' AND '.join(f'{_quote(c)}=NEW.{_quote(c)}' for c in pk)
                condition += f' OR EXISTS(SELECT 1 FROM {q} WHERE {match})'
            if operation == 'UPDATE':
                condition += f' OR {array("OLD", pk)}!={array("NEW", pk)}'
            con.execute(f'''CREATE TRIGGER "genesis_pool_{table}_{operation.lower()}"
                BEFORE {operation} ON {q} WHEN {condition}
                BEGIN SELECT RAISE(ABORT,'QUESTION_POOL_USER_ACTION_REQUIRED'); END''')
            before = 'NULL' if operation == 'INSERT' else array('OLD', columns)
            after = 'NULL' if operation == 'DELETE' else array('NEW', columns)
            asset_sql = ''
            if operation == 'DELETE':
                paths = {'questions': ('raw_crop_path', 'display_image_path'),
                         'crop_sessions': ('raw_crop_path', 'display_image_path'),
                         'source_documents': ('stored_path',)}.get(table, ())
                for column in paths:
                    if column in columns:
                        asset_sql += f'''INSERT INTO pool_asset_deletions(asset_key,actor,action)
                            SELECT 'DATA/'||replace(OLD.{_quote(column)},char(92),'/'),genesis_pool_actor(),genesis_pool_action()
                            WHERE OLD.{_quote(column)} IS NOT NULL AND OLD.{_quote(column)}!='';'''
            con.execute(f'''CREATE TRIGGER "genesis_pool_{table}_{operation.lower()}_audit"
                AFTER {operation} ON {q} BEGIN
                INSERT INTO pool_user_changes(table_name,row_key,before_json,after_json,actor,action)
                VALUES('{table}',{key},{before},{after},genesis_pool_actor(),genesis_pool_action());
                {asset_sql} END''')


def fingerprint(con):
    # Keep the deployed canonical hash: a permission upgrade is not a content change.
    tables = {}
    names = sorted(r[0] for r in con.execute("select name from sqlite_master where type='table'"))
    for table in names:
        if not protected_table(table):
            continue
        q = _quote(table)
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
    for table, in con.execute("select name from sqlite_master where type='table'").fetchall():
        if not protected_table(table):
            continue
        columns, pk = _schema(con, table)
        result[table] = {}
        for row in con.execute(f'select * from {_quote(table)}'):
            values = dict(zip(columns, row))
            key = json.dumps([values[c] for c in pk], ensure_ascii=False, separators=(',', ':'))
            result[table][key] = tuple(row)
    return result


def journal_seq(con):
    try:
        return con.execute('select coalesce(max(seq),0) from pool_user_changes').fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def assert_preserved(before, con, after_seq=None):
    expected = {table: dict(rows) for table, rows in before.items()}
    if after_seq is not None:
        try:
            changes = con.execute('''select table_name,row_key,before_json,after_json,actor,action
                from pool_user_changes where seq>? order by seq''', (after_seq,))
        except sqlite3.OperationalError:
            changes = []
        for table, key, old, new, actor, action in changes:
            if not actor or not question_write_route(action.split(' ', 1)[0], action.split(' ', 1)[-1]):
                raise RuntimeError('QUESTION_POOL_UNAUTHORIZED_JOURNAL')
            old = tuple(json.loads(old)) if old is not None else None
            new = tuple(json.loads(new)) if new is not None else None
            rows = expected.setdefault(table, {})
            if rows.get(key) != old:
                raise RuntimeError('QUESTION_POOL_JOURNAL_CHAIN_MISMATCH')
            if new is None:
                rows.pop(key, None)
            else:
                rows[key] = new
    current = immutable_rows(con)
    if {t:r for t,r in current.items() if r} != {t:r for t,r in expected.items() if r}:
        raise RuntimeError('QUESTION_POOL_UNAUTHORIZED_CHANGE: content differs from user audit trail')


def deleted_assets(con):
    try:
        return {r[0] for r in con.execute('select asset_key from pool_asset_deletions')}
    except sqlite3.OperationalError:
        return set()
