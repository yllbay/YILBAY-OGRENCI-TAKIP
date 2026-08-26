function reportText(v,max=1200){return String(v==null?'':v).replace(/[\u0000-\u001f\u007f]/g,' ').trim().slice(0,max)}
