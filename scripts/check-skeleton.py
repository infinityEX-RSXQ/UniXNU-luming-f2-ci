#!/usr/bin/env python3
"""Host-side static validation for the f2-luming format-2 skeleton.

Runs offline on Windows (bundled Python 3.12). It does NOT build anything; it checks that the
format-2 board resolves structurally against the local UniXNU reference checkout:
  - board.toml schema/fields, OS profile and component IDs
  - config fragments + patch series (arch:/soc:/os:/device:) resolve to real files
  - every series entry exists relative to its series directory
  - DTS entry/include exists and the memory node size matches payload.dram_size
  - ADT tables/bootimg/userdata/prelink sanity (27 AMFI+PMGR roots, early init, trust pin)
  - known external inputs (firmware, seed, data, luming UFS component) reported as MISSING
Usage: python scripts/check-skeleton.py [--unixnu DIR]
Exit code 0 if no ERROR (WARN/MISSING allowed); 1 otherwise.
"""
import argparse
import re
import sys
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
RESULTS = []


def add(level, check, detail=''):
    RESULTS.append((level, check, detail))


def resolve_base(prefix, board):
    if prefix == 'arch':
        return UNI / 'profiles/arch/arm64'
    if prefix == 'os':
        return UNI / 'profiles/os' / board['board']['os_profile']
    if prefix == 'soc':
        return ROOT / 'soc'
    if prefix == 'device':
        return ROOT
    raise ValueError(f'unknown prefix {prefix}')


def split_ref(ref, board):
    if ':' not in ref:
        return None, ref
    prefix, path = ref.split(':', 1)
    return prefix, path


def check_toml():
    for path in sorted(ROOT.rglob('*.toml')):
        try:
            tomllib.loads(path.read_text(encoding='utf-8'))
            add('PASS', f'toml parse: {path.relative_to(ROOT)}')
        except Exception as exc:  # noqa: BLE001
            add('ERROR', f'toml parse: {path.relative_to(ROOT)}', str(exc))


def check_board(board):
    board_t = board.get('board', {})
    for key in ('name', 'soc', 'soc_source', 'os_profile', 'kit'):
        if not board_t.get(key):
            add('ERROR', f'board.{key} missing')
        else:
            add('PASS', f'board.{key} = {board_t[key]}')
    if board.get('schema_version') != 2:
        add('ERROR', 'schema_version must be 2')
    else:
        add('PASS', 'schema_version = 2')
    profile = UNI / 'profiles/os' / board_t.get('os_profile', '')
    if not (profile / 'profile.toml').is_file():
        add('ERROR', f'os_profile not found in local UniXNU: {profile}')
    else:
        add('PASS', f'os_profile exists: {board_t["os_profile"]}')
    catalog = {c['id']: c for c in tomllib.loads((UNI / 'components.toml').read_text(encoding='utf-8'))['component']}
    selected = list(board.get('components', {}).get('include', []))
    if not selected:
        add('ERROR', 'components.include empty')
    pending = list(selected)
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
    add('PASS', f'components: {len(selected)} selected incl dependencies: {", ".join(sorted(selected))}')


