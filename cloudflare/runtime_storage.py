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
_status = {'mode': 'local-r2', 'restored': False, 'last_sync': None, 'last_error': None}


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
    global _client, _bucket
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

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(restore, objects))
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
    _status['restored'] = True
    print(MARKER, 'restored', len(objects), 'R2 objects', flush=True)


def _upload_database(path, key):
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
        finally:
            destination.close()
            source.close()
        digest = _digest(temp)
        if _known.get(key) != digest:
            _client.upload_file(str(temp), _bucket, key,
                                ExtraArgs={'ContentType': 'application/vnd.sqlite3'})
            _known[key] = digest
            # A complete SQLite snapshot must not be paired with a stale WAL.
            _client.delete_object(Bucket=_bucket, Key=key + '-wal')
            _client.delete_object(Bucket=_bucket, Key=key + '-shm')
    finally:
        temp.unlink(missing_ok=True)


def sync_once():
    if _client is None:
        return
    with _lock:
        seen = set()
        for path in sorted(ROOT.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            if path.name.endswith(('-wal', '-shm', '.restoring', '.recovered', '.uploading')):
                continue
            key = 'DATA/' + path.relative_to(ROOT).as_posix()
            seen.add(key)
            signature = _signature(path)
            if _stats.get(key) == signature:
                continue
            if path.suffix == '.db':
                _upload_database(path, key)
            else:
                try:
                    digest = _digest(path)
                    if _known.get(key) != digest:
                        _client.upload_file(str(path), _bucket, key)
                        _known[key] = digest
                except FileNotFoundError:
                    seen.discard(key)
            _stats[key] = signature
        for key in set(_known) - seen:
            _client.delete_object(Bucket=_bucket, Key=key)
            del _known[key]
            _stats.pop(key, None)
        _status.update(last_sync=int(time.time()), last_error=None)


def _run():
    while not _stop.is_set():
        try:
            sync_once()
        except Exception as error:
            code = getattr(error, 'response', {}).get('Error', {}).get('Code')
            _status['last_error'] = code or type(error).__name__
            print(MARKER, 'sync_error', _status['last_error'], flush=True)
        _wake.wait(3)
        _wake.clear()


def start():
    global _thread
    if _thread is None:
        _thread = threading.Thread(target=_run, name='genesis-r2-sync', daemon=True)
        _thread.start()


def changed():
    _wake.set()


def stop():
    _stop.set()
    _wake.set()
    if _thread is not None:
        _thread.join(timeout=20)
    sync_once()


def status():
    return dict(_status)


if __name__ == '__main__':
    import sys
    sys.modules['runtime_storage'] = sys.modules[__name__]
    bootstrap()
    import uvicorn
    uvicorn.run('app:app', host='0.0.0.0', port=8000, timeout_graceful_shutdown=25)
