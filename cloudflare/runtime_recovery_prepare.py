from pathlib import Path
import json
import os
import subprocess
from restore_point import worker_module

snapshot = Path('/tmp/recovery/snapshot')
runtime = Path('/tmp/recovery/runtime')
runtime.mkdir(parents=True, exist_ok=True)
saved_package = os.environ.get('RECOVERY_WORKER_PACKAGE')
source = Path(saved_package) if saved_package else snapshot
module = worker_module((source/'worker.bin').read_bytes())
# Core GENESIS scope: deferred/unimplemented launch actions must not appear as live features.
if os.environ.get('CORE_ONLY')=='1':
    from core_scope_worker import patch as patch_core_scope
    module = patch_core_scope(module)
if os.environ.get('ANA_PRG_RELEASE')=='1':
    from ana_prg_worker import patch
    module=patch(module)
(runtime/'index.js').write_bytes(module)
if not saved_package and b'GENESIS_LOCAL_SQLITE_R2_V1' not in module:
    subprocess.run(['python3', 'cloudflare/runtime_recovery_worker.py', str(runtime/'index.js')], check=True)
settings = json.loads((source/'settings.json').read_text(encoding='utf-8'))['result']
before = json.loads((snapshot/'container.json').read_text())
base_grace = int(before.get('rollout_active_grace_period') or 0)
rollout_grace = int(os.environ.get('RECOVERY_ROLLOUT_GRACE') or (2 if base_grace != 2 else 1))
cfg = {
    'name': 'genesis-web-0152', 'main': 'index.js', 'no_bundle': True, 'keep_vars': True,
    'workers_dev': True, 'compatibility_date': settings['compatibility_date'],
    'compatibility_flags': settings.get('compatibility_flags', []),
    'containers': [{'class_name': 'GenesisContainer', 'image': os.environ['RECOVERY_IMAGE'],
                    'instance_type': 'standard-1', 'max_instances': 1,
                    'rollout_active_grace_period': rollout_grace}],
    'durable_objects': {'bindings': [{'name': 'GENESIS_CONTAINER', 'class_name': 'GenesisContainer'}]},
    'r2_buckets': [{'binding': 'GENESIS_DATA', 'bucket_name': 'genesis-web-0152-data'}],
    'migrations': [{'tag': 'v1', 'new_sqlite_classes': ['GenesisContainer']}],
    'observability': {'enabled': True},
}
(runtime/'wrangler.jsonc').write_text(json.dumps(cfg, indent=2)+'\n')
print('Prepared exact saved Worker' if saved_package else 'Prepared recovery wrapper; preserved live application and edge overlays')
