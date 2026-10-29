#!/usr/bin/env bash
# f2-luming-ci.sh — format-2 (route ①) device-side CI helper for the Xiaomi Civi 5 Pro
# (luming, SM8735). Deploy target: `scripts/ci/f2-luming-ci.sh` in the format-2 device
# repository (agents/f2-luming/ is the skeleton).
#
# The primary macOS workflow (.github/workflows/macos.yml in this device repo) invokes:
#   bash scripts/ci/f2-luming-ci.sh dry-run     -> checklist + blocker list (always exit 0)
#   bash scripts/ci/f2-luming-ci.sh preflight   -> strict board/input validation (exit 1 on blockers)
#   bash scripts/ci/f2-luming-ci.sh pre_build   -> stage proprietary inputs, write ci-inputs.json
#   bash scripts/ci/f2-luming-ci.sh collect     -> stage artifacts + SHA256SUMS + build-manifest.json
#
# It never prints URLs/secrets (they arrive through masked workflow inputs or repository secrets)
# and never writes Apple-derived material into the repository.
set -euo pipefail

DEVICE_DIR="${UNIXNU_DEVICE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
BUILD_ROOT="${UNIXNU_BUILD_ROOT:-$DEVICE_DIR}"
MODE="${1:-dry-run}"
STEPS="${STEPS:-kernel package firmware payload bootimg}"
DEFCONFIG="${DEFCONFIG:-luming_defconfig}"
RUNNER_TEMP="${RUNNER_TEMP:-/tmp}"
INPUTS_DIR="$RUNNER_TEMP/f2-luming-inputs"
ART_DIR="${GITHUB_WORKSPACE:-$DEVICE_DIR}/ci-artifacts"
ALLOW_INCOMPLETE="${ALLOW_INCOMPLETE:-0}"
mkdir -p "$ART_DIR"

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

