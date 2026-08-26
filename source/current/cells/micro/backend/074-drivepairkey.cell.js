function drivePairKey(name){return String(name||'').replace(/\.pdf$/i,'').replace(/__(CEVAP|CEVAP[_ -]?ANAHTARI|ANSWER[_ -]?KEY)$/i,'').trim().toLocaleLowerCase('tr-TR').replace(/\s+/g,' ')}
