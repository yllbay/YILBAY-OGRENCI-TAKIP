from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"app.py"
src=path.read_text(encoding="utf-8")
mark="GENESIS_QUESTION_STUDIO_R2_IMAGES_V1"
if mark in src:
    raise SystemExit(0)

anchor='from db import init_db, connect, log_event, audit, ROOT, DATA, DB, SCHEMA_VERSION, format_folder_name, CURRENT_DB, CURRENT_INSTITUTION_ID'
if anchor not in src:
    raise SystemExit("db import anchor changed")
src=src.replace(
    anchor,
    anchor+'\nfrom r2_object_store import put_file as r2_put_file, get_file as r2_get_file, remove as r2_remove, head as r2_head',
    1,
)

anchor='def _is_transient_source(src):'
helper='''# GENESIS_QUESTION_STUDIO_R2_IMAGES_V1
def _persist_question_image(rel):
    fp=abs_data(rel)
    if not fp.is_file():
        raise RuntimeError(f"Kalıcı soru görseli bulunamadı: {rel}")
    key="DATA/"+str(rel).replace("\\\\","/")
    r2_put_file(key,fp,"image/png")
    if not r2_head(key):
        raise RuntimeError(f"R2 görsel doğrulaması başarısız: {rel}")
    return True

def _ensure_question_image_local(rel):
    fp=abs_data(rel)
    if fp.is_file():
        return fp
    key="DATA/"+str(rel).replace("\\\\","/")
    if not r2_get_file(key,fp):
        raise HTTPException(404,"Soru görseli kalıcı depoda bulunamadı.")
    return fp

'''
if anchor not in src:
    raise SystemExit("helper anchor changed")
src=src.replace(anchor,helper+anchor,1)

old='''    raw_cleanup=_purge_finalized_raw(qid,crop_id,str(r["raw_crop_path"]),str(r["display_image_path"]))
    drive=_sync_question_drive(int(qid))
'''
new='''    _persist_question_image(str(r["display_image_path"]))
    raw_cleanup=_purge_finalized_raw(qid,crop_id,str(r["raw_crop_path"]),str(r["display_image_path"]))
    drive=_sync_question_drive(int(qid))
'''
if old not in src:
    raise SystemExit("single save anchor changed")
src=src.replace(old,new,1)

old='''    raw_cleanup=[]
    for r,qid in zip(rows,saved):
        raw_cleanup.append(_purge_finalized_raw(int(qid),int(r["id"]),str(r["raw_crop_path"]),str(r["display_image_path"])))
    drive_syncs=[_sync_question_drive(int(qid)) for qid in saved]
'''
new='''    raw_cleanup=[]
    for r,qid in zip(rows,saved):
        _persist_question_image(str(r["display_image_path"]))
        raw_cleanup.append(_purge_finalized_raw(int(qid),int(r["id"]),str(r["raw_crop_path"]),str(r["display_image_path"])))
    drive_syncs=[_sync_question_drive(int(qid)) for qid in saved]
'''
if old not in src:
    raise SystemExit("batch save anchor changed")
src=src.replace(old,new,1)

old='return FileResponse(abs_data(r["display_image_path"]),media_type="image/png",headers={"Cache-Control":"no-store"})'
new='return FileResponse(_ensure_question_image_local(str(r["display_image_path"])),media_type="image/png",headers={"Cache-Control":"no-store"})'
if old not in src:
    raise SystemExit("image endpoint anchor changed")
src=src.replace(old,new,1)

path.write_text(src,encoding="utf-8")
