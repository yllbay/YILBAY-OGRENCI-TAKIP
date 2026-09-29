from __future__ import annotations
import os, shutil
from pathlib import Path

def _root():
    return Path(os.environ.get("GENESIS_R2_MOUNT","/mnt/r2"))

def _path(key):
    clean=str(key or "").replace("\\","/").lstrip("/")
    if ".." in Path(clean).parts:
        raise ValueError("invalid R2 key")
    return _root()/clean

def put_file(key,path,content_type="application/octet-stream"):
    src=Path(path); dst=_path(key)
    dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+".uploading")
    shutil.copyfile(src,tmp)
    os.replace(tmp,dst)
    return True

def get_file(key,path):
    src=_path(key)
    if not src.exists():
        return False
    dst=Path(path); dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    return True

def head(key):
    p=_path(key)
    if not p.exists():
        return None
    st=p.stat()
    return {"size":int(st.st_size),"etag":None}

def delete(key):
    p=_path(key)
    try:p.unlink()
    except FileNotFoundError:pass
    return True

def delete_prefix(prefix):
    root=_path(prefix)
    deleted=[]
    if root.is_file():
        root.unlink(); return [str(prefix)]
    if not root.exists():
        return deleted
    for p in sorted(root.rglob("*"),reverse=True):
        if p.is_file():
            deleted.append(str(p.relative_to(_root())).replace("\\","/"))
            p.unlink()
        elif p.is_dir():
            try:p.rmdir()
            except OSError:pass
    try:root.rmdir()
    except OSError:pass
    return deleted

def restore_primary_db(path):
    return get_file("DATA/genesis.db",path)

def persist_primary_db(path):
    return put_file("DATA/genesis.db",path,"application/vnd.sqlite3")
