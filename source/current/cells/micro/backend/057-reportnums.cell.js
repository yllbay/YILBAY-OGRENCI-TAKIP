function reportNums(a){return Array.isArray(a)?[...new Set(a.map(v=>String(v||'').trim()).filter(Boolean))].slice(0,1000):[]}