board_check() {
  # Emits a JSON object {summary, blockers, warnings, planned} on stdout.
  python3 - "$DEVICE_DIR" "$STEPS" "$DEFCONFIG" "$INPUTS_DIR" <<'PY'
import json, os, sys
from pathlib import Path

device = Path(sys.argv[1]).resolve()
steps = sys.argv[2].split()
defconfig = sys.argv[3]
inputs_dir = Path(sys.argv[4])
blockers, warnings, planned = [], [], []

def require(cond, message):
    if not cond:
        blockers.append(message)

def warn(cond, message):
    if not cond:
        warnings.append(message)

board_path = device / 'board.toml'
if not board_path.is_file():
    print(json.dumps({'summary': 'no board.toml', 'blockers': [f'{board_path} missing'], 'warnings': [], 'planned': []}, indent=2))
    sys.exit(0)
try:
    import tomllib
    board = tomllib.loads(board_path.read_text(encoding='utf-8'))
except Exception as error:  # noqa: BLE001 - report the parse error verbatim
    print(json.dumps({'summary': 'board.toml parse failed', 'blockers': [str(error)], 'warnings': [], 'planned': []}, indent=2))
    sys.exit(0)

def get(*keys):
    value = board
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value

summary = (get('board', 'name') or '<unnamed>') + ' / ' + (get('board', 'soc') or '<no soc>')
require(board.get('schema_version') == 2, 'board.toml schema_version must be 2 (format 2)')
for key in ('board', 'kernel', 'components', 'device_tree', 'firmware', 'payload', 'bootimg'):
    require(key in board, f'board.toml is missing [{key}]')

kernel = board.get('kernel') or {}
prelink = kernel.get('prelink') or {}
roots = prelink.get('roots') or []
require(kernel.get('defconfig') == defconfig, f"board [kernel].defconfig is {kernel.get('defconfig')!r}, expected {defconfig!r}")
config_path = device / 'configs' / defconfig
require(config_path.is_file(), f"{config_path} missing (configs/luming_defconfig is not in the skeleton yet)")
require(bool(kernel.get('archive') is not None or kernel.get('archives')), 'board [kernel].archives is empty')
require(bool(kernel.get('config_fragments')), 'board [kernel].config_fragments is empty')
require(bool(kernel.get('patch_series')), 'board [kernel].patch_series is empty')
require(bool(roots), 'board [kernel.prelink].roots is empty')
require(prelink.get('slide') is not None, 'board [kernel.prelink].slide is missing')
require('early_security_init' in prelink, 'board [kernel.prelink].early_security_init is missing')
if roots:
    planned.append(f'prelink roots: {len(roots)} (dada/sheng format-2 shape)')

components = board.get('components') or {}
require(bool(components.get('include')), 'board [components].include is empty')
planned.append('components: ' + ', '.join(components.get('include') or []))

device_tree = board.get('device_tree') or {}
source = (device_tree.get('source') or '').removeprefix('device:')
if source:
    require((device / source).is_file(), f'device tree source device/{source} missing')
else:
    blockers.append('board [device_tree].source is missing')
for pattern in ('dts/luming.dts',):
    if not (device / pattern).is_file():
        warnings.append(f'{pattern} is absent from the skeleton (needed by the device tree step)')

for series in kernel.get('patch_series') or []:
    if series.startswith('device:'):
        rel = series.split(':', 1)[1]
        require((device / rel).is_file(), f'device patch series {rel} missing')
for frag in kernel.get('config_fragments') or []:
    kind, rel = (frag.split(':', 1) + [''])[:2] if ':' in frag else ('', frag)
    if kind == 'device':
        require((device / rel).is_file(), f'device config fragment {rel} missing')

firmware = board.get('firmware') or {}
for key in ('config', 'dsc', 'fd'):
    require(bool(firmware.get(key)), f'board [firmware].{key} is empty')
for preflight in firmware.get('preflight') or []:
    if preflight.startswith('scripts/'):
        require((device / preflight).is_file(), f'firmware preflight script device/{preflight} missing')
uefi = os.environ.get('UNIXNU_UEFI') or ''
if 'firmware' in steps:
    require(bool(uefi), 'firmware step needs UNIXNU_UEFI (workflow input uefi_repository)')
    if uefi:
        require(Path(uefi).is_dir(), f'UEFI checkout {uefi} missing')
payload = board.get('payload') or {}
require(bool(payload.get('volume')), 'board [payload].volume is empty')
require(bool(payload.get('size_mib')), 'board [payload].size_mib is empty')
require(bool(payload.get('kernel_args')), 'board [payload].kernel_args is empty')
payload_adt = payload.get('adt') or {}
require(bool(payload_adt.get('unique_chip_id')), 'board [payload.adt].unique_chip_id is empty')
if payload_adt.get('unique_chip_id') == 'required' and not os.environ.get('UNIXNU_UNIQUE_CHIP_ID'):
    if 'payload' in steps:
        blockers.append('payload step needs UNIXNU_UNIQUE_CHIP_ID (repository secret)')
uuid_value = str(payload_adt.get('root_match_volume_uuid') or '')
if not uuid_value or uuid_value.startswith('REQUIRED_'):
    warnings.append('board [payload.adt].root_match_volume_uuid is still a placeholder')
bootimg = board.get('bootimg') or {}
image = bootimg.get('image') or {}
require(image.get('header_version') == 4, 'board [bootimg.image].header_version must be 4')
require(bool(bootimg.get('dtb_node')), 'board [[bootimg.dtb_node]] is empty')
planned.append('boot image: v4 pagesize=%s' % image.get('pagesize', '?'))

skeleton_script = device / 'scripts' / 'check-skeleton.py'
skeleton_missing, skeleton_warn = [], []
if skeleton_script.is_file():
    import subprocess
    skeleton_args = [sys.executable, str(skeleton_script)]
    core_dir = os.environ.get('UNIXNU_CORE', '')
    if core_dir:
        skeleton_args += ['--unixnu', core_dir]
    proc = subprocess.run(skeleton_args, cwd=str(device), capture_output=True, text=True)
    planned.append(f'check-skeleton.py: exit {proc.returncode}')
    for line in (proc.stdout + proc.stderr).splitlines():
        line = line.strip()
        if line.startswith('[MISS]'):
            skeleton_missing.append(line[len('[MISS]'):].strip())
        elif line.startswith('[WARN]'):
            skeleton_warn.append(line[len('[WARN]'):].strip())
else:
    warnings.append('scripts/check-skeleton.py is missing (cannot audit skeleton readiness)')

check_luming_script = device / 'scripts' / 'check-luming.py'
if check_luming_script.is_file():
    import subprocess
    check_args = [sys.executable, str(check_luming_script), '--device', str(device)]
    core_dir = os.environ.get('UNIXNU_CORE', '')
    if core_dir:
        check_args += ['--unixnu', core_dir]
    proc = subprocess.run(check_args, cwd=str(device), capture_output=True, text=True)
    planned.append(f'check-luming.py: exit {proc.returncode}')
    for line in (proc.stdout + proc.stderr).splitlines():
        line = line.strip()
        if line.startswith('[ERROR]'):
            blockers.append('check-luming: ' + line[len('[ERROR]'):].strip())
        elif line.startswith('[WARN]'):
            warnings.append('check-luming: ' + line[len('[WARN]'):].strip())
else:
    warnings.append('scripts/check-luming.py is missing (format-2 preflight not available)')

input_checks = {
    'kernelcache': inputs_dir / 'kernelcache.macho',
    'trustcache': inputs_dir / 'trustcache',
    'data.dbr': inputs_dir / 'data.dbr',
}
for name, path in input_checks.items():
    if path.is_file():
        planned.append(f'{name}: staged {path.stat().st_size} B')
if 'kernel' in steps and not (inputs_dir / 'kernelcache.macho').is_file() and not os.environ.get('UNIXNU_IPSW'):
    warnings.append('kernel step has no kernelcache input and UNIXNU_IPSW is unset; board.toml [ipsw] must supply the target')

print(json.dumps({'summary': summary, 'blockers': blockers, 'warnings': warnings,
                  'skeleton_missing': skeleton_missing, 'skeleton_warn': skeleton_warn,
                  'planned': planned}, indent=2))
PY
}

