"""Save/consume an encrypted exact runtime package; never restore application data."""
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

DATE = '2026-10-01'
TAG = 'genesis-restore-' + DATE
REPO = 'yllbay/YILBAY-OGRENCI-TAKIP'
ASSET = TAG + '.tar.enc'
IMAGE = 'registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:520be26036aede569368ed985a114e4220b022baf7bf7a8679579e0fd4d822d6'
WORKER = 'c742c1dd-e3f4-4256-a2bd-331ff29a7126'
ROOT = Path('/tmp/recovery')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def worker_module(raw):
    boundary = raw.splitlines()[0].strip().removeprefix(b'--')
    message = BytesParser(policy=default).parsebytes(
        b'Content-Type: multipart/form-data; boundary="' + boundary + b'"\r\n\r\n' + raw)
    modules = [part.get_payload(decode=True) for part in message.iter_parts()
               if b'GenesisContainer' in (part.get_payload(decode=True) or b'')]
    if len(modules) != 1:
        raise RuntimeError('Expected the single preserved GenesisContainer Worker module')
    return modules[0]


def crypt(source, target, decrypt=False):
    if not os.environ.get('GENESIS_RESTORE_KEY'):
        raise RuntimeError('Checkpoint encryption key is missing')
    subprocess.run(['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-iter', '200000',
                    *(['-d'] if decrypt else ['-salt']), '-pass', 'env:GENESIS_RESTORE_KEY',
                    '-in', str(source), '-out', str(target)], check=True)


def capture():
    snapshot = ROOT / 'snapshot'
    container = read_json(snapshot / 'container.json')
    deployments = read_json(snapshot / 'deployments.json')['result']
    current = deployments['deployments'][0]['versions']
    if container['version'] != 115 or container['configuration']['image'] != IMAGE or current != [{'version_id': WORKER, 'percentage': 100}]:
        raise RuntimeError('Live runtime changed; do not create a misleading dated checkpoint')
    package = ROOT / 'checkpoint-package'
    package.mkdir()
    files = ['worker.bin', 'settings.json', 'deployments.json', 'container.json',
             'image-config.json', 'start-container.sh', 'app-source.tar.xz',
             'pool-fingerprint-before.json', 'pool-assets-before.json', 'checkpoint-health.json']
    for name in files:
        shutil.copy2(snapshot / name, package / name)
    (package / 'worker-index.js').write_bytes(worker_module((package / 'worker.bin').read_bytes()))
    subprocess.run(['node', '--check', str(package / 'worker-index.js')], check=True)
    # Retain full dependency layers and original manifest, independently of registry retention.
    subprocess.run(['skopeo', 'copy', '--preserve-digests', '--src-creds',
                    os.environ['REG_USER'] + ':' + os.environ['REG_PASS'],
                    'docker://' + IMAGE, 'oci-archive:' + str(package / 'container.oci.tar') + ':checkpoint'], check=True)
    with tarfile.open(package / 'container.oci.tar') as archive:
        index = json.load(archive.extractfile('index.json'))
        descriptor = index['manifests'][0]
        if descriptor['digest'] != IMAGE.split('@')[1]:
            raise RuntimeError('OCI archive lost the exact production image digest')
    hashes = {p.name: sha256(p) for p in package.iterdir() if p.is_file()}
    baseline = read_json(snapshot / 'pool-fingerprint-before.json')
    assets = read_json(snapshot / 'pool-assets-before.json')['question_assets_fingerprint']
    manifest = {
        'format': 'GENESIS_RUNTIME_RESTORE_POINT_V1', 'date': DATE, 'tag': TAG,
        'created_at': datetime.now(timezone.utc).isoformat(), 'image': IMAGE,
        'container_version': 115, 'worker_version': WORKER,
        'image_source_commit': '1bdfb203ad03b640b33cfb9668f7f89202e5e5da',
        'verified_release_run': 36783274326, 'capture_run': int(os.environ['GITHUB_RUN_ID']),
        'checkpoint_commit': os.environ['GITHUB_SHA'],
        'release_url': f'https://github.com/{REPO}/releases/tag/{TAG}',
        'archive_asset': ASSET, 'encryption': 'AES-256-CBC/PBKDF2-SHA256/200000',
        'key_secret': 'GENESIS_RESTORE_20261001_KEY',
        'data_policy': 'PRESERVE_CURRENT_DB_AND_R2_ASSETS_NO_DATA_ROLLBACK',
        'baseline_db_sha256': baseline['sha256'], 'baseline_assets': assets,
        'files_sha256': hashes,
    }
    write_json(package / 'package-manifest.json', manifest)
    plain = ROOT / 'checkpoint.tar'
    with tarfile.open(plain, 'w') as archive:
        for path in sorted(package.iterdir()):
            archive.add(path, arcname=path.name, recursive=False)
    encrypted = snapshot / ASSET
    crypt(plain, encrypted)
    manifest['archive_sha256'] = sha256(encrypted)
    manifest['archive_size'] = encrypted.stat().st_size
    write_json(snapshot / 'restore-point.json', manifest)
    plain.unlink()
    print('EXACT_ENCRYPTED_RUNTIME_CHECKPOINT_READY', DATE, manifest['archive_size'])


