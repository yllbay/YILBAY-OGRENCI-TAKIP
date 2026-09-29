from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
db_path=root/"backend"/"db.py"
app_path=root/"backend"/"app.py"
db=db_path.read_text(encoding="utf-8")
app=app_path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V2"

if MARK in db and MARK in app:
    print("Question Studio immutable guard V2 already installed")
    raise SystemExit(0)

if "GENESIS_QUESTION_STUDIO_HARD_LOCK_V1" not in db or "GENESIS_QUESTION_POOL_GUARD_V1" not in app:
    raise SystemExit("Required V1 guards missing; refusing unsafe V2 patch")

# Expand protected-table classification to cover all Question Studio-owned data.
old_func='''def _question_studio_protected_table(name):
    n=str(name or "").lower()
    return (
        "question" in n
        or "topic" in n
        or n=="exams"
        or n.startswith("exam_")
        or n=="tests"
        or n.startswith("test_")
    )
'''
new_func='''def _question_studio_protected_table(name):
    n=str(name or "").lower()
    return any(token in n for token in (
        "question",
        "topic",
        "exam",
        "test",
        "folder",
        "crop",
        "source",
    ))
'''
if old_func in db:
    db=db.replace(old_func,new_func,1)
elif new_func not in db:
    raise SystemExit("protected-table classifier changed; refusing unsafe V2 patch")

# Startup storage hygiene is permanently disabled for production data.
# Explicit user deletion tombstones remain a separate, user-authorized path.
for fn in (
    "purge_stale_prepared_on_startup",
    "purge_finalized_working_files_on_startup",
    "purge_transient_source_files_on_startup",
):
    old=f'''def {fn}():
    if os.environ.get("GENESIS_STARTUP_STORAGE_MAINTENANCE","0")!="1":
        return
'''
    new=f'''def {fn}():
    # GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V2
    # Never mutate Question Studio storage during deploy/restart/startup.
    return
'''
    if old in app:
        app=app.replace(old,new,1)
    elif new not in app:
        raise SystemExit(f"{fn} shape changed; refusing unsafe V2 patch")

if MARK not in db:
    db += "\n# GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V2\n"
if MARK not in app:
    app += "\n# GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V2\n"

db_path.write_text(db,encoding="utf-8")
app_path.write_text(app,encoding="utf-8")

out_db=db_path.read_text(encoding="utf-8")
out_app=app_path.read_text(encoding="utf-8")
assert MARK in out_db and MARK in out_app
assert '"folder"' in out_db and '"crop"' in out_db and '"source"' in out_db
for fn in (
    "purge_stale_prepared_on_startup",
    "purge_finalized_working_files_on_startup",
    "purge_transient_source_files_on_startup",
):
    pos=out_app.index("def "+fn+"():")
    block=out_app[pos:pos+260]
    assert "Never mutate Question Studio storage" in block
print("GENESIS Question Studio immutable guard V2 installed")
