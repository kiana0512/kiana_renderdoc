"""Archive the complete frame-38112 reconstruction workspace with ZIP64."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time
import zipfile


ROOTS = [
    (Path('F:/KianaStudioElectron'), Path('KianaStudioElectron')),
    (Path('F:/KianaFrame38112Unity'), Path('KianaFrame38112Unity')),
]
CAPTURE = Path('E:/KianaCaptures/ZenlessZoneZero')
CAPTURE_FOLDER = next(p for p in CAPTURE.iterdir()
                      if (p / 'capture_frame38112.rdc').is_file())
for name in ('capture_frame38112.rdc', 'analysis-frame38112',
             'capture_frame38112-reconstruction-1790516864703'):
    ROOTS.append((CAPTURE_FOLDER / name, Path('Frame38112Capture') / name))
ROOTS.append((Path('C:/Users/RT/.agents/skills/unity-cli'),
              Path('ExternalSkills/unity-cli')))

REFERENCE_PREFIXES = (
    '073c15c8', '3a8d6662', '6a933d05', 'c275b6f2', '05862510',
    '94ee9c8c', '6ebc9b11', 'f97c81c7', '7d27a112', 'e24d7d4d',
    '412570cc', 'e0e3dc43', '3ac2ef20', 'fdf195f8', '8be1a25f',
    '5d63e6b8', 'af3f739a', 'b6b034e7', '3163313d', 'f7dfc34b',
    '2e31a495', '1f06f16a', 'fbf414f3', '9ffc3f89', '87ce0509',
    '5c19b027', '6bba4520', '06794f23', '2153fc79', '998217b1',
    '7dda0568', 'b84145fd', '0c5e55a3', '7464aabc', '2f5dc631',
)
CLIPBOARD = Path('C:/Users/RT/AppData/Local/Temp')
for prefix in REFERENCE_PREFIXES:
    matches = list(CLIPBOARD.glob('codex-clipboard-' + prefix + '*.png'))
    for screenshot in matches:
        ROOTS.append((screenshot, Path('Frame38112References') / screenshot.name))

DEST = Path('F:/KianaFrame38112-complete-20260927.zip')
TEMP = DEST.with_suffix('.zip.partial')


def files_for(source, archive_root):
    if source.is_file():
        yield source, archive_root.as_posix()
        return
    for root, dirs, files in os.walk(source, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(root) / d).is_symlink())
        for filename in sorted(files):
            path = Path(root) / filename
            if path.is_symlink():
                raise RuntimeError('Symlinked file requires manual handling: ' + str(path))
            yield path, (archive_root / path.relative_to(source)).as_posix()


def main():
    if DEST.exists() or TEMP.exists():
        raise RuntimeError('Archive destination already exists: ' + str(DEST))
    entries = []
    for source, archive_root in ROOTS:
        if not source.exists():
            raise FileNotFoundError(source)
        entries.extend(files_for(source, archive_root))
    print('files=%d input_gb=%.3f' %
          (len(entries), sum(p.stat().st_size for p, _ in entries) / 2**30), flush=True)
    started = time.time()
    manifest = {'createdLocal': time.strftime('%Y-%m-%d %H:%M:%S'),
                'entryCount': len(entries),
                'sourceRoots': [{'source': str(s), 'archiveRoot': str(a)}
                                for s, a in ROOTS],
                'note': 'Unity Library and Kiana bundled runtime are included.'}
    with zipfile.ZipFile(TEMP, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=1, allowZip64=True) as archive:
        for index, (source, name) in enumerate(entries, 1):
            archive.write(source, name)
            if index % 2000 == 0:
                print('packed=%d/%d zip_gb=%.3f elapsed_s=%d' %
                      (index, len(entries), TEMP.stat().st_size / 2**30,
                       time.time() - started), flush=True)
        archive.writestr('PACKAGE-MANIFEST.json',
                         json.dumps(manifest, ensure_ascii=False, indent=2))
    print('checking_archive', flush=True)
    with zipfile.ZipFile(TEMP) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError('ZIP CRC failure: ' + bad)
        if len(archive.infolist()) != len(entries) + 1:
            raise RuntimeError('ZIP entry count mismatch')
    os.replace(TEMP, DEST)
    digest = hashlib.sha256()
    with DEST.open('rb') as stream:
        while True:
            chunk = stream.read(8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    summary = {'zip': str(DEST), 'bytes': DEST.stat().st_size,
               'sha256': digest.hexdigest(), 'files': len(entries),
               'elapsedSeconds': round(time.time() - started, 1)}
    Path('F:/KianaStudioElectron/docs/frame38112-package-result.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('PACKAGE_FAILED: %s: %s' % (type(error).__name__, error),
              file=sys.stderr, flush=True)
        raise
