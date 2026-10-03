"""Local SQLite and files, with explicit R2 snapshots (no FUSE)."""
from __future__ import annotations

import concurrent.futures
import hashlib
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tempfile
import threading
import time
import uuid
import question_pool_policy as pool_policy

ROOT = Path(os.environ.get('GENESIS_DATA_DIR', '/app/DATA'))
MARKER = 'GENESIS_LOCAL_SQLITE_R2_V1'
_client = None
_bucket = None
_known = {}
_stats = {}
_lock = threading.Lock()
_stop = threading.Event()
_wake = threading.Event()
_thread = None
_pool_etag = None
_pool_revision = None
_pool_rows = {}
_pool_pending = False
_locked_assets = {}
_journal_seq = 0
_asset_deletions = set()
_user_requests = 0
OPERATIONS_KEY = '_runtime/operations.db'
BACKGROUND_SYNC_INTERVAL = 30
_status = {'mode': 'local-r2', 'restored': False, 'last_sync': None, 'last_error': None,
           'boot_id': uuid.uuid4().hex, 'background_sync_interval': BACKGROUND_SYNC_INTERVAL}


def _safe_path(key):
    relative = PurePosixPath(key).relative_to('DATA')
    if '..' in relative.parts or '\\' in str(relative):
        raise ValueError('Invalid storage path')
    path = ROOT.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Storage path escapes DATA')
    return path


def _digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _signature(path):
    files = [path, Path(str(path) + '-wal')] if path.suffix == '.db' else [path]
    result = []
    for file in files:
        try:
            stat = file.stat()
            result.append((stat.st_size, stat.st_mtime_ns))
        except FileNotFoundError:
            result.append(None)
    return tuple(result)


def bootstrap():
    global _client, _bucket, _pool_etag, _pool_revision, _pool_rows, _locked_assets, _journal_seq, _asset_deletions
    ROOT.mkdir(parents=True, exist_ok=True)
    if ROOT.is_symlink():
        raise RuntimeError('SQLite DATA must be on a local filesystem')
    if os.getenv('GENESIS_STORAGE_MODE') == 'local':
        _status.update(mode='local-test', restored=True)
        return
    import sys
    sys.path.insert(0, '/app/APP/backend/_vendor')
    import boto3
    from botocore.config import Config
    account = os.environ['R2_ACCOUNT_ID']
    _bucket = os.environ['R2_BUCKET_NAME']
    _client = boto3.client('s3', endpoint_url=f'https://{account}.r2.cloudflarestorage.com',
        region_name='auto', aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        config=Config(connect_timeout=4, read_timeout=12, retries={'max_attempts': 1},
                      max_pool_connections=12))
    # Authentication must succeed before the app can create a new empty DB.
    objects = []
    for page in _client.get_paginator('list_objects_v2').paginate(Bucket=_bucket, Prefix='DATA/'):
        objects.extend(page.get('Contents', []))
    primary = next((obj for obj in objects if obj['Key'] == 'DATA/genesis.db'), None)
    if primary is None or not primary.get('Size'):
        raise RuntimeError('Authoritative question database missing; refusing empty pool')
    _pool_etag = primary['ETag']

    def restore(obj):
        key = obj['Key']
        if key.endswith('/') or key.endswith('-shm'):
            return
        path = _safe_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Keep a server-side recovery copy before modifying authoritative objects.
        recovery_key = '_recovery/20260930/' + key
        try:
            _client.head_object(Bucket=_bucket, Key=recovery_key)
        except Exception as error:
            code = getattr(error, 'response', {}).get('Error', {}).get('Code')
            if code not in {'404', 'NoSuchKey', 'NotFound'}:
                raise
            _client.copy_object(Bucket=_bucket, Key=recovery_key,
                                CopySource={'Bucket': _bucket, 'Key': key})
        response = _client.get_object(Bucket=_bucket, Key=key)
        temporary = path.with_name(path.name + '.restoring')
        with temporary.open('wb') as destination:
            for chunk in response['Body'].iter_chunks(1024 * 1024):
                destination.write(chunk)
        response['Body'].close()
        os.replace(temporary, path)
        if not key.endswith('-wal'):
            _known[key] = _digest(path)

    # Read the authoritative user deletion intents before restoring any assets.
    restore(primary)
    con = sqlite3.connect(ROOT / 'genesis.db')
    try:
        _asset_deletions = pool_policy.deleted_assets(con) - _referenced_assets(con, include_drafts=True)
    finally:
        con.close()
    for obj in objects:
        if obj['Key'] in _asset_deletions:
            _known[obj['Key']] = obj['ETag']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(restore, [obj for obj in objects if obj['Key'] != primary['Key']
                                   and obj['Key'] not in _asset_deletions]))
    for db in ROOT.rglob('*.db'):
        # Merge any restored WAL into a self-contained, validated database.
        source = sqlite3.connect(db, timeout=10)
        try:
            if source.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise RuntimeError('Stored database failed SQLite integrity check')
            temp = db.with_name(db.name + '.recovered')
            destination = sqlite3.connect(temp)
            try:
                source.backup(destination)
            finally:
                destination.close()
        finally:
            source.close()
        for suffix in ('-wal', '-shm'):
            Path(str(db) + suffix).unlink(missing_ok=True)
        os.replace(temp, db)
    con = sqlite3.connect(ROOT / 'genesis.db')
    try:
        _pool_revision = pool_policy.fingerprint(con)['sha256']
        _pool_rows = pool_policy.immutable_rows(con)
        _journal_seq = pool_policy.journal_seq(con)
        keys = _referenced_assets(con)
    finally:
        con.close()
    _locked_assets = {key: digest for key, digest in _known.items() if key in keys}
    _restore_operations()
    _status['restored'] = True
    print(MARKER, 'restored', len(objects), 'R2 objects', flush=True)