def check_kernel(board):
    kernel = board.get('kernel', {})
    defconfig = ROOT / 'configs' / kernel.get('defconfig', '')
    if defconfig.is_file():
        add('PASS', f'defconfig exists: {defconfig.relative_to(ROOT)}')
    else:
        add('ERROR', f'defconfig missing: {kernel.get("defconfig")}')
    for ref in kernel.get('config_fragments', []):
        prefix, rel = split_ref(ref, board)
        path = resolve_base(prefix, board) / rel
        if path.is_file():
            add('PASS', f'config fragment {ref}')
        else:
            add('ERROR', f'config fragment missing: {ref}', str(path))
    for ref in kernel.get('patch_series', []):
        prefix, rel = split_ref(ref, board)
        series = resolve_base(prefix, board) / rel
        if not series.is_file():
            add('ERROR', f'patch series missing: {ref}', str(series))
            continue
        add('PASS', f'patch series {ref}')
        for line in series.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('component:'):
                # component files live in an unpublished checkout; the resolver owns them.
                add('WARN', f'  component series entry (resolver-owned): {line}')
                continue
            if ':' in line and not line.startswith('/') and line.split(':', 1)[0] in ('arch', 'soc', 'os', 'device'):
                pfx, sub = line.split(':', 1)
                base = resolve_base(pfx, board)
                entry = (base / sub).resolve()
            else:
                entry = (series.parent / line).resolve()
            if entry.is_file():
                add('PASS', f'  series entry {ref}: {line}')
            else:
                add('ERROR', f'  series entry missing in {ref}: {line}', str(entry))
    archives = kernel.get('archives', [])
    for item in archives:
        if item.startswith('component:'):
            cid = item.split(':', 1)[1]
            ids = {c['id'] for c in tomllib.loads((UNI / 'components.toml').read_text(encoding='utf-8'))['component']}
            if cid in ids:
                add('PASS', f'archive component: {item}')
            elif (ROOT / 'drivers' / cid).is_dir():
                add('WARN', f'archive component is a board module without a catalog entry: {item}',
                    'needs patches/unixnu/unixnu-components-lumingufs.patch')
            else:
                add('ERROR', f'archive component: {item}')
        else:
            name = item.split()[0]
            if (UNI / 'scripts' / name).is_file() or (ROOT / 'scripts' / name).is_file():
                add('PASS', f'archive builder present: {name}')
            else:
                add('MISSING', f'archive builder not present: {name}', 'expected from the dada clone recipe')
    prelink = kernel.get('prelink', {})
    roots = prelink.get('roots', [])
    if roots:
        add('PASS' if len(roots) == 27 else 'ERROR', f'prelink roots = {len(roots)} (dada proven shape 27)')
        for required in ('com.apple.driver.AppleMobileFileIntegrity', 'com.apple.driver.ApplePMGR',
                         'com.apple.security.sandbox', 'com.apple.security.AppleImage4'):
            add('PASS' if required in roots else 'ERROR', f'prelink root {required}')
        if prelink.get('early_security_init'):
            add('PASS', 'early_security_init present (AMFI initializer)')
        else:
            add('ERROR', 'early_security_init missing (proven AMFI shape needs it)')
    else:
        add('MISSING', 'prelink roots not set in board.toml')


