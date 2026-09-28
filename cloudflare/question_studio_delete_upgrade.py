from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"app.py"
src=path.read_text(encoding="utf-8")
mark="GENESIS_QUESTION_STUDIO_DELETE_UPGRADE_V1"
if mark in src:
    raise SystemExit(0)

old='''            fp=abs_data(rel)
            if fp.exists():
                fp.unlink()
            local_deleted.append(rel)
'''
new='''            # GENESIS_QUESTION_STUDIO_DELETE_UPGRADE_V1
            fp=abs_data(rel)
            if fp.exists():
                fp.unlink()
            if os.environ.get("R2_ACCOUNT_ID"):\n                r2_remove("DATA/"+str(rel).replace("\\\\","/"))
            local_deleted.append(rel)
'''
if old not in src:
    raise SystemExit("installed delete function shape changed")
path.write_text(src.replace(old,new,1),encoding="utf-8")
