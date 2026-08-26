function reportNums(a){return Array.isArray(a)?[...new Set(a.map(Number).filter(n=>Number.isInteger(n)&&n>0))].sort((x,y)=>x-y).slice(0,1000):[]}
