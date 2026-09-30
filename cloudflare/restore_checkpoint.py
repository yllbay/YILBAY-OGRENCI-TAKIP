"""Request a dated code-only restore through the protected release workflow."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess


def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()


def main():
    parser = argparse.ArgumentParser(description='Korumalı GENESIS paket geri yükleme')
    parser.add_argument('date', choices=['2026-10-01'])
    parser.add_argument('--apply', action='store_true', help='Korumalı geri yükleme işini başlat')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    import os
    os.chdir(repo)
    manifest = json.loads((repo / 'cloudflare/restore-points' / (args.date + '.json')).read_text(encoding='utf-8'))
    if manifest['data_policy'] != 'PRESERVE_CURRENT_DB_AND_R2_ASSETS_NO_DATA_ROLLBACK':
        raise RuntimeError('Unsafe checkpoint data policy')
    print('Paket:', manifest['image'])
    print('Güncel soru havuzu, klasörler ve dosyalar korunur; eski veritabanı yüklenmez.')
    if not args.apply:
        print('Başlatmak için: python cloudflare/restore_checkpoint.py 2026-10-01 --apply')
        return
    if git('branch', '--show-current') != 'cloudflare-release':
        raise RuntimeError('Use the active cloudflare-release branch')
    if git('diff', '--name-only') or git('diff', '--cached', '--name-only'):
        raise RuntimeError('Commit current tracked changes before requesting restore')
    subprocess.run(['git', 'fetch', 'origin', 'cloudflare-release'], check=True)
    if git('rev-parse', 'HEAD') != git('rev-parse', 'origin/cloudflare-release'):
        raise RuntimeError('Update to the current release branch before requesting restore')
    trigger = repo / 'cloudflare/runtime-recovery-trigger.txt'
    with trigger.open('a', encoding='utf-8') as stream:
        stream.write(f'\nRestore {args.date} exact package; preserve current data. Requested {datetime.now(timezone.utc).isoformat()}\n')
    subprocess.run(['git', 'add', '--', 'cloudflare/runtime-recovery-trigger.txt'], check=True)
    subprocess.run(['git', 'commit', '-m', f'[pool-restore] Restore {args.date} exact runtime; preserve current pool'], check=True)
    subprocess.run(['git', 'push', 'origin', 'cloudflare-release'], check=True)
    print('Korumalı iş başlatıldı: https://github.com/yllbay/YILBAY-OGRENCI-TAKIP/actions/workflows/cloudflare-runtime-recovery.yml')


if __name__ == '__main__':
    main()
