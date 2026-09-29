from pathlib import Path

p=Path("cloudflare/package-runtime/index.js")
src=p.read_text(encoding="utf-8")
MARK="GENESIS_R2_QUESTION_POOL_READONLY_PROBE_V3"
OLD_MARK="GENESIS_R2_QUESTION_POOL_READONLY_PROBE_V3"
changed=False

if OLD_MARK in src:
    old_cond='if (request.method === "GET" && probeUrl.pathname === "/api/internal/r2-question-pool-readonly") {'
    pos=src.find(OLD_MARK)
    cpos=src.find(old_cond,pos)
    if cpos<0:
        raise SystemExit("V1 R2 probe marker found but route shape changed")
    src=src[:cpos]+old_cond.replace("if (","if (false && ",1)+src[cpos+len(old_cond):]
    src=src.replace(OLD_MARK,"GENESIS_R2_QUESTION_POOL_READONLY_PROBE_RETIRED_V2",1)
    changed=True

if MARK in src:
    if changed:
        p.write_text(src,encoding="utf-8")
        print("R2 readonly probe V2 retired; existing V3 preserved")
    else:
        print("R2 readonly probe V3 already present")
    raise SystemExit(0)

needle='''      const upstream = await container.fetch(forwarded);
      const headers = new Headers(upstream.headers);'''
if needle not in src:
    raise SystemExit("Worker upstream anchor missing")

probe=r'''      // GENESIS_R2_QUESTION_POOL_READONLY_PROBE_V3
      // Temporary read-only diagnostics. Never put/delete/write R2 objects here.
      {
        const probeUrl = new URL(request.url);
        if (request.method === "GET" && probeUrl.pathname === "/api/internal/r2-question-pool-readonly") {
          const prefixCounts = {};
          const sampleKeys = [];
          const protectedAssets = [];
          let cursor = undefined;
          let total = 0;
          let bucketTotal = 0;
          const bucketSamples = [];
          let truncated = false;
          do {
            const page = await env.GENESIS_DATA.list({prefix:"DATA/", limit:1000, cursor});
            for (const obj of page.objects || []) {
              total++;
              const k = obj.key || "";
              if (
                k.startsWith("DATA/DisplayImages/") ||
                k.startsWith("DATA/RawCrops/") ||
                k.startsWith("DATA/Sources/")
              ) {
                protectedAssets.push({
                  key:k,
                  size:Number(obj.size || 0),
                  etag:String(obj.etag || "")
                });
              }
              const group =
                k.startsWith("DATA/DisplayImages/") ? "DisplayImages" :
                k.startsWith("DATA/RawCrops/") ? "RawCrops" :
                k.startsWith("DATA/DeletionTombstones/") ? "DeletionTombstones" :
                k === "DATA/genesis.db" ? "genesis.db" : "other";
              prefixCounts[group] = (prefixCounts[group] || 0) + 1;
              if (sampleKeys.length < 40) {
                sampleKeys.push({key:k,size:obj.size,uploaded:obj.uploaded,etag:obj.etag});
              }
            }
            cursor = page.truncated ? page.cursor : undefined;
            truncated = Boolean(page.truncated);
          } while (cursor && total < 100000);

          let rootCursor = undefined;
          do {
            const rootPage = await env.GENESIS_DATA.list({limit:1000, cursor:rootCursor});
            for (const obj of rootPage.objects || []) {
              bucketTotal++;
              if (bucketSamples.length < 80) bucketSamples.push({key:obj.key,size:obj.size,uploaded:obj.uploaded,etag:obj.etag});
            }
            rootCursor = rootPage.truncated ? rootPage.cursor : undefined;
          } while (rootCursor && bucketTotal < 200000);

          protectedAssets.sort((a,b)=>a.key.localeCompare(b.key));
          const assetBytes = new TextEncoder().encode(JSON.stringify(protectedAssets));
          const assetDigest = await crypto.subtle.digest("SHA-256", assetBytes);
          const assetSha256 = Array.from(new Uint8Array(assetDigest))
            .map(b=>b.toString(16).padStart(2,"0")).join("");

          const dbHead = await env.GENESIS_DATA.head("DATA/genesis.db");
          const rootDbHead = await env.GENESIS_DATA.head("genesis.db");
          const response = {
            marker:"GENESIS_R2_QUESTION_POOL_READONLY_PROBE_V3",
            read_only:true,
            question_assets_fingerprint:{
              sha256:assetSha256,
              count:protectedAssets.length
            },
            total_objects_under_DATA:total,
            prefix_counts:prefixCounts,
            bucket_total_objects:bucketTotal,
            bucket_sample_keys:bucketSamples,
            root_genesis_db:rootDbHead ? {exists:true,size:rootDbHead.size,uploaded:rootDbHead.uploaded,etag:rootDbHead.etag} : {exists:false},
            genesis_db:dbHead ? {
              exists:true,
              size:dbHead.size,
              uploaded:dbHead.uploaded,
              etag:dbHead.etag,
              httpEtag:dbHead.httpEtag
            } : {exists:false},
            sample_keys:sampleKeys,
            listing_truncated:truncated
          };
          return new Response(JSON.stringify(response),{
            status:200,
            headers:{
              "content-type":"application/json; charset=utf-8",
              "cache-control":"no-store"
            }
          });
        }
      }

      const upstream = await container.fetch(forwarded);
      const headers = new Headers(upstream.headers);'''

src=src.replace(needle,probe,1)
p.write_text(src,encoding="utf-8")
out=p.read_text(encoding="utf-8")
assert MARK in out
assert 'env.GENESIS_DATA.list' in out
assert 'question_assets_fingerprint' in out
assert 'env.GENESIS_DATA.head("DATA/genesis.db")' in out
assert '.put(' not in probe and '.delete(' not in probe
print("GENESIS R2 question-pool read-only probe: OK")