def check_adt_payload(board):
    dt = board.get('device_tree', {})
    source = dt.get('source', '')
    src_path = ROOT / source.split(':', 1)[1] if ':' in source else ROOT / source
    if src_path.is_file():
        add('PASS', f'board DTS exists: {src_path.relative_to(ROOT)}')
    else:
        add('ERROR', f'board DTS missing: {src_path}')
    for ref in dt.get('include_dirs', []):
        prefix, rel = split_ref(ref, board)
        d = resolve_base(prefix, board) / rel
        add('PASS' if d.is_dir() else 'ERROR', f'DTS include dir: {ref}', str(d))
    if src_path.is_file():
        text = src_path.read_text(encoding='utf-8')
        if 'sm8735.dtsi' in text and (ROOT / 'soc/dts/sm8735.dtsi').is_file():
            add('PASS', 'sm8735.dtsi include present')
        mem = re.search(r'memory@[0-9a-fA-F]+\s*\{[^}]*reg\s*=\s*<([^>]+)>', text)
        payload = board.get('payload', {})
        if mem:
            cells = [int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+|\b\d+\b', mem.group(1))]
            size = (cells[2] << 32) | cells[3]
            dram = int(str(payload.get('dram_size', '0')), 0)
            add('PASS' if size == dram else 'ERROR', f'ADT DRAM window: dts {hex(size)} vs payload {hex(dram)}')
        else:
            add('ERROR', 'memory@ node reg not parsed')
        if 'splash_region' in text and '0xfc800000' in text:
            add('PASS', 'splash_region 0xfc800000 present')
        else:
            add('ERROR', 'splash_region missing')
    payload = board.get('payload', {})
    if payload.get('volume') and len(payload['volume']) <= 11:
        add('PASS', f'payload volume = {payload["volume"]} ({len(payload["volume"])} chars)')
    else:
        add('ERROR', 'payload.volume missing/too long')
    boot = board.get('bootimg', {})
    img = boot.get('image', {})
    add('PASS' if img.get('header_version') == 4 else 'ERROR', 'bootimg header_version v4')
    add('PASS' if img.get('pagesize') == 4096 else 'ERROR', 'bootimg pagesize 4096')
    splash = boot.get('dtb_node', [])
    if any(n.get('path', '').endswith('/splash_region') for n in splash):
        add('PASS', 'bootimg splash dtb node')
    else:
        add('ERROR', 'bootimg splash dtb node missing')
    adt = payload.get('adt', {})
    for key in ('chip_id', 'owned_memory_size', 'root_match_volume_uuid', 'unique_chip_id'):
        add('PASS' if adt.get(key) else 'ERROR', f'payload.adt.{key} = {adt.get(key)!r}')
    if str(adt.get('root_match_volume_uuid')).upper() == '04769D26-2CA0-4825-B443-E2E5F88300F2':
        add('PASS', 'root UUID matches the 21H461 SystemOS volume')
    else:
        add('MISSING', 'root UUID is a placeholder', 'extract/verify from the built SHNGROOT image')
    trust = payload.get('trust_cache_sha256', [])
    add('PASS' if trust else 'WARN', f'trust_cache pins = {len(trust)}')
    userdata = board.get('userdata', {})
    if userdata.get('first_lba') and userdata.get('last_lba') and userdata.get('first_lba') < userdata.get('last_lba'):
        add('PASS', f'userdata LBAs {userdata["first_lba"]}..{userdata["last_lba"]}')
    else:
        add('ERROR', 'userdata LBAs invalid')
    adt_tables = board.get('adt', {})
    if 'chosen' in adt_tables:
        add('PASS', 'typed [adt] tables present')


def check_firmware(board):
    fw = board.get('firmware', {})
    for key in ('dsc', 'fd', 'config'):
        add('PASS' if fw.get(key) else 'ERROR', f'firmware.{key} = {fw.get(key)!r}')
    preflight = fw.get('preflight', [])
    for item in preflight:
        path = ROOT / Path(item).name if Path(item).name != item else ROOT / item
        if (ROOT / 'scripts/reference' / Path(item).name).is_file():
            add('MISSING', f'firmware preflight is the format-1 script: {item}', 'rewrite for format 2')
        else:
            add('MISSING', f'firmware preflight missing: {item}')
    add('MISSING', 'external uefi-luming checkout', 'owned by uefi-builder; firmware/README.md')
    add('MISSING', 'FD base/size 0xA7100000/0x300000 unverified', 'measure luming reserved region')


def check_external_gaps():
    for name in ('drivers/LumingUfs', 'drivers/LumingDisplayTouch'):
        add('MISSING', f'component source: {name}', 'not a format-2 component yet')
    for name in ('data.dbr', 'trustcache.bundle'):
        add('MISSING', f'payload input: {name}', 'provided at build time, never committed')
    for name in ('.github/workflows/porting-record.yml', '.github/workflows/macos.yml'):
        add('PASS' if (ROOT / name).is_file() else 'ERROR', f'workflow {name}')


def main():
    global UNI
    ap = argparse.ArgumentParser()
    ap.add_argument('--unixnu', type=Path, default=ROOT.parents[1] / 'unixnu-format2/UniXNU')
    args = ap.parse_args()
    UNI = args.unixnu.resolve()
    if not (UNI / 'components.toml').is_file():
        print(f'FATAL: UniXNU reference not found at {UNI}')
        return 2
    add('PASS', f'UniXNU reference: {UNI}')
    check_toml()
    board = tomllib.loads((ROOT / 'board.toml').read_text(encoding='utf-8'))
    check_board(board)
    check_kernel(board)
    check_adt_payload(board)
    check_firmware(board)
    if (ROOT / 'porting.toml').is_file():
        record = tomllib.loads((ROOT / 'porting.toml').read_text(encoding='utf-8'))
        add('PASS', f'porting.toml: {len(record.get("area", []))} areas')
    else:
        add('ERROR', 'porting.toml missing')
    check_external_gaps()

    counts = {'ERROR': 0, 'WARN': 0, 'MISSING': 0, 'PASS': 0}
    for level, check, detail in RESULTS:
        counts[level] = counts.get(level, 0) + 1
        flag = {'PASS': 'PASS', 'WARN': 'WARN', 'MISSING': 'MISS', 'ERROR': 'ERR '}[level]
        print(f'[{flag}] {check}' + (f'  -> {detail}' if detail else ''))
    print(f'\nsummary: {counts["PASS"]} pass, {counts["MISSING"]} missing, {counts["WARN"]} warn, {counts["ERROR"]} error')
    return 0 if counts['ERROR'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
