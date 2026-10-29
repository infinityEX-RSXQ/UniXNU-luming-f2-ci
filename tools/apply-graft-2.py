#!/usr/bin/env python3
"""Second graft pass: catalog patch, CI preflight wiring and checker board-module acceptance."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
UNI = Path(r'D:/civitoip20/unixnu-format2/UniXNU')
TMP = ROOT / '.check' / 'uni'
GIT = r'C:/Program Files/Git/cmd/git.exe'


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    print(f'wrote {rel}')


def edit(rel, pairs):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        if old not in text:
            print(f'WARN {rel}: pattern not found: {old[:70]!r}')
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')
    print(f'edited {rel}')


def check_skeleton_accept_modules():
    edit('scripts/check-skeleton.py', [
        ('''    pending = list(selected)
    while pending:
        cid = pending.pop()
        if cid not in catalog:
            add('ERROR', f'component not in catalog: {cid}')
            continue
        for dep in catalog[cid].get('dependencies', []):
            if dep not in selected:
                selected.append(dep)
                pending.append(dep)
    add('PASS', f'components: {len(selected)} selected incl dependencies: {", ".join(sorted(selected))}')''',
         '''    pending = list(selected)
    board_modules = []
    while pending:
        cid = pending.pop()
        if cid not in catalog:
            if (ROOT / 'drivers' / cid).is_dir():
                board_modules.append(cid)
                add('WARN', f'component {cid} is a board module without a catalog entry',
                    'needs patches/unixnu/unixnu-components-lumingufs.patch applied to UniXNU')
                continue
            add('ERROR', f'component not in catalog: {cid}')
            continue
        for dep in catalog[cid].get('dependencies', []):
            if dep not in selected:
                selected.append(dep)
                pending.append(dep)
    add('PASS', f'components: {len(selected)} selected incl dependencies: {", ".join(sorted(selected))}')'''),
        ('''        if item.startswith('component:'):
            cid = item.split(':', 1)[1]
            add('PASS' if cid in {c['id'] for c in tomllib.loads((UNI / 'components.toml').read_text(encoding='utf-8'))['component']} else 'ERROR',
                f'archive component: {item}')''',
         '''        if item.startswith('component:'):
            cid = item.split(':', 1)[1]
            ids = {c['id'] for c in tomllib.loads((UNI / 'components.toml').read_text(encoding='utf-8'))['component']}
            if cid in ids:
                add('PASS', f'archive component: {item}')
            elif (ROOT / 'drivers' / cid).is_dir():
                add('WARN', f'archive component is a board module without a catalog entry: {item}',
                    'needs patches/unixnu/unixnu-components-lumingufs.patch')
            else:
                add('ERROR', f'archive component: {item}')'''),
    ])


def catalog_patch():
    TMP.mkdir(parents=True, exist_ok=True)
    original = (UNI / 'components.toml').read_text(encoding='utf-8')
    entry = '''
[[component]]
id = "LumingUfs"
repository_id = 0   # [placeholder] assign when the source repository is published
kind = "driver"
function = "SM8735 UFS transport and luming SHNGROOT storage"
scope = "board"
repository = "https://github.com/REQUIRED_OWNER/UniXNU-luming-ufs.git"   # [placeholder]
revision = "local"   # device module; published revision TBD
path = "drivers/LumingUfs"
hardware = ["SM8735 UFS controller", "apps_smmu stream 0x60"]
os_abi = ["ipados-17.7.11-21H461"]
board_dependencies = ["luming userdata SHNGROOT layout", "SM8735 GCC offsets and qmp-v4-niobe PHY hand-off"]
verified_devices = []
dependencies = ["VirtioMmioBlock", "VerifiedRoot"]
source_files = ["LumingUfs.cpp"]
runtime_identifiers = ["NativeUfs", "NativeUfs.cpp", "LumingUfs.cpp", "org.blu-sharky.NativeUfs"]
build_stage = "kernel"
build = ["build-arm-driver.py", "LumingUfs"]
outputs = ["build/luming-ufs/libLumingUfs.a"]
'''
    modified = original.rstrip('\n') + '\n' + entry
    old = TMP / 'orig'; new = TMP / 'new'
    for d in (old, new):
        d.mkdir(parents=True, exist_ok=True)
    (old / 'components.toml').write_text(original, encoding='utf-8')
    (new / 'components.toml').write_text(modified, encoding='utf-8')
    diff = subprocess.run([GIT, 'diff', '--no-index', '--no-color', str(old / 'components.toml'), str(new / 'components.toml')],
                          capture_output=True, text=True).stdout
    diff = diff.replace(str(old), 'a').replace(str(new), 'b')
    diff = re.sub(r'^diff --git a.*components\.toml b.*components\.toml$', 'diff --git a/components.toml b/components.toml', diff, flags=re.M)
    diff = re.sub(r'^--- a.*components\.toml$', '--- a/components.toml', diff, flags=re.M)
    diff = re.sub(r'^\+\+\+ b.*components\.toml$', '+++ b/components.toml', diff, flags=re.M)
    write('patches/unixnu/unixnu-components-lumingufs.patch', diff)
    # patched UniXNU copy for local validation
    import shutil
    if (TMP / 'UniXNU').exists():
        shutil.rmtree(TMP / 'UniXNU')
    shutil.copytree(UNI, TMP / 'UniXNU', ignore=shutil.ignore_patterns('.git', 'drivers', 'package', 'assets', 'docs', 'tests', 'examples', 'kits', 'patches', 'profiles'))
    (TMP / 'UniXNU' / 'components.toml').write_text(modified, encoding='utf-8')
    print(f'wrote patches/unixnu/unixnu-components-lumingufs.patch and patched copy {TMP / "UniXNU"}')


def wire_ci():
    # f2-luming-ci.sh: run check-luming.py after the skeleton audit
    anchor = """else:
    warnings.append('scripts/check-skeleton.py is missing (cannot audit skeleton readiness)')
