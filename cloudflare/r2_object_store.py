from __future__ import annotations
import os, sys, shutil
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent/"_vendor"))
import boto3


def _have_s3_credentials():
    return bool(
        os.environ.get("R2_ACCOUNT_ID")
        and (os.environ.get("R2_ACCESS_KEY_ID") or os.environ.get("AWS_ACCESS_KEY_ID"))
        and (os.environ.get("R2_SECRET_ACCESS_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY"))
        and os.environ.get("R2_BUCKET_NAME")
    )


def _client():
    account_id=os.environ["R2_ACCOUNT_ID"]
    access_key=os.environ.get("R2_ACCESS_KEY_ID") or os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key=os.environ.get("R2_SECRET_ACCESS_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY")
    session_token=os.environ.get("R2_SESSION_TOKEN") or os.environ.get("AWS_SESSION_TOKEN")
    endpoint=f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="auto",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        config=None,
    )


def _bucket():
    return os.environ["R2_BUCKET_NAME"]


def _mount_root():
    p=Path(os.environ.get("GENESIS_R2_MOUNT","/mnt/r2"))
    if not p.exists() or not p.is_dir():
        raise RuntimeError(f"R2 mount is unavailable: {p}")
    return p


def _mount_path(key):
    clean=str(key or "").replace("\\","/").lstrip("/")
    if ".." in Path(clean).parts:
        raise ValueError("invalid R2 key")
    return _mount_root()/clean


def put_file(key,path,content_type="application/octet-stream"):
    if _have_s3_credentials():
        _client().upload_file(
            str(path),
            _bucket(),
            key,
            ExtraArgs={"ContentType":content_type},
        )
        return True
    src=Path(path); dst=_mount_path(key)
    dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+".uploading")
    shutil.copyfile(src,tmp)
    os.replace(tmp,dst)
    return True


def get_file(key,path):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    if _have_s3_credentials():
        try:
            _client().download_file(_bucket(),key,str(p))
            return True
        except Exception as exc:
            code=getattr(exc,"response",{}).get("Error",{}).get("Code")
            if code in {"404","NoSuchKey","NotFound"}:
                return False
            raise
    src=_mount_path(key)
    if not src.exists():
        return False
    tmp=p.with_name(p.name+".downloading")
    shutil.copyfile(src,tmp)
    os.replace(tmp,p)
    return True


def head(key):
    if _have_s3_credentials():
        try:
            r=_client().head_object(Bucket=_bucket(),Key=key)
            return {"size":int(r.get("ContentLength") or 0),"etag":r.get("ETag")}
        except Exception as exc:
            code=getattr(exc,"response",{}).get("Error",{}).get("Code")
            if code in {"404","NoSuchKey","NotFound"}:
                return None
            raise
    p=_mount_path(key)
    if not p.exists():
        return None
    st=p.stat()
    return {"size":int(st.st_size),"etag":None}


def delete(key):
    if _have_s3_credentials():
        _client().delete_object(Bucket=_bucket(),Key=key)
        return True
    p=_mount_path(key)
    try:
        p.unlink()
    except FileNotFoundError:
        pass
    return True


def delete_prefix(prefix):
    if _have_s3_credentials():
        c=_client()
        deleted=[]
        token=None
        while True:
            kw={"Bucket":_bucket(),"Prefix":prefix,"MaxKeys":1000}
            if token:
                kw["ContinuationToken"]=token
            r=c.list_objects_v2(**kw)
            keys=[o["Key"] for o in r.get("Contents",[])]
            if keys:
                c.delete_objects(
                    Bucket=_bucket(),
                    Delete={"Objects":[{"Key":k} for k in keys],"Quiet":True},
                )
                deleted.extend(keys)
            if not r.get("IsTruncated"):
                break
            token=r.get("NextContinuationToken")
        return deleted
    root=_mount_path(prefix)
    deleted=[]
    if root.is_file():
        root.unlink()
        return [str(prefix)]
    if not root.exists():
        return deleted
    for p in sorted(root.rglob("*"),reverse=True):
        if p.is_file():
            deleted.append(str(p.relative_to(_mount_root())).replace("\\","/"))
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
