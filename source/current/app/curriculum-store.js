const fs=require("fs"),path=require("path");

function cleanName(value){
  const name=String(value||"").trim().replace(/\s+/g," ");
  if(!name) throw new Error("Ad boş olamaz");
  if(name.length>200) throw new Error("Ad 200 karakterden uzun olamaz");
  return name;
}
function sortRows(a,b){return Number(a.sortOrder||0)-Number(b.sortOrder||0)||Number(a.id)-Number(b.id)}
function blank(){return {version:1,nextId:1,courses:[]}}
function createCurriculumStore(runtimeDir){
  const file=path.join(runtimeDir,"curriculum.json");
  const temp=file+".tmp";

  function load(){
    try{
      const x=JSON.parse(fs.readFileSync(file,"utf8"));
      if(!x||!Array.isArray(x.courses)) return blank();
      x.version=1;x.nextId=Math.max(1,Number(x.nextId)||1);
      for(const c of x.courses){
        c.id=Number(c.id);c.name=cleanName(c.name);c.sortOrder=Number(c.sortOrder)||0;c.isActive=c.isActive!==false;c.units=Array.isArray(c.units)?c.units:[];
        for(const u of c.units){
          u.id=Number(u.id);u.name=cleanName(u.name);u.sortOrder=Number(u.sortOrder)||0;u.isActive=u.isActive!==false;u.topics=Array.isArray(u.topics)?u.topics:[];
          for(const t of u.topics){t.id=Number(t.id);t.name=cleanName(t.name);t.sortOrder=Number(t.sortOrder)||0;t.isActive=t.isActive!==false}
        }
      }
      const ids=[];for(const c of x.courses){ids.push(c.id);for(const u of c.units){ids.push(u.id);for(const t of u.topics)ids.push(t.id)}}
      x.nextId=Math.max(x.nextId,...ids.map(n=>Number(n)||0),0)+1;
      return x;
    }catch{return blank()}
  }

  function save(db){
    fs.mkdirSync(runtimeDir,{recursive:true});
    fs.writeFileSync(temp,JSON.stringify(db,null,2),"utf8");
    fs.renameSync(temp,file);
  }

  function unique(list,name,ignoreId=null){
    const key=cleanName(name).toLocaleLowerCase("tr-TR");
    return !list.some(x=>Number(x.id)!==Number(ignoreId)&&cleanName(x.name).toLocaleLowerCase("tr-TR")===key);
  }

  function tree(includeInactive=false){
    const db=load();
    return db.courses
      .filter(c=>includeInactive||c.isActive)
      .sort(sortRows)
      .map(c=>({...c,units:c.units.filter(u=>includeInactive||u.isActive).sort(sortRows).map(u=>({...u,topics:u.topics.filter(t=>includeInactive||t.isActive).sort(sortRows)}))}));
  }

  function legacy(){
    const out={};
    for(const c of tree(false)){
      out[c.name]={};
      for(const u of c.units) out[c.name][u.name]=u.topics.map(t=>t.name);
    }
    return out;
  }

  function addPath(courseName,unitName,topicName,sortOrder=0){
    const db=load(),cn=cleanName(courseName),un=cleanName(unitName),tn=cleanName(topicName);
    let c=db.courses.find(x=>cleanName(x.name).toLocaleLowerCase("tr-TR")===cn.toLocaleLowerCase("tr-TR"));
    if(!c){c={id:db.nextId++,name:cn,sortOrder:0,isActive:true,units:[]};db.courses.push(c)}
    c.isActive=true;
    let u=c.units.find(x=>cleanName(x.name).toLocaleLowerCase("tr-TR")===un.toLocaleLowerCase("tr-TR"));
    if(!u){u={id:db.nextId++,name:un,sortOrder:0,isActive:true,topics:[]};c.units.push(u)}
    u.isActive=true;
    let t=u.topics.find(x=>cleanName(x.name).toLocaleLowerCase("tr-TR")===tn.toLocaleLowerCase("tr-TR"));
    if(!t){t={id:db.nextId++,name:tn,sortOrder:Number(sortOrder)||0,isActive:true};u.topics.push(t)}
    else t.isActive=true;
    save(db);
    return {courseId:c.id,unitId:u.id,topicId:t.id};
  }

  function findEntity(db,entity,id){
    id=Number(id);
    if(entity==="course"){
      const item=db.courses.find(x=>x.id===id);return item?{item,list:db.courses}:null;
    }
    for(const c of db.courses){
      if(entity==="unit"){
        const item=c.units.find(x=>x.id===id);if(item)return {item,list:c.units,parent:c};
      }else if(entity==="topic"){
        for(const u of c.units){const item=u.topics.find(x=>x.id===id);if(item)return {item,list:u.topics,parent:u,course:c}}
      }
    }
    return null;
  }

  function update(entity,id,changes={}){
    if(!["course","unit","topic"].includes(entity)) throw new Error("Geçersiz kayıt türü");
    const db=load(),found=findEntity(db,entity,id);
    if(!found) throw new Error("Kayıt bulunamadı");
    if(changes.name!==undefined){
      const next=cleanName(changes.name);
      if(!unique(found.list,next,found.item.id)) throw new Error("Bu ad aynı kapsamda zaten kullanılıyor");
      found.item.name=next;
    }
    if(changes.sortOrder!==undefined) found.item.sortOrder=Number(changes.sortOrder)||0;
    if(changes.isActive!==undefined) found.item.isActive=!!changes.isActive;
    save(db);
    return found.item;
  }

  function importRows(rows=[]){
    if(!Array.isArray(rows)) throw new Error("Satırlar dizi olmalıdır");
    let processed=0;
    for(const r of rows){
      if(!r)continue;
      addPath(r.course||r.ders,r.unit||r["ünite"],r.topic||r["alt başlık"]||r.altBaslik,r.sortOrder??r["sıra"]??0);
      processed++;
    }
    return {processed};
  }

  return {file,tree,legacy,addPath,update,importRows};
}
module.exports={createCurriculumStore};
