let currTreeCache=[];
function currEsc(v){
  return String(v==null?"":v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function currFind(entity,id){
  id=Number(id);
  for(const course of currTreeCache){
    if(entity==="course"&&Number(course.id)===id)return course;
    for(const unit of course.units||[]){
      if(entity==="unit"&&Number(unit.id)===id)return unit;
      for(const topic of unit.topics||[])if(entity==="topic"&&Number(topic.id)===id)return topic;
    }
  }
  return null;
}
function currTreeHtml(courses){
  if(!courses.length)return emptyState("Müfredat boş","Ders, ünite ve alt başlık ekleyerek başlayın.");
  return courses.map(function(course){
    const topicCount=(course.units||[]).reduce(function(n,u){return n+(u.topics||[]).length},0);
    const units=(course.units||[]).map(function(unit){
      const topics=(unit.topics||[]).map(function(topic){
        return '<span class="badge neutral" style="margin:3px 4px 3px 0">'+currEsc(topic.name)+
          ' <button class="btn ghost small" style="padding:1px 5px" onclick="currEditModal(\'topic\','+Number(topic.id)+')">Düzenle</button>'+
          ' <button class="btn ghost small" style="padding:1px 5px" onclick="currDeactivate(\'topic\','+Number(topic.id)+')">Pasife al</button></span>';
      }).join(" ");
      return '<div class="item"><div class="section-head"><div><div class="cell-title">'+currEsc(unit.name)+
        '</div><div class="cell-sub">Sıra: '+Number(unit.sortOrder||0)+'</div></div><div>'+
        '<button class="btn ghost small" onclick="currEditModal(\'unit\','+Number(unit.id)+')">Düzenle</button> '+
        '<button class="btn danger small" onclick="currDeactivate(\'unit\','+Number(unit.id)+')">Pasife al</button>'+
        '</div></div><div style="margin-top:8px">'+(topics||'<span class="muted">Alt başlık yok.</span>')+'</div></div>';
    }).join("");
    return '<div class="card"><div class="section-head"><div><h2 style="margin:0">'+currEsc(course.name)+
      '</h2><div class="cell-sub">Sıra: '+Number(course.sortOrder||0)+' · '+topicCount+' alt başlık</div></div><div>'+
      '<button class="btn ghost small" onclick="currEditModal(\'course\','+Number(course.id)+')">Düzenle</button> '+
      '<button class="btn danger small" onclick="currDeactivate(\'course\','+Number(course.id)+')">Pasife al</button>'+
      '</div></div>'+units+'</div>';
  }).join("");
}
curriculum=async function(){
  shell(pageHead("Ders ve Üniteler","Ders → Ünite → Alt Başlık yapısını merkezi olarak yönetin.",
    '<button class="btn ghost" onclick="currImportCsv()">CSV Yükle</button> '+
    '<button class="btn primary" onclick="currModal()">+ Müfredat Ekle</button>'+
    '<input id="currCsvFile" type="file" accept=".csv,text/csv" style="display:none" onchange="currCsvChanged(event)">')+
    '<div id="curriculumServerState" class="notice"><div><b>Müfredat yükleniyor…</b>Sunucu tarafındaki kalıcı kayıt okunuyor.</div></div>'+
    '<div id="curriculumTree" class="list"></div>',"curriculum");
  try{
    const d=await apiJson("/api/coaching/curriculum/tree");
    currTreeCache=d.courses||[];
    db.curriculum=d.legacy||{};
    save();
    const s=q("curriculumServerState");
    if(s)s.innerHTML='<div><b>Merkezi müfredat aktif</b>Değişiklikler sunucu tarafındaki kalıcı müfredat dosyasına yazılır.</div>';
    const t=q("curriculumTree");
    if(t)t.innerHTML=currTreeHtml(currTreeCache);
  }catch(e){
    currTreeCache=[];
    const s=q("curriculumServerState");
    if(s){s.className="notice error";s.innerHTML='<div><b>Sunucu müfredatı okunamadı</b>'+currEsc(e.message)+'</div>'}
    const t=q("curriculumTree");
    if(t){
      let cards="";
      for(const pair of Object.entries(db.curriculum||{})){
        const course=pair[0],units=pair[1];
        cards+='<div class="card"><h2>'+currEsc(course)+'</h2>';
        for(const upair of Object.entries(units||{})){
          cards+='<div class="item"><div class="cell-title">'+currEsc(upair[0])+'</div><div>'+
            upair[1].map(function(x){return '<span class="badge neutral">'+currEsc(x)+'</span>'}).join(" ")+'</div></div>';
        }
        cards+="</div>";
      }
      t.innerHTML=cards||emptyState("Müfredat boş","Sunucu bağlantısı düzeldikten sonra kayıt ekleyin.");
    }
  }
};
window.currModal=function(){
  modal('<h2>Müfredat Ekle</h2><p class="muted">Aynı ders veya ünite varsa tekrar oluşturulmaz; yeni alt başlık ilgili yere eklenir.</p>'+
    '<div class="formgrid"><div class="field"><label>Ders</label><input id="ccourse"></div>'+
    '<div class="field"><label>Ünite</label><input id="cunit"></div>'+
    '<div class="field"><label>Alt Başlık</label><input id="ctopic"></div>'+
    '<div class="field"><label>Alt Başlık Sırası</label><input id="csort" type="number" value="0"></div></div>'+
    '<div class="modal-actions"><button class="btn primary" onclick="addCurr()">Kaydet</button>'+
    '<button class="btn ghost" onclick="closeModal()">İptal</button></div>');
};
window.addCurr=async function(){
  const course=q("ccourse").value.trim(),unit=q("cunit").value.trim(),topic=q("ctopic").value.trim();
  if(!course||!unit||!topic)return alert("Ders, ünite ve alt başlık zorunludur");
  try{
    await apiJson("/api/coaching/curriculum/action",{action:"add-path",course:course,unit:unit,topic:topic,sortOrder:Number(q("csort").value)||0});
    closeModal();await curriculum();
  }catch(e){alert("Müfredat kaydedilemedi: "+e.message)}
};
window.currEditModal=function(entity,id){
  const x=currFind(entity,id);if(!x)return;
  const label=entity==="course"?"Ders":entity==="unit"?"Ünite":"Alt Başlık";
  modal('<h2>'+label+' Düzenle</h2><div class="formgrid">'+
    '<div class="field"><label>Ad</label><input id="currEditName" value="'+currEsc(x.name)+'"></div>'+
    '<div class="field"><label>Sıra</label><input id="currEditSort" type="number" value="'+Number(x.sortOrder||0)+'"></div></div>'+
    '<div class="modal-actions"><button class="btn primary" onclick="currSaveEdit(\''+entity+'\','+Number(id)+')">Kaydet</button>'+
    '<button class="btn ghost" onclick="closeModal()">İptal</button></div>');
};
window.currSaveEdit=async function(entity,id){
  try{
    await apiJson("/api/coaching/curriculum/action",{action:"update",entity:entity,id:id,name:q("currEditName").value.trim(),sortOrder:Number(q("currEditSort").value)||0});
    closeModal();await curriculum();
  }catch(e){alert("Değişiklik kaydedilemedi: "+e.message)}
};
window.currDeactivate=async function(entity,id){
  const x=currFind(entity,id);
  if(!x||!confirm('"'+x.name+'" pasife alınsın mı? Kayıt fiziksel olarak silinmeyecek.'))return;
  try{
    await apiJson("/api/coaching/curriculum/action",{action:"update",entity:entity,id:id,isActive:false});
    await curriculum();
  }catch(e){alert("Kayıt pasife alınamadı: "+e.message)}
};
window.currImportCsv=function(){const el=q("currCsvFile");if(el)el.click()};
function currCsvLine(line){
  const out=[];let cur="",quoted=false;
  for(let i=0;i<line.length;i++){
    const ch=line[i];
    if(ch==='"'){
      if(quoted&&line[i+1]==='"'){cur+='"';i++}else quoted=!quoted;
    }else if(ch===","&&!quoted){out.push(cur.trim());cur=""}
    else cur+=ch;
  }
  out.push(cur.trim());return out;
}
window.currCsvChanged=async function(event){
  const file=event.target.files&&event.target.files[0];if(!file)return;
  try{
    const text=await file.text(),lines=text.replace(/^\uFEFF/,"").split(/\r?\n/).filter(function(x){return x.trim()});
    if(lines.length<2)throw new Error("CSV veri satırı bulunamadı");
    const h=currCsvLine(lines[0]).map(function(x){return x.toLocaleLowerCase("tr-TR")});
    const ci=h.indexOf("ders"),ui=h.indexOf("ünite"),ti=h.indexOf("alt başlık"),si=h.indexOf("sıra");
    if(ci<0||ui<0||ti<0)throw new Error("Başlıklar Ders, Ünite, Alt Başlık olmalıdır");
    const rows=[];
    for(const line of lines.slice(1)){
      const v=currCsvLine(line);
      if(!v[ci]&&!v[ui]&&!v[ti])continue;
      rows.push({course:v[ci],unit:v[ui],topic:v[ti],sortOrder:si>=0?Number(v[si])||0:0});
    }
    const d=await apiJson("/api/coaching/curriculum/action",{action:"import",rows:rows});
    alert((d.processed||0)+" satır işlendi.");await curriculum();
  }catch(e){alert("CSV yüklenemedi: "+e.message)}
  finally{event.target.value=""}
};