def load():
    anchor = read_json(Path(__file__).parent / 'restore-points' / (DATE + '.json'))
    if anchor['date'] != DATE or anchor['image'] != IMAGE or anchor['worker_version'] != WORKER:
        raise RuntimeError('Unexpected checkpoint identity')
    download = ROOT / 'restore-download'
    download.mkdir()
    subprocess.run(['gh', 'release', 'download', TAG, '--repo', REPO, '--dir', str(download),
                    '--pattern', ASSET, '--pattern', 'restore-point.json'], check=True)
    encrypted = download / ASSET
    if sha256(encrypted) != anchor['archive_sha256']:
        raise RuntimeError('Encrypted checkpoint checksum mismatch')
    if read_json(download / 'restore-point.json') != anchor:
        raise RuntimeError('Release manifest differs from the committed checkpoint')
    plain = ROOT / 'restore-package.tar'
    crypt(encrypted, plain, decrypt=True)
    target = ROOT / 'restore-package'
    target.mkdir()
    expected = set(anchor['files_sha256']) | {'package-manifest.json'}
    with tarfile.open(plain) as archive:
        members = archive.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != expected or any(not m.isfile() for m in members):
            raise RuntimeError('Unexpected content in runtime-only checkpoint')
        archive.extractall(target, filter='data')
    for name, digest in anchor['files_sha256'].items():
        if sha256(target / name) != digest:
            raise RuntimeError('Checkpoint file checksum mismatch: ' + name)
    if worker_module((target / 'worker.bin').read_bytes()) != (target / 'worker-index.js').read_bytes():
        raise RuntimeError('Saved Worker module differs from original content')
    creds = os.environ['REG_USER'] + ':' + os.environ['REG_PASS']
    present = subprocess.run(['skopeo', 'inspect', '--raw', '--creds', creds, 'docker://' + IMAGE], capture_output=True)
    if present.returncode:
        # A registry tag may expire; recover the exact saved layers/manifest from the encrypted archive.
        registry = ROOT / 'restore-registry.json'
        account = os.environ['CLOUDFLARE_ACCOUNT_ID'].strip()
        subprocess.run(['curl', '-fsS', '-X', 'POST', f'https://api.cloudflare.com/client/v4/accounts/{account}/containers/registries/registry.cloudflare.com/credentials',
                        '-H', 'Authorization: Bearer ' + os.environ['CLOUDFLARE_API_TOKEN'], '-H', 'Content-Type: application/json',
                        '--data', '{"expiration_minutes":20,"permissions":["pull","push"]}', '-o', str(registry)], check=True)
        credentials = read_json(registry)['result']
        for key in ('username', 'password'):
            print('::add-mask::' + credentials[key], flush=True)
        creds = credentials['username'] + ':' + credentials['password']
        subprocess.run(['skopeo', 'copy', '--preserve-digests', '--dest-creds', creds,
                        'oci-archive:' + str(target / 'container.oci.tar') + ':checkpoint',
                        'docker://' + IMAGE.split('@')[0] + ':' + TAG], check=True)
        present = subprocess.run(['skopeo', 'inspect', '--raw', '--creds', creds, 'docker://' + IMAGE], capture_output=True, check=True)
    if hashlib.sha256(present.stdout).hexdigest() != IMAGE.split('@sha256:')[1]:
        raise RuntimeError('Registry does not contain the exact saved manifest')
    with Path(os.environ['GITHUB_ENV']).open('a', encoding='utf-8') as env:
        env.write(f'RECOVERY_IMAGE={IMAGE}\nRECOVERY_WORKER_PACKAGE={target}\n')
    plain.unlink()
    print('EXACT_CHECKPOINT_LOADED_CURRENT_QUESTION_POOL_WILL_BE_PRESERVED')


if __name__ == '__main__':
    {'capture': capture, 'load': load}[sys.argv[1]]()
