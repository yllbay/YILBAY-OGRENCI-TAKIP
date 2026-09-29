from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"app.py"
src=path.read_text(encoding="utf-8")
mark="GENESIS_QUESTION_STUDIO_DELETE_UPGRADE_V1"
if mark in src:
    raise SystemExit(0)

# Newer question-pool guards may already contain the durable R2 removal.
# In that case only stamp the compatibility marker; never rewrite working code.
if 'r2_remove("DATA/"+str(rel).replace(' in src:
    path.write_text(src+"\n# "+mark+"\n",encoding="utf-8")
    print("Question Studio delete upgrade already functionally present")
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
            if os.environ.get("R2_ACCOUNT_ID"):
                r2_remove("DATA/"+str(rel).replace("\\\\","/"))
            local_deleted.append(rel)
'''
if old not in src:
    raise SystemExit("installed delete function shape changed; refusing unsafe rewrite")
path.write_text(src.replace(old,new,1),encoding="utf-8")
