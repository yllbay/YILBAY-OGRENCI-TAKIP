from __future__ import annotations
import os, sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent/"_vendor"))
import boto3


def _client():
    endpoint=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="auto",
        config=None,
    )


def _bucket():
    return os.environ["R2_BUCKET_NAME"]


def put_file(key,path,content_type="application/octet-stream"):
    _client().upload_file(
        str(path),
        _bucket(),
        key,
        ExtraArgs={"ContentType":content_type},
    )
    return True


def get_file(key,path):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    try:
        _client().download_file(_bucket(),key,str(p))
        return True
    except Exception as exc:
        code=getattr(exc,"response",{}).get("Error",{}).get("Code")
        if code in {"404","NoSuchKey","NotFound"}:
            return False
        raise


def head(key):
    try:
        r=_client().head_object(Bucket=_bucket(),Key=key)
        return {"size":int(r.get("ContentLength") or 0),"etag":r.get("ETag")}
    except Exception as exc:
        code=getattr(exc,"response",{}).get("Error",{}).get("Code")
        if code in {"404","NoSuchKey","NotFound"}:
            return None
        raise


def delete(key):
    _client().delete_object(Bucket=_bucket(),Key=key)
    return True


def delete_prefix(prefix):
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


def restore_primary_db(path):
    return get_file("DATA/genesis.db",path)


def persist_primary_db(path):
    return put_file("DATA/genesis.db",path,"application/vnd.sqlite3")
