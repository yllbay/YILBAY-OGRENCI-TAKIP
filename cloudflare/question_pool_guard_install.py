from pathlib import Path

ROOT = Path(__import__("os").environ.get("GENESIS_APP_ROOT", "/app/APP"))
p = ROOT / "backend" / "app.py"
src = p.read_text(encoding="utf-8")
MARK = "GENESIS_QUESTION_POOL_GUARD_V1"

if MARK in src:
    print("question pool guard already installed")
    raise SystemExit(0)

old = '''def _process_delete_tombstone(path:Path):
    d=json.loads(path.read_text(encoding="utf-8-sig"))
    qid=int(d["question_id"]);raw_rel=str(d["raw_crop_path"]);display_rel=str(d["display_image_path"])
    backups=_purge_question_from_backup_zips(qid,raw_rel,display_rel)
    drive=_purge_question_from_drive_snapshots(qid,raw_rel,display_rel)
    drive_file=drive_delete_file(d.get("drive_file_id"))
    if drive.get("status")=="PURGED" and drive_file.get("status") in {"PURGED","NOT_PRESENT"}:
        try:path.unlink()
        except Exception:pass
    else:
        d["last_attempt_at"]=dt.datetime.now(dt.timezone.utc).isoformat()
        d["drive"]=drive
        d["drive_file"]=drive_file
        path.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"backups":backups,"drive":drive,"drive_file":drive_file}
'''

new = '''# GENESIS_QUESTION_POOL_GUARD_V1
def _process_delete_tombstone(path:Path):
    """Retry an explicit user-requested question deletion until every persistent copy is gone.

    This is intentionally the only startup path allowed to delete finalized question data.
    Deploy/restart maintenance must never purge question-pool content by itself.
    """
    d=json.loads(path.read_text(encoding="utf-8-sig"))
    qid=int(d["question_id"]);raw_rel=str(d["raw_crop_path"]);display_rel=str(d["display_image_path"])

    # R2 is mounted at DATA. Treat both finalized and raw image removal as durable work:
    # if unlink fails, keep the tombstone and retry on the next backend start.
    local_deleted=[]
    local_pending=[]
    for rel in dict.fromkeys([raw_rel,display_rel]):
        try:
            fp=abs_data(rel)
            if fp.exists():
                fp.unlink()
            if "r2_remove" in globals():
                r2_remove("DATA/"+str(rel).replace("\\\\","/"))
            local_deleted.append(rel)
        except Exception as exc:
            local_pending.append({"path":rel,"reason":str(exc)[:300]})

    backups=_purge_question_from_backup_zips(qid,raw_rel,display_rel)
    drive=_purge_question_from_drive_snapshots(qid,raw_rel,display_rel)
    drive_file=drive_delete_file(d.get("drive_file_id"))

    complete=(
        not local_pending
        and drive.get("status")=="PURGED"
        and drive_file.get("status") in {"PURGED","NOT_PRESENT"}
    )
    if complete:
        try:path.unlink()
        except Exception:pass
    else:
        d["last_attempt_at"]=dt.datetime.now(dt.timezone.utc).isoformat()
        d["local_pending"]=local_pending
        d["drive"]=drive
        d["drive_file"]=drive_file
        path.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")

    return {
        "backups":backups,
        "local":{"status":"PURGED" if not local_pending else "PENDING",
                 "deleted":local_deleted,"pending":local_pending},
        "drive":drive,
        "drive_file":drive_file,
        "complete":complete,
    }
'''

if old not in src:
    raise SystemExit("delete tombstone function shape changed; refusing unsafe patch")
src = src.replace(old, new, 1)

# Deployment/restart must not perform autonomous destructive storage hygiene.
# Explicit user deletion tombstones remain enabled and are retried on startup.
repls = {
'''@app.on_event("startup")
def purge_stale_prepared_on_startup():
    try:
        result=_stale_prepared_cleanup()
''':
'''@app.on_event("startup")
def purge_stale_prepared_on_startup():
    if os.environ.get("GENESIS_STARTUP_STORAGE_MAINTENANCE","0")!="1":
        return
    try:
        result=_stale_prepared_cleanup()
''',
'''@app.on_event("startup")
def purge_finalized_working_files_on_startup():
    try:
        _purge_historical_finalized_working_files()
''':
'''@app.on_event("startup")
def purge_finalized_working_files_on_startup():
    if os.environ.get("GENESIS_STARTUP_STORAGE_MAINTENANCE","0")!="1":
        return
    try:
        _purge_historical_finalized_working_files()
''',
'''@app.on_event("startup")
def purge_transient_source_files_on_startup():
    try:
        result=_cleanup_transient_sources()
''':
'''@app.on_event("startup")
def purge_transient_source_files_on_startup():
    if os.environ.get("GENESIS_STARTUP_STORAGE_MAINTENANCE","0")!="1":
        return
    try:
        result=_cleanup_transient_sources()
'''
}
for a,b in repls.items():
    if a not in src:
        raise SystemExit("startup maintenance function shape changed; refusing unsafe patch")
    src=src.replace(a,b,1)

# Make API deletion response include the durable R2 completion state.
old_response='''        "backup_purge":purge["backups"],
        "drive":drive,
        "drive_pending":drive.get("status")!="PURGED"
'''
new_response='''        "backup_purge":purge["backups"],
        "r2":purge.get("local",{"status":"PURGED"}),
        "r2_pending":purge.get("local",{}).get("status")!="PURGED",
        "drive":drive,
        "drive_file":purge.get("drive_file"),
        "drive_pending":drive.get("status")!="PURGED" or purge.get("drive_file",{}).get("status") not in {"PURGED","NOT_PRESENT"},
        "deletion_complete":bool(purge.get("complete"))
'''
if old_response not in src:
    raise SystemExit("question delete response shape changed; refusing unsafe patch")
src=src.replace(old_response,new_response,1)

p.write_text(src,encoding="utf-8")
out=p.read_text(encoding="utf-8")
assert MARK in out
assert 'GENESIS_STARTUP_STORAGE_MAINTENANCE' in out
assert '"r2_pending"' in out
assert '"deletion_complete"' in out
print("GENESIS question pool guard install: OK")
