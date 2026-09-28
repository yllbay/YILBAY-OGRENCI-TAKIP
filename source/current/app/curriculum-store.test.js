const assert=require("assert");
const fs=require("fs"),os=require("os"),path=require("path");
const {createCurriculumStore}=require("./curriculum-store");

const dir=fs.mkdtempSync(path.join(os.tmpdir(),"genesis-curriculum-"));
try{
  const store=createCurriculumStore(dir);

  let r=store.addPath("Matematik","Fonksiyonlar","Fonksiyon Kavramı",1);
  assert.ok(r.courseId&&r.unitId&&r.topicId);

  store.addPath("Matematik","Fonksiyonlar","Bileşke Fonksiyon",2);
  store.addPath("Fizik","Hareket","Doğrusal Hareket",1);

  let tree=store.tree(false);
  assert.equal(tree.length,2);
  assert.equal(tree[0].name,"Matematik");
  assert.equal(tree[0].units[0].topics.length,2);

  const before=JSON.stringify(store.tree(true));
  store.addPath("matematik","fonksiyonlar","Bileşke Fonksiyon",2);
  assert.equal(JSON.stringify(store.tree(true)),before);

  const topicId=tree[0].units[0].topics[0].id;
  store.update("topic",topicId,{name:"Fonksiyon Kavramı ve Tanımı",sortOrder:5});
  tree=store.tree(false);
  assert.equal(tree[0].units[0].topics.find(x=>x.id===topicId).name,"Fonksiyon Kavramı ve Tanımı");

  const unitId=tree[0].units[0].id;
  store.update("unit",unitId,{isActive:false});
  assert.equal(store.tree(false)[0].units.length,0);
  assert.equal(store.tree(true)[0].units.length,1);

  const imported=store.importRows([
    {course:"Kimya",unit:"Atom",topic:"Atom Modelleri",sortOrder:1},
    {course:"Kimya",unit:"Atom",topic:"Periyodik Sistem",sortOrder:2}
  ]);
  assert.equal(imported.processed,2);
  assert.ok(store.legacy().Kimya.Atom.includes("Atom Modelleri"));

  const saved=JSON.parse(fs.readFileSync(path.join(dir,"curriculum.json"),"utf8"));
  assert.equal(saved.version,1);
  console.log("CURRICULUM_STORE_TEST_OK");
}finally{
  fs.rmSync(dir,{recursive:true,force:true});
}
