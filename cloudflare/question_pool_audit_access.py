"""Short-lived, authenticated read-only R2 audit Worker. No R2 writes or deletes."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

ROOT = Path('/tmp/recovery/audit')
ROOT.mkdir(parents=True, exist_ok=True)
account = os.environ['CLOUDFLARE_ACCOUNT_ID'].strip()
api = f'https://api.cloudflare.com/client/v4/accounts/{account}'
auth = 'Authorization: Bearer ' + os.environ['CLOUDFLARE_API_TOKEN']


def call(method, path, extra=()):
    result = subprocess.run(['curl', '-sS', '--max-time', '30', '-X', method,
                             api + path, '-H', auth, *extra], capture_output=True, check=True)
    response = json.loads(result.stdout)
    if not response.get('success'):
        raise RuntimeError(f'{method} {path}: {response.get("errors")}')
    return response.get('result')


mode = sys.argv[1]
if mode == 'create':
    name = 'genesis-pool-audit-' + os.environ['GITHUB_RUN_ID']
    token = secrets.token_hex(32)
    print('::add-mask::' + token, flush=True)
    (ROOT / 'name').write_text(name)
    (ROOT / 'token').write_text(token)
    source = Path(__file__).with_name('question_pool_audit_worker.mjs').read_text(encoding='utf-8')
    (ROOT / 'index.mjs').write_text(source)
    metadata = {'main_module': 'index.mjs', 'compatibility_date': '2026-09-10',
                'bindings': [{'name': 'DATA', 'type': 'r2_bucket', 'bucket_name': 'genesis-web-0152-data'},
                             {'name': 'AUDIT_TOKEN', 'type': 'secret_text', 'text': token}]}
    (ROOT / 'metadata.json').write_text(json.dumps(metadata))
    call('PUT', f'/workers/scripts/{name}',
         ('-F', f'metadata=@{ROOT}/metadata.json;type=application/json',
          '-F', f'index.mjs=@{ROOT}/index.mjs;type=application/javascript+module'))
    call('POST', f'/workers/scripts/{name}/subdomain',
         ('-H', 'Content-Type: application/json', '--data', '{"enabled":true}'))
    subdomain = call('GET', '/workers/subdomain')['subdomain']
    (ROOT / 'url').write_text(f'https://{name}.{subdomain}.workers.dev/db')
elif mode in ('download', 'download-assets'):
    target = Path(sys.argv[2])
    token = (ROOT / 'token').read_text()
    print('::add-mask::' + token, flush=True)
    url = (ROOT / 'url').read_text()
    if mode == 'download-assets':
        url = url.removesuffix('/db') + '/assets'
    for attempt in range(20):
        result = subprocess.run(['curl', '-fsS', '--max-time', '15', url,
                                 '-H', 'Authorization: Bearer ' + token, '-o', str(target)],
                                capture_output=True)
        if result.returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError('Read-only audit Worker could not download authoritative DB')
elif mode == 'cleanup':
    if (ROOT / 'name').exists():
        name = (ROOT / 'name').read_text()
        assert name.startswith('genesis-pool-audit-')
        call('DELETE', f'/workers/scripts/{name}')
        print('Ephemeral read-only audit Worker removed')
else:
    raise ValueError(mode)
