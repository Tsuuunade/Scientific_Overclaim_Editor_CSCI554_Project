"""Refresh the package snapshot after intentional edits and verification.

Temporary QA outputs, Python caches and repository metadata are excluded.
Human review edits are intentional changes but require a new versioned snapshot.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT/'provenance/package_checksums.json'
EXCLUDED = {'tmp', '.git', '__pycache__', '.pytest_cache'}


def main():
    files = []
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p == TARGET or any(part in EXCLUDED for part in p.relative_to(ROOT).parts):
            continue
        payload = p.read_bytes()
        files.append(dict(path=p.relative_to(ROOT).as_posix(), size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()))
    TARGET.write_text(json.dumps(dict(package_version='2.1', created_utc=datetime.now(timezone.utc).isoformat(),
                                    excludes=sorted(EXCLUDED), files=files), indent=2)+'\n', encoding='utf-8')
    print(f'Recorded {len(files)} package file hashes.')


if __name__ == '__main__':
    main()