def _referenced_assets(con, include_drafts=False):
    keys = set()
    for table, columns in [('questions', ('raw_crop_path', 'display_image_path')),
                            ('crop_sessions', ('raw_crop_path', 'display_image_path')),
                            ('source_documents', ('stored_path',))]:
        try:
            condition = " where status='FINALIZED'" if table == 'crop_sessions' and not include_drafts else ''
            rows = con.execute(f"select {','.join(columns)} from {table}{condition}")
            for row in rows:
                for value in row:
                    value = str(value or '')
                    if value and not Path(value).is_absolute():
                        keys.add('DATA/' + value.replace('\\', '/'))
        except sqlite3.OperationalError:
            pass
    return keys


def _restore_operations():
    """Restore sessions/coaching separately; never import their Question Studio rows."""
    try:
        response = _client.get_object(Bucket=_bucket, Key=OPERATIONS_KEY)
    except Exception as error:
        code = getattr(error, 'response', {}).get('Error', {}).get('Code')
        if code in {'404', 'NoSuchKey', 'NotFound'}:
            return
        raise
    fd, name = tempfile.mkstemp(prefix='genesis-operations-', suffix='.db')
    os.close(fd)
    temp = Path(name)
    try:
        with temp.open('wb') as stream:
            for chunk in response['Body'].iter_chunks(1024 * 1024):
                stream.write(chunk)
        response['Body'].close()
        source = sqlite3.connect(temp)
        target = sqlite3.connect(ROOT / 'genesis.db')
        try:
            if source.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise RuntimeError('Operational database failed integrity check')
            target.execute('PRAGMA foreign_keys=OFF')
            for table, sql in source.execute("select name,sql from sqlite_master where type='table'"):
                if table.startswith('sqlite_') or pool_policy.protected_table(table) or table in pool_policy.JOURNAL_TABLES:
                    continue
                q = '"' + table.replace('"', '""') + '"'
                if not target.execute('select 1 from sqlite_master where name=?', (table,)).fetchone():
                    target.execute(sql)
                source_columns = [r[1] for r in source.execute(f'pragma table_info({q})')]
                target_columns = {r[1] for r in target.execute(f'pragma table_info({q})')}
                columns = [name for name in source_columns if name in target_columns]
                cols = ','.join('"' + name.replace('"', '""') + '"' for name in columns)
                target.execute(f'DELETE FROM {q}')
                target.executemany(f'INSERT INTO {q}({cols}) VALUES({",".join("?" for _ in columns)})',
                                   source.execute(f'SELECT {cols} FROM {q}'))
            pool_policy.assert_preserved(_pool_rows, target)
            assert pool_policy.fingerprint(target)['sha256'] == _pool_revision
            target.commit()
        finally:
            source.close()
            target.close()
    finally:
        temp.unlink(missing_ok=True)


