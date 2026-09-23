"""Keep verified runtime layers; replace accumulated app patches with one COPY."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tarfile

root = pathlib.Path('/tmp/genesis-v3')
oci = root / 'current-oci'
blobs = oci / 'blobs/sha256'
index = json.loads((oci / 'index.json').read_text())
manifest = json.loads((blobs / index['manifests'][0]['digest'].split(':')[1]).read_text())
config = json.loads((blobs / manifest['config']['digest'].split(':')[1]).read_text())
keep = 10
assert len(manifest['layers']) >= keep
history = config.get('history', [])
layer_history = [h for h in history if not h.get('empty_layer')]
assert 'pip install' in layer_history[keep-1]['created_by'], 'Runtime boundary changed'
assert 'COPY APP' in layer_history[keep]['created_by'], 'Application boundary changed'
# Later layers must not contain operating-system/runtime changes we would discard.
for layer in manifest['layers'][keep:]:
    with tarfile.open(blobs / layer['digest'].split(':')[1], 'r:*') as archive:
        for item in archive:
            name = item.name.removeprefix('./').strip('/')
            if not name:
                continue
            if name.split('/')[0] not in {'app', 'tmp'}:
                raise SystemExit('Unexpected later-layer path outside app/tmp: ' + name)
cfg = dict(config)
cfg['rootfs'] = dict(config['rootfs'], diff_ids=config['rootfs']['diff_ids'][:keep])
cfg['history'] = []
n = 0
for h in history:
    if not h.get('empty_layer'):
        n += 1
    if n > keep:
        break
    cfg['history'].append(h)
prefix = root / 'runtime-oci'
shutil.copytree(oci, prefix)
def blob(value):
    data = json.dumps(value, separators=(',', ':')).encode()
    digest = hashlib.sha256(data).hexdigest()
    (prefix / 'blobs/sha256' / digest).write_bytes(data)
    return 'sha256:' + digest, len(data)
dg, size = blob(cfg)
manifest['config'] = dict(manifest['config'], digest=dg, size=size)
manifest['layers'] = manifest['layers'][:keep]
dg, size = blob(manifest)
index['manifests'] = [dict(index['manifests'][0], digest=dg, size=size, annotations={'org.opencontainers.image.ref.name':'runtime'})]
(prefix / 'index.json').write_text(json.dumps(index))
subprocess.run(['skopeo','copy','oci:'+str(prefix)+':runtime','docker-daemon:genesis-runtime:v3'], check=True)
build = root / 'clean-build'
build.mkdir()
shutil.copytree(root / 'bundle/rootfs/app', build / 'app', symlinks=True)
dockerfile = 'FROM genesis-runtime:v3\nCOPY --chown=0:0 app/ /app/\n'
(build / 'Dockerfile').write_text(dockerfile)
subprocess.run(['docker','build','--platform','linux/amd64','-t',os.environ['NEW_IMAGE'],str(build)],check=True)
result = json.loads(subprocess.check_output(['docker','image','inspect',os.environ['NEW_IMAGE']]))[0]
assert len(result['RootFS']['Layers']) == keep + 1
for key in ('Cmd','Entrypoint','WorkingDir','Env','User'):
    assert (result['Config'].get(key) or None) == (config['config'].get(key) or None), 'Runtime configuration changed: '+key
print('GENESIS_CLEAN_RUNTIME_IMAGE_OK layers=',len(result['RootFS']['Layers']))
