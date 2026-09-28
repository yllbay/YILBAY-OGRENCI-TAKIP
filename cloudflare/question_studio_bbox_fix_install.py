from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"app.py"
src=path.read_text(encoding="utf-8")
mark="GENESIS_QUESTION_STUDIO_BBOX_SAVEFIX_V1"
if mark in src:
    raise SystemExit(0)

old='''    bbox,outside,diag=_find_expected_number_on_pdf_page(row,int(expected))
    if outside:
        return {"masked":False,"reason":"number_outside_crop","diagnostics":diag}
    if bbox is None:
        # Fallback to exact-token OCR on the immutable raw crop.
        bbox,raw_diag=_exact_question_number_bbox(raw,int(expected))
        diag={"page":diag,"raw":raw_diag}
'''
new='''    # GENESIS_QUESTION_STUDIO_BBOX_SAVEFIX_V1
    bbox=None; outside=False; diag={"method":"stored_crop_bbox","expected":int(expected)}
    try:
        saved=json.loads(row["source_number_bbox"] or "{}")
    except Exception:
        saved={}
    try:
        if all(saved.get(k) is not None for k in ("x0","y0","x1","y1")):
            bbox=(int(round(float(saved["x0"]))),int(round(float(saved["y0"]))),
                  int(round(float(saved["x1"]))),int(round(float(saved["y1"]))))
    except Exception:
        bbox=None
    if bbox is None:
        bbox,outside,page_diag=_find_expected_number_on_pdf_page(row,int(expected))
        diag={"stored":diag,"page":page_diag}
        if outside:
            return {"masked":False,"reason":"number_outside_crop","diagnostics":diag}
        if bbox is None:
            bbox,raw_diag=_exact_question_number_bbox(raw,int(expected))
            diag={"stored":diag,"raw":raw_diag}
'''
if old not in src:
    raise SystemExit("mask function shape changed")
path.write_text(src.replace(old,new,1),encoding="utf-8")