def _upload_database(path, key, pool_write=False):
    global _pool_etag, _pool_revision, _pool_rows, _pool_pending, _locked_assets, _journal_seq, _asset_deletions
    if path.name == 'genesis.db' and _user_requests and not pool_write:
        return
    fd, name = tempfile.mkstemp(prefix='genesis-r2-', suffix='.db')
    os.close(fd)
    temp = Path(name)
    try:
        deadline = time.monotonic() + 10
        def progress(status, remaining, total):
            if time.monotonic() > deadline:
                raise TimeoutError('SQLite snapshot exceeded its time limit')
        source = sqlite3.connect(path, timeout=5)
        destination = sqlite3.connect(temp)
        try:
            source.backup(destination, pages=256, progress=progress, sleep=0.02)
            if path.name == 'genesis.db':
                pool_policy.assert_preserved(_pool_rows, destination, after_seq=_journal_seq)
                revision = pool_policy.fingerprint(destination)['sha256']
                rows = pool_policy.immutable_rows(destination)
                assets = _referenced_assets(destination)
                seq = pool_policy.journal_seq(destination)
                deletions = pool_policy.deleted_assets(destination) - _referenced_assets(destination, include_drafts=True)
        finally:
            destination.close()
            source.close()
        digest = _digest(temp)
        if path.name == 'genesis.db':
            if _known.get(OPERATIONS_KEY) != digest:
                _client.upload_file(str(temp), _bucket, OPERATIONS_KEY,
                                    ExtraArgs={'ContentType': 'application/vnd.sqlite3'})
                _known[OPERATIONS_KEY] = digest
            if revision != _pool_revision or seq > _journal_seq:
                # A committed SQLite audit entry is proof of an earlier explicit user request.
                _pool_pending = _pool_pending or (seq > _journal_seq)
                if not _pool_pending:
                    # Session/startup/coaching tasks cannot publish question content.
                    return
                for attempt in range(2):
                    try:
                        with temp.open('rb') as stream:
                            result = _client.put_object(Bucket=_bucket, Key=key, Body=stream,
                                ContentType='application/vnd.sqlite3', IfMatch=_pool_etag,
                                Metadata={'pool-revision': revision, 'policy': pool_policy.MARKER})
                        break
                    except Exception as error:
                        code = getattr(error, 'response', {}).get('Error', {}).get('Code')
                        if code in {'412', 'PreconditionFailed', 'ConditionalRequestConflict'}:
                            if attempt == 0:
                                _refresh_primary_etag(key)
                                continue
                            raise RuntimeError('CENTRAL_POOL_CONFLICT: stale snapshot refused') from error
                        raise
                _pool_etag = result['ETag']
                _pool_revision = revision
                _pool_rows = rows
                _journal_seq = seq
                _asset_deletions = deletions
                _known[key] = digest
                _locked_assets = {asset: _known[asset] for asset in assets if asset in _known}
                _pool_pending = False
                # Immutable, content-addressed recovery history; never replace older snapshots.
                history = f'_snapshots/question-pool/{revision}.db'
                try:
                    with temp.open('rb') as stream:
                        _client.put_object(Bucket=_bucket, Key=history, Body=stream,
                                           ContentType='application/vnd.sqlite3', IfNoneMatch='*')
                except Exception as error:
                    code = getattr(error, 'response', {}).get('Error', {}).get('Code')
                    if code not in {'412', 'PreconditionFailed'}:
                        print(MARKER, 'history_copy_pending', type(error).__name__, flush=True)
            return
        if _known.get(key) != digest:
            _client.upload_file(str(temp), _bucket, key,
                                ExtraArgs={'ContentType': 'application/vnd.sqlite3'})
            _known[key] = digest
            # A complete SQLite snapshot must not be paired with a stale WAL.
            _client.delete_object(Bucket=_bucket, Key=key + '-wal')
            _client.delete_object(Bucket=_bucket, Key=key + '-shm')
    finally:
        temp.unlink(missing_ok=True)


def _refresh_primary_etag(key):
    """An old container may write sessions during rollout; accept only identical pool rows."""
    global _pool_etag
    response = _client.get_object(Bucket=_bucket, Key=key)
    fd, name = tempfile.mkstemp(prefix='genesis-central-check-', suffix='.db')
    os.close(fd)
    temp = Path(name)
    try:
        with temp.open('wb') as stream:
            for chunk in response['Body'].iter_chunks(1024 * 1024):
                stream.write(chunk)
        response['Body'].close()
        con = sqlite3.connect(temp)
        try:
            if pool_policy.fingerprint(con)['sha256'] != _pool_revision:
                raise RuntimeError('CENTRAL_POOL_CONFLICT: another question revision exists')
        finally:
            con.close()
        _pool_etag = response['ETag']
    finally:
        temp.unlink(missing_ok=True)


