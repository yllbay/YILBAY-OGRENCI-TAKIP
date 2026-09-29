from pathlib import Path

p=Path("cloudflare/package-runtime/index.js")
src=p.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_INTEGRITY_PROBE_V4"
PATH="/api/internal/question-studio-integrity-v4"

if MARK in src:
    print("Question Studio integrity probe V4 already present")
    raise SystemExit(0)

needle='''      const upstream = await container.fetch(forwarded);
      const headers = new Headers(upstream.headers);'''
if needle not in src:
    raise SystemExit("Worker upstream anchor missing")

probe=r'''      // GENESIS_QUESTION_STUDIO_INTEGRITY_PROBE_V4
      // Strictly read-only integrity endpoint. Never put/delete/write R2 objects here.
      {
        const integrityUrl = new URL(request.url);
        if (request.method === "GET" && integrityUrl.pathname === "/api/internal/question-studio-integrity-v4") {
          const protectedAssets = [];
          const prefixCounts = {};
          let cursor = undefined;
          let total = 0;
          let truncated = false;

          do {
            const page = await env.GENESIS_DATA.list({prefix:"DATA/", limit:1000, cursor});
            for (const obj of page.objects || []) {
              total++;
              const k = obj.key || "";
              const group =
                k.startsWith("DATA/DisplayImages/") ? "DisplayImages" :
                k.startsWith("DATA/RawCrops/") ? "RawCrops" :
                k.startsWith("DATA/Sources/") ? "Sources" :
                k.startsWith("DATA/DeletionTombstones/") ? "DeletionTombstones" :
                k === "DATA/genesis.db" ? "genesis.db" : "other";
              prefixCounts[group] = (prefixCounts[group] || 0) + 1;

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
            }
            cursor = page.truncated ? page.cursor : undefined;
            truncated = Boolean(page.truncated);
          } while (cursor && total < 100000);

          protectedAssets.sort((a,b)=>a.key.localeCompare(b.key));
          const bytes = new TextEncoder().encode(JSON.stringify(protectedAssets));
          const digest = await crypto.subtle.digest("SHA-256", bytes);
          const sha256 = Array.from(new Uint8Array(digest))
            .map(b=>b.toString(16).padStart(2,"0")).join("");

          const dbHead = await env.GENESIS_DATA.head("DATA/genesis.db");
          const response = {
            marker:"GENESIS_QUESTION_STUDIO_INTEGRITY_PROBE_V4",
            read_only:true,
            question_assets_fingerprint:{
              sha256,
              count:protectedAssets.length
            },
            genesis_db:dbHead ? {
              exists:true,
              size:Number(dbHead.size || 0),
              uploaded:dbHead.uploaded,
              etag:dbHead.etag,
              httpEtag:dbHead.httpEtag
            } : {exists:false},
            prefix_counts:prefixCounts,
            total_objects_under_DATA:total,
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
assert PATH in out
assert 'env.GENESIS_DATA.list' in out
assert 'env.GENESIS_DATA.head("DATA/genesis.db")' in out
assert '.put(' not in probe and '.delete(' not in probe
print("GENESIS Question Studio integrity probe V4: OK")