write_checklist() {
  # $1 = output file, $2 = JSON from board_check
  python3 - "$1" "$2" "$DEVICE_DIR" "$STEPS" "$DEFCONFIG" <<'PY'
import json, sys
from pathlib import Path
out, raw, device, steps, defconfig = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
lines = [
    '# format-2 luming CI checklist\n',
    f'- device repository: `{device}`',
    f'- defconfig: `{defconfig}`',
    f'- steps: `{steps}`',
    f'- board: {raw["summary"]}',
    '',
    '## Blockers',
] + [f'- {item}' for item in raw['blockers']] + ['', '## Skeleton gaps (scripts/check-skeleton.py)'] + (
    [f'- {item}' for item in raw.get('skeleton_missing') or []] or ['- none']) + ['', '## Skeleton warnings'] + (
    [f'- {item}' for item in raw.get('skeleton_warn') or []] or ['- none']) + ['', '## Warnings'] + (
    [f'- {item}' for item in raw['warnings']]) + ['', '## Planned work']
lines += [f'- {item}' for item in raw['planned']]
lines += ['', '## Planned commands (executed by the macOS workflow)']
lines += [
    '```sh',
    './unixnu defconfig "$DEFCONFIG" --device "$UNIXNU_DEVICE"',
    './unixnu fetch --device "$UNIXNU_DEVICE"',
    './unixnu status --device "$UNIXNU_DEVICE" --json',
    './unixnu build kernel --device "$UNIXNU_DEVICE" --kernelcache "$UNIXNU_KERNELCACHE"',
    './unixnu build package --device "$UNIXNU_DEVICE"',
    './unixnu build firmware --device "$UNIXNU_DEVICE" --uefi "$UNIXNU_UEFI"',
    './unixnu build payload --device "$UNIXNU_DEVICE" --unique-chip-id "$UNIXNU_UNIQUE_CHIP_ID"',
    './unixnu bootimg --device "$UNIXNU_DEVICE" --uefi "$UNIXNU_UEFI" --fd <FD> --dtb <DTB>',
    '```',
    '',
    '## Build-time inputs (never committed)',
    '- kernelcache or IPSW (kernelcache_url/ipsw_url input or UNIXNU_IPSW secret)',
    '- UNIXNU_UNIQUE_CHIP_ID secret (payload platform seed)',
    '- optional trust cache bundle / Data seed (.dbr) URLs',
    '- uefi-luming checkout or prebuilt FD + compiled DTB for bootimg',
]
Path(out).write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY
}