"""
    addition = """
check_luming_script = device / 'scripts' / 'check-luming.py'
if check_luming_script.is_file():
    import subprocess
    proc = subprocess.run([sys.executable, str(check_luming_script), '--device', str(device)],
                          cwd=str(device), capture_output=True, text=True)
    planned.append(f'check-luming.py: exit {proc.returncode}')
    for line in (proc.stdout + proc.stderr).splitlines():
        line = line.strip()
        if line.startswith('[ERROR]'):
            blockers.append('check-luming: ' + line[len('[ERROR]'):].strip())
        elif line.startswith('[WARN]'):
            warnings.append('check-luming: ' + line[len('[WARN]'):].strip())
else:
    warnings.append('scripts/check-luming.py is missing (format-2 preflight not available)')
"""
    edit('scripts/ci/f2-luming-ci.sh', [(anchor, anchor + addition)])

    # macos.yml: add the explicit preflight call in the device preflight step
    edit('.github/workflows/macos.yml', [
        ('          bash device/scripts/ci/f2-luming-ci.sh preflight',
         '          python3 device/scripts/check-luming.py --device device --json ci-artifacts/check-luming.json\n'
         '          bash device/scripts/ci/f2-luming-ci.sh preflight'),
    ])

    # porting-record workflow: apply the catalog patch before the official check (self-contained)
    write('.github/workflows/porting-record.yml', '''name: Porting record

# [adapted] sheng-style porting-record check plus the local LumingUfs catalog entry patch required
# until UniXNU carries the component (patches/unixnu/unixnu-components-lumingufs.patch).

on: [push, pull_request]

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/checkout@v4
        with:
          repository: UniXNU/UniXNU
          ref: main
          path: tools
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Apply the local LumingUfs catalog entry
        run: |
          git -C tools apply ../patches/unixnu/unixnu-components-lumingufs.patch
      - name: Validate structure and changed areas
        env:
          BASE: ${{ github.event.pull_request.base.sha || github.event.before }}
          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
        run: |
          if [[ -z "$BASE" || "$BASE" =~ ^0+$ ]]; then
            BASE="refs/remotes/origin/$DEFAULT_BRANCH"
          fi
          python3 tools/scripts/porting-record.py check --device .
''')
    # macos.yml: apply the catalog patch to the UniXNU checkout before resolution
    edit('.github/workflows/macos.yml', [
        ('      - name: Check the inputs',
         '      - name: Apply the local LumingUfs catalog entry\n'
         '        run: git -C unixnu apply device/patches/unixnu/unixnu-components-lumingufs.patch\n\n'
         '      - name: Check the inputs'),
    ])


def main():
    check_skeleton_accept_modules()
    catalog_patch()
    wire_ci()
    print('graft pass 2 done')


if __name__ == '__main__':
    main()
