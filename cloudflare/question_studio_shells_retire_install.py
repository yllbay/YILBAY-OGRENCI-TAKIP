from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"app.py"
src=path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_SHELLS_V1"
RETIRE="GENESIS_QUESTION_STUDIO_SHELLS_RETIRED_V1"

if RETIRE in src:
    print("legacy Question Studio shell seeding already retired")
    raise SystemExit(0)

if MARK in src:
    block='''# GENESIS_QUESTION_STUDIO_SHELLS_V1
with connect() as con:
    if int(con.execute("select count(*) from topics").fetchone()[0])==0:
        con.execute("insert into topics(id,parent_id,name,description,content,sort_order) values(5,null,'TYT MATEMATİK','','',0)")
        con.execute("insert into topics(id,parent_id,name,description,content,sort_order) values(7,5,'Temel Kavramlar','','',0)")
        con.execute("insert into topics(id,parent_id,name,description,content,sort_order) values(8,5,'Tek Çift Sayı','','',1)")
        con.execute("insert into topics(id,parent_id,name,description,content,sort_order) values(9,5,'Asal Çarpanlara Ayırma','','',2)")
        con.execute("insert into topics(id,parent_id,name,description,content,sort_order) values(10,null,'TYTFİZİK','','',1)")
    if int(con.execute("select count(*) from test_classes").fetchone()[0])==0:
        con.execute("insert into test_classes(id,parent_id,name,sort_order) values(2,null,'4.SINIF',0)")
    if int(con.execute("select count(*) from exams").fetchone()[0])==0:
        con.execute("insert into exams(id,class_id,name,sort_order,settings_json,auto_generated,auto_build_json) values(10,2,'TARAMA 1',0,'{}',0,'{}')")
        con.execute("insert into exams(id,class_id,name,sort_order,settings_json,auto_generated,auto_build_json) values(11,2,'TARAMA 2',1,'{}',0,'{}')")
'''
    if block not in src:
        raise SystemExit("legacy Question Studio shell block shape changed; refusing unsafe removal")
    src=src.replace(block,"# "+RETIRE+"\n# Legacy automatic Question Studio seeding removed.\n",1)
else:
    src += "\n# "+RETIRE+"\n"

path.write_text(src,encoding="utf-8")
out=path.read_text(encoding="utf-8")
assert RETIRE in out
assert "insert into topics(id,parent_id,name" not in out
assert "insert into test_classes(id,parent_id,name" not in out
print("legacy Question Studio automatic shell seeding retired")
