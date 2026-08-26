async function apiJson(url,body=null){
 const opt=body===null?{}:{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)};
 const r=await fetch(url,opt),data=await r.json().catch(()=>({}));
 if(!r.ok||data.ok===false)throw new Error(data.error||`HTTP ${r.status}`);
 return data
}

/* CELL:90-integrations | layer:frontend | generated-from:v0.9.6 */

/* CELL:90-integrations | layer:frontend | generated-from:v0.7.2 */
