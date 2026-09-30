from pathlib import Path
import json
import os
import subprocess

snapshot = Path('/tmp/recovery/snapshot')
runtime = Path('/tmp/recovery/runtime')
runtime.mkdir(parents=True, exist_ok=True)
raw = (snapshot/'worker.bin').read_bytes()
boundary = raw.splitlines()[0].strip()
modules = []
for part in raw.split(boundary)[1:]:
    part = part.strip(b'\r\n-')
    sep = b'\r\n\r\n' if b'\r\n\r\n' in part else b'\n\n'
    if sep not in part:
        continue
    payload = part.split(sep, 1)[1].rstrip(b'\r\n')
    if b'GenesisContainer' in payload:
        modules.append(payload)
assert len(modules) == 1
(runtime/'index.js').write_bytes(modules[0])
if b'GENESIS_LOCAL_SQLITE_R2_V1' not in modules[0]:
    subprocess.run(['python3', 'cloudflare/runtime_recovery_worker.py', str(runtime/'index.js')], check=True)
settings = json.loads((snapshot/'settings.json').read_text())['result']
before = json.loads((snapshot/'container.json').read_text())
cfg = {
    'name': 'genesis-web-0152', 'main': 'index.js', 'no_bundle': True, 'keep_vars': True,
    'workers_dev': True, 'compatibility_date': settings['compatibility_date'],
    'compatibility_flags': settings.get('compatibility_flags', []),
    'containers': [{'class_name': 'GenesisContainer', 'image': os.environ['RECOVERY_IMAGE'],
                    'instance_type': 'standard-1', 'max_instances': 1,
                    'rollout_active_grace_period': 1}],
    'durable_objects': {'bindings': [{'name': 'GENESIS_CONTAINER', 'class_name': 'GenesisContainer'}]},
    'r2_buckets': [{'binding': 'GENESIS_DATA', 'bucket_name': 'genesis-web-0152-data'}],
    'migrations': [{'tag': 'v1', 'new_sqlite_classes': ['GenesisContainer']}],
    'observability': {'enabled': True},
}
(runtime/'wrangler.jsonc').write_text(json.dumps(cfg, indent=2)+'\n')
print('Prepared recovery wrapper; preserved live application and edge overlays')