case "$MODE" in
  dry-run)
    raw="$(board_check)"
    write_checklist "$ART_DIR/DRY-RUN.md" "$raw"
    python3 - "$raw" <<'PY'
import json, sys
raw = json.loads(sys.argv[1])
for item in raw['blockers']:
    print('BLOCKER:', item)
for item in raw['warnings']:
    print('WARNING:', item)
for item in raw['planned']:
    print('PLAN:', item)
print(f"blockers={len(raw['blockers'])} warnings={len(raw['warnings'])}")
PY
    if [ "${GITHUB_STEP_SUMMARY:-}" ]; then
      cat "$ART_DIR/DRY-RUN.md" >> "$GITHUB_STEP_SUMMARY"
    fi
    printf '%s\n' "$raw" > "$ART_DIR/preflight.json"
    exit 0
    ;;
  preflight)
    raw="$(board_check)"
    printf '%s\n' "$raw" > "$ART_DIR/preflight.json"
    python3 - "$raw" <<'PY'
import json, sys
raw = json.loads(sys.argv[1])
for item in raw['blockers']:
    print('BLOCKER:', item)
for item in raw['warnings']:
    print('WARNING:', item)
# check-skeleton.py MISS lines are long-lived external gaps owned by uefi-builder /
# device-builder (firmware checkout, FD geometry, build-time seeds, source components).
# They are audited and printed, but they do not block the kernel-only CI target.
soft_skeleton = list(raw.get('skeleton_missing') or []) + list(raw.get('skeleton_warn') or [])
for item in soft_skeleton:
    print('WARNING:', item)
if raw['blockers']:
    print(f"{len(raw['blockers'])} blocker(s); fix them or use the dry-run mode")
    sys.exit(1)
print('preflight: OK')
PY
    ;;
  pre_build)
    mkdir -p "$INPUTS_DIR"
    python3 - "$INPUTS_DIR" "$ART_DIR" <<'PY'
import hashlib, json, os, sys
from pathlib import Path
inputs, art = Path(sys.argv[1]), Path(sys.argv[2])
record = {}
for path in sorted(inputs.glob('*')):
    if not path.is_file():
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    record[path.name] = {'bytes': path.stat().st_size, 'sha256': digest}
if 'kernelcache.macho' in record:
    expected = os.environ.get('KERNELCACHE_SHA256', '')
    if expected and record['kernelcache.macho']['sha256'] != expected:
        raise SystemExit('kernelcache sha256 mismatch: %s != %s' % (record['kernelcache.macho']['sha256'], expected))
    print('kernelcache:', record['kernelcache.macho']['sha256'])
art.mkdir(parents=True, exist_ok=True)
(art / 'ci-inputs.json').write_text(json.dumps({'inputs': record}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'inputs': record}, indent=2))
PY
    ;;
  collect)
    python3 - "$BUILD_ROOT" "$ART_DIR" <<'PY'
import hashlib, json, os, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
device, art = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
art.mkdir(parents=True, exist_ok=True)
candidates = []
for pattern in ('out/**/kernel/kernel.macho', 'out/**/payload/**', 'out/**/boot/**', 'out/**/package/Build/**/*.efi', 'out/**/package/Build/**/*.fd', 'out/**/package/Build/**/*.json', 'out/**/logs/*.log'):
    candidates.extend(p for p in device.glob(pattern) if p.is_file())
staged, manifest = art / 'files', []
for path in sorted(set(candidates)):
    rel = path.relative_to(device)
    dest = staged / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    manifest.append({'path': rel.as_posix(), 'bytes': dest.stat().st_size, 'sha256': digest})
(art / 'build-manifest.json').write_text(json.dumps({
    'device': str(device), 'steps': os.environ.get('STEPS', ''),
    'created_at': datetime.now(timezone.utc).isoformat(), 'files': manifest}, indent=2) + '\n', encoding='utf-8')
(art / 'SHA256SUMS').write_text(''.join(f"{m['sha256']}  {m['path']}\n" for m in manifest), encoding='ascii')
print('\n'.join(f"{m['sha256']}  {m['path']}" for m in manifest))
PY
    ;;
  *)
    usage
    exit 2
    ;;
esac
