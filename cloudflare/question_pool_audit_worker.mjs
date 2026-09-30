// Ephemeral authenticated reader; no R2 put/delete operations.
export default {async fetch(request, env) {
  if (request.method !== 'GET' || request.headers.get('Authorization') !== 'Bearer ' + env.AUDIT_TOKEN)
    return new Response('Not found', {status:404});
  const path = new URL(request.url).pathname;
  const headers = {'Content-Type':'application/json', 'Cache-Control':'no-store'};
  if (path === '/db') {
    const object = await env.DATA.get('DATA/genesis.db');
    if (!object) return new Response('Missing authoritative DB', {status:404});
    return new Response(object.body, {headers:{...headers, 'Content-Type':'application/vnd.sqlite3'}});
  }
  if (path !== '/assets') return new Response('Not found', {status:404});
  const protectedAssets = [], prefixCounts = {};
  let cursor, total = 0;
  do {
    const page = await env.DATA.list({prefix:'DATA/', limit:1000, cursor});
    for (const obj of page.objects || []) {
      total++;
      const k = obj.key || '';
      const group = k.startsWith('DATA/DisplayImages/') ? 'DisplayImages' :
        k.startsWith('DATA/RawCrops/') ? 'RawCrops' :
        k.startsWith('DATA/Sources/') ? 'Sources' :
        k.startsWith('DATA/DeletionTombstones/') ? 'DeletionTombstones' :
        k === 'DATA/genesis.db' ? 'genesis.db' : 'other';
      prefixCounts[group] = (prefixCounts[group] || 0) + 1;
      if (['DATA/DisplayImages/', 'DATA/RawCrops/', 'DATA/Sources/'].some(prefix => k.startsWith(prefix)))
        protectedAssets.push({key:k, size:Number(obj.size || 0), etag:String(obj.etag || '')});
    }
    cursor = page.truncated ? page.cursor : undefined;
  } while (cursor);
  protectedAssets.sort((a,b) => a.key.localeCompare(b.key));
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify(protectedAssets)));
  const sha256 = Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2,'0')).join('');
  const db = await env.DATA.head('DATA/genesis.db');
  return new Response(JSON.stringify({read_only:true,
    question_assets_fingerprint:{sha256, count:protectedAssets.length},
    genesis_db:db ? {exists:true, size:Number(db.size || 0), uploaded:db.uploaded, etag:db.etag, httpEtag:db.httpEtag} : {exists:false},
    prefix_counts:prefixCounts, total_objects_under_DATA:total, listing_truncated:false
  }), {headers});
}};
