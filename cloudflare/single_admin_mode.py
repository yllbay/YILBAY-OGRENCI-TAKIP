from pathlib import Path

app=Path("/app/APP/backend/app.py")
src=app.read_text(encoding="utf-8")
if "GENESIS_SINGLE_ADMIN_AUTO_SESSION" not in src:
    needle='    token=request.cookies.get("genesis_session")\n    session=session_from_token(token)\n'
    replacement='''    token=request.cookies.get("genesis_session")
    session=session_from_token(token)
    auto_admin_token=None
    if not session and not path.startswith("/coaching/student/") and not path.startswith("/api/coaching/public/") and not path.startswith("/online/") and not path.startswith("/api/online/public/") and not path.startswith("/api/online/session/") and not path.startswith("/api/online/internet-test/"):
        # GENESIS_SINGLE_ADMIN_AUTO_SESSION
        auto_admin_token=create_session("ADMIN")
        session=session_from_token(auto_admin_token)
'''
    if needle not in src:
        raise SystemExit("auto-session patch point not found")
    src=src.replace(needle,replacement,1)
    needle2='''    try:
        return await call_next(request)
    finally:
'''
    replacement2='''    try:
        response=await call_next(request)
        if auto_admin_token:
            _cookie(response,auto_admin_token)
        return response
    finally:
'''
    if needle2 not in src:
        raise SystemExit("response patch point not found")
    src=src.replace(needle2,replacement2,1)
    cleanup='''\n# GENESIS_SINGLE_ADMIN_ACCOUNT_CLEANUP
def _enforce_single_admin_accounts():
    with connect(DB) as con:
        con.execute("delete from auth_sessions where role='INSTITUTION'")
        con.execute("delete from institutions")
        con.execute("insert into schema_meta(key,value) values('auth_mode','single_admin_auto_session') on conflict(key) do update set value=excluded.value")

'''
    startup='init_db()\nTRANSIENT_PDF.mkdir(parents=True,exist_ok=True)'
    if startup not in src:
        raise SystemExit("startup patch point not found")
    src=src.replace(startup,'init_db()\n'+cleanup+'_enforce_single_admin_accounts()\nTRANSIENT_PDF.mkdir(parents=True,exist_ok=True)',1)
    app.write_text(src,encoding="utf-8")