def sync_once(pool_write=False):
    global _pool_revision
    if _client is None:
        # Disposable local mode uses the same committed user tombstones and revision
        # contract, without touching any remote credentials or production objects.
        if os.getenv('GENESIS_STORAGE_MODE') == 'local' and (ROOT / 'genesis.db').is_file():
            with _lock:
                con = sqlite3.connect(ROOT / 'genesis.db')
                try:
                    keys = pool_policy.deleted_assets(con) - _referenced_assets(con, include_drafts=True)
                    _pool_revision = pool_policy.fingerprint(con)['sha256']
                finally:
                    con.close()
                for key in keys:
                    if key.startswith(('DATA/RawCrops/', 'DATA/DisplayImages/', 'DATA/Sources/')):
                        _safe_path(key).unlink(missing_ok=True)
                _status.update(last_sync=int(time.time()), last_error=None)
        return
    with _lock:
        for key in _locked_assets:
            path = _safe_path(key)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                response = _client.get_object(Bucket=_bucket, Key=key)
                with path.open('wb') as stream:
                    for chunk in response['Body'].iter_chunks(1024 * 1024):
                        stream.write(chunk)
                response['Body'].close()
        seen = set()
        # Upload new assets first; publish their DB references only after assets are durable.
        for path in sorted(ROOT.rglob('*'), key=lambda p: (p.suffix == '.db', str(p))):
            if not path.is_file() or path.is_symlink():
                continue
            if path.name.endswith(('-wal', '-shm', '.restoring', '.recovered', '.uploading')):
                continue
            key = 'DATA/' + path.relative_to(ROOT).as_posix()
            if path.name == 'genesis.db' and _user_requests and not pool_write:
                continue
            if key in _asset_deletions:
                continue
            seen.add(key)
            signature = _signature(path)
            if _stats.get(key) == signature and not (path.name == 'genesis.db' and (pool_write or _pool_pending)):
                continue
            if path.suffix == '.db':
                _upload_database(path, key, pool_write=pool_write)
            else:
                try:
                    digest = _digest(path)
                    if _known.get(key) != digest:
                        if key in _locked_assets:
                            raise RuntimeError('QUESTION_POOL_IMMUTABLE: protected asset rewrite refused')
                        if key.startswith(('DATA/DisplayImages/', 'DATA/RawCrops/', 'DATA/Sources/')) and key not in _known:
                            with path.open('rb') as stream:
                                _client.put_object(Bucket=_bucket, Key=key, Body=stream, IfNoneMatch='*')
                        else:
                            _client.upload_file(str(path), _bucket, key)
                        _known[key] = digest
                except FileNotFoundError:
                    seen.discard(key)
            _stats[key] = signature
        # Only durable, explicit user tombstones authorize physical deletion. This retry
        # is safe after a restart; an arbitrary missing local file never creates an intent.
        for key in _asset_deletions:
            if not key.startswith(('DATA/RawCrops/', 'DATA/DisplayImages/', 'DATA/Sources/')):
                raise RuntimeError('Invalid user asset deletion path')
            _safe_path(key).unlink(missing_ok=True)
            if key in _known:
                _client.delete_object(Bucket=_bucket, Key=key)
                _known.pop(key, None)
                _stats.pop(key, None)
        _status.update(last_sync=int(time.time()), last_error=None)


def _run():
    first = True
    while not _stop.is_set():
        if first:
            first = False
        else:
            _wake.wait(BACKGROUND_SYNC_INTERVAL)
            _wake.clear()
            if _stop.is_set():
                break
        try:
            sync_once()
        except Exception as error:
            code = getattr(error, 'response', {}).get('Error', {}).get('Code')
            _status['last_error'] = code or type(error).__name__
            print(MARKER, 'sync_error', _status['last_error'], flush=True)


def start():
    global _thread
    if _thread is None:
        _thread = threading.Thread(target=_run, name='genesis-r2-sync', daemon=True)
        _thread.start()


def changed():
    _wake.set()


def user_request_started():
    global _user_requests
    _user_requests += 1


def user_request_finished():
    global _user_requests
    _user_requests -= 1
    # Successful user mutations are already synchronously persisted by middleware.
    # Do not immediately rescan the whole DATA tree a second time.


def persistence_failed(error):
    _status['last_error'] = type(error).__name__
    # Failed persistence must retry without waiting for the safety interval.
    _wake.set()


def stop():
    _stop.set()
    _wake.set()
    if _thread is not None:
        _thread.join(timeout=20)
    sync_once()


def status():
    return {**_status, 'pool_policy': pool_policy.MARKER, 'pool_revision': _pool_revision,
            'pool_pending': _pool_pending}


def pool_status():
    return {'revision': _pool_revision, 'pending': _pool_pending,
            'durable': _status['last_error'] is None, 'policy': pool_policy.MARKER,
            'existing_content_locked': False, 'user_action_required': True}


if __name__ == '__main__':
    import sys
    sys.modules['runtime_storage'] = sys.modules[__name__]
    bootstrap()
    import uvicorn
    uvicorn.run('app:app', host='0.0.0.0', port=8000, timeout_graceful_shutdown=25)
