function load(){try{
 const current=localStorage.getItem(STORAGE);
 if(current) return normalizeDb(JSON.parse(current));
 const p63=localStorage.getItem(PREV_STORAGE_063);
 if(p63){const migrated=normalizeDb(JSON.parse(p63));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const p62=localStorage.getItem(PREV_STORAGE_062);
 if(p62){const migrated=normalizeDb(JSON.parse(p62));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const p61=localStorage.getItem(PREV_STORAGE_061);
 if(p61){const migrated=normalizeDb(JSON.parse(p61));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const p60=localStorage.getItem(PREV_STORAGE_060);
 if(p60){const migrated=normalizeDb(JSON.parse(p60));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const p45=localStorage.getItem(PREV_STORAGE_045);
 if(p45){const migrated=normalizeDb(JSON.parse(p45));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const prev=localStorage.getItem(PREV_STORAGE);
 if(prev){const migrated=normalizeDb(JSON.parse(prev)); localStorage.setItem(STORAGE,JSON.stringify(migrated)); return migrated;}
 const legacy43=localStorage.getItem(LEGACY_043);
 if(legacy43){const migrated=normalizeDb(JSON.parse(legacy43)); localStorage.setItem(STORAGE,JSON.stringify(migrated)); return migrated;}
 const old=localStorage.getItem(OLD_STORAGE);
 if(old){const migrated=normalizeDb(JSON.parse(old)); localStorage.setItem(STORAGE,JSON.stringify(migrated)); return migrated;}
 return normalizeDb(structuredClone(seed))
}catch{return normalizeDb(structuredClone(seed))}}


