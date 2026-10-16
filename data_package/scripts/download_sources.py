from pathlib import Path
from urllib.request import urlopen
import hashlib, json, time

ROOT = Path(__file__).resolve().parents[1]

def download(url, path, expected_hash):
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash:
        print('Already verified:', path.relative_to(ROOT))
        return
    if path.exists():
        raise SystemExit(f'Existing content differs; move it before redownloading: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=60) as response:
        payload = response.read()
    actual = hashlib.sha256(payload).hexdigest()
    if expected_hash and actual != expected_hash:
        # Live abstract records may legitimately change; preserve downloaded bytes separately.
        changed = path.with_name(path.name + '.changed')
        changed.write_bytes(payload)
        raise SystemExit(f'Upstream content changed; saved separately at {changed}')
    path.write_bytes(payload)
    print('Downloaded:', path.relative_to(ROOT))
    time.sleep(.35)

for name in ['download_manifest.json', 'auxiliary_strength_manifest.json']:
    manifest = json.loads((ROOT/'provenance'/name).read_text())
    for item in manifest['files']:
        download(item['url'], ROOT/item['local_path'], item['sha256'])
for line in (ROOT/'sources/abstracts.jsonl').read_text(encoding='utf-8').splitlines():
    if line.strip():
        item = json.loads(line)
        download(item['provider_url'], ROOT/item['raw_response_path'], item['raw_response_sha256'])
