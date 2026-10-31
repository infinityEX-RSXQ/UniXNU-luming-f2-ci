#!/usr/bin/env python3
"""format-2 preflight for the Xiaomi Civi 5 Pro (luming, SM8735) device repository.

Adapted from UniXNU-sheng `scripts/check-sheng.py` (compiled-DT / platform-interval checks) and
dada `scripts/check-dada.py` (board/firmware/UFS/archive checks), reduced to the luming skeleton.
It is also the script referenced by `board.toml [firmware].preflight` and is run by
`scripts/ci/f2-luming-ci.sh preflight` / `.github/workflows/macos.yml`.

Design: hard errors are inconsistencies inside this repository (wrong values, missing referenced
files, archive order violations). Known external gaps (unpublished LumingUfs catalog entry,
firmware checkout, payload seeds) are WARN so CI stays green while the gap list tracks them.

Usage:
  python scripts/check-luming.py [--device DIR] [--unixnu DIR] [--uefi DIR] [--json FILE]
Exit code 0 when there is no ERROR, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
import tomllib

HERE = Path(__file__).resolve()
ROWS: list[tuple[str, str, str]] = []


def add(level: str, name: str, detail: str = '') -> None:
    ROWS.append((level, name, detail))


def read(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except OSError:
        add('ERROR', f'{label}: missing', str(path))
        return ''


def resolve_prefix(prefix: str, board: dict, device: Path, unixnu: Path) -> Path:
    if prefix == 'device':
        return device
    if prefix == 'soc':
        return device / 'soc'
    if prefix == 'arch':
        return unixnu / 'profiles/arch/arm64'
    if prefix == 'os':
        return unixnu / 'profiles/os' / board['board']['os_profile']
    raise ValueError(prefix)


def check_board(device: Path, unixnu: Path, board: dict) -> None:
    if board.get('schema_version') != 2:
        add('ERROR', 'board.toml schema_version must be 2 (format 2)')
    for key in ('name', 'soc', 'soc_source', 'os_profile', 'kit'):
        if not board.get('board', {}).get(key):
            add('ERROR', f'board.{key} missing')
    if not (unixnu / 'profiles/os' / str(board['board'].get('os_profile', '')) / 'profile.toml').is_file():
        add('ERROR', f'OS profile not found in UniXNU: {board["board"].get("os_profile")}')
    else:
        add('PASS', f'OS profile {board["board"]["os_profile"]} exists')

    # component catalog + board modules
    catalog_doc = tomllib.loads(read(unixnu / 'components.toml', 'UniXNU components.toml'))
    catalog = {item['id']: item for item in catalog_doc.get('component', [])}
    catalog = {key: value for key, value in catalog.items() if key}
    selected = list(board.get('components', {}).get('include', []))
    missing_catalog = []
    pending = list(selected)
    while pending:
        cid = pending.pop()
        if cid in catalog:
            for dep in catalog[cid].get('dependencies', []):
                if dep not in selected:
                    selected.append(dep)
                    pending.append(dep)
        elif (device / 'drivers' / cid).is_dir():
            # board module: a directory in this repository, awaiting the upstream catalog entry
            missing_catalog.append(cid)
            add('WARN', f'component {cid} is a board module without a catalog entry',
                'needs a UniXNU components.toml entry (patches/unixnu/unixnu-components-lumingufs.patch)')
        else:
            add('ERROR', f'component unknown to both catalog and drivers/: {cid}')
    if not missing_catalog:
        add('PASS', f'components resolve from the catalog: {", ".join(sorted(selected))}')
    required = {'LumingUfs', 'ArmDTPlatform', 'ArmCpu', 'SoftwareAES', 'RamBlock', 'XnuPrelink', 'DarwinBoot'}
    for cid in sorted(required):
        if cid not in selected:
            add('ERROR', f'components.include misses {cid}')

    # archive graph/order (dada proof: classes -> component -> bindings -> ram-block/boot-log)
    archives = board.get('kernel', {}).get('archives', [])
    def index(predicate):
        for i, item in enumerate(archives):
            if predicate(item):
                return i
        return -1
    classes = index(lambda s: s.startswith('build-storage-classes.py'))
    ufs = index(lambda s: s == 'component:LumingUfs')
    bindings = index(lambda s: s.startswith('build-storage-kext-bindings.py') and '--component LumingUfs' in s)
    ramblock = index(lambda s: s.startswith('build-luming-ram-block.py'))
    bootlog = index(lambda s: s.startswith('build-luming-boot-log.py'))
    power = index(lambda s: s.startswith('build-luming-platform-power.py'))
    order = {'classes': classes, 'LumingUfs': ufs, 'bindings': bindings, 'ram-block': ramblock,
             'boot-log': bootlog, 'platform-power': power}
    for name, idx in order.items():
        if idx < 0:
            add('WARN', f'archive plan misses {name}', 'see docs/A-FIX-CROSSWALK.md (c1)')
    if classes >= 0 and ufs >= 0 and bindings >= 0:
        if classes < ufs < bindings and (ramblock < 0 or bindings < ramblock) and (bootlog < 0 or bindings < bootlog):
            add('PASS', 'archive order storage-classes -> LumingUfs -> kext-bindings -> ram-block/boot-log')
        else:
            add('ERROR', 'archive order violates the OSMetaClass-safe order (classes, UFS, bindings, ram-block, boot-log)')
    builder_names = ('build-luming-platform-power.py', 'build-luming-ram-block.py', 'build-luming-boot-log.py',
                     'build-storage-classes.py', 'build-storage-kext-bindings.py')
    for name in builder_names:
        if (device / 'scripts' / name).is_file():
            add('PASS', f'board builder {name}')
        else:
            add('ERROR', f'board builder missing: scripts/{name}')

    # kernel config fragments/series
    for frag in board.get('kernel', {}).get('config_fragments', []):
        kind, rel = frag.split(':', 1)
        path = resolve_prefix(kind, board, device, unixnu) / rel
        add('PASS' if path.is_file() else 'ERROR', f'config fragment {frag}', str(path))
    for series in board.get('kernel', {}).get('patch_series', []):
        kind, rel = series.split(':', 1)
        path = resolve_prefix(kind, board, device, unixnu) / rel
        if not path.is_file():
            add('ERROR', f'patch series missing: {series}', str(path))
            continue
        add('PASS', f'patch series {series}')
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('component:'):
                add('WARN', f'  component-owned patch {line}')
                continue
            entry = resolve_prefix(line.split(':', 1)[0], board, device, unixnu) / line.split(':', 1)[1] \
                if ':' in line and line.split(':', 1)[0] in ('arch', 'soc', 'os', 'device') else path.parent / line
            add('PASS' if entry.is_file() else 'ERROR', f'  series entry {line}', str(entry))


def check_prelink(board: dict) -> None:
    prelink = board.get('kernel', {}).get('prelink', {})
    roots = prelink.get('roots', [])
    if len(roots) == 27:
        add('PASS', 'prelink roots = 27 (dada proven shape)')
    else:
        add('ERROR', f'prelink roots = {len(roots)} (expected 27)')
    for name in ('com.apple.driver.AppleMobileFileIntegrity', 'com.apple.driver.ApplePMGR',
                 'com.apple.security.sandbox', 'com.apple.security.AppleImage4'):
        add('PASS' if name in roots else 'ERROR', f'prelink root {name}')
    if prelink.get('early_security_init') == 'com.apple.driver.AppleMobileFileIntegrity=0xfffffff005ab4ae0':
        add('PASS', 'early_security_init restored (AMFI initializer)')
    else:
        add('ERROR', f'early_security_init wrong: {prelink.get("early_security_init")!r}')
    if prelink.get('slide') == '-0x1000000':
        add('PASS', 'prelink slide -0x1000000')
    else:
        add('ERROR', f'prelink slide wrong: {prelink.get("slide")!r}')


def check_payload_adt(board: dict) -> None:
    payload = board.get('payload', {})
    adt = payload.get('adt', {})
    dram = int(str(payload.get('dram_size', '0x0')), 0)
    if dram == 0x23ffff000:
        add('PASS', 'payload.dram_size = 0x23ffff000 (measured contiguous window)')
    else:
        add('ERROR', f'payload.dram_size unexpected: {payload.get("dram_size")}')
    if str(adt.get('root_match_volume_uuid', '')).upper() == '04769D26-2CA0-4825-B443-E2E5F88300F2':
        add('PASS', 'root_match_volume_uuid = 21H461 SystemOS UUID')
    else:
        add('ERROR', 'root_match_volume_uuid is not the 21H461 SystemOS UUID')
    if adt.get('unique_chip_id') == 'required':
        add('PASS', 'unique_chip_id = required (seed supplied at build time)')
    else:
        add('ERROR', 'unique_chip_id must be "required"')
    trust = payload.get('trust_cache_sha256', [])
    if trust and all(re.fullmatch(r'[0-9a-f]{64}', h) for h in trust):
        add('PASS', f'trust_cache pins: {len(trust)}')
    else:
        add('ERROR', 'trust_cache_sha256 must contain 64-hex pins')
    args = payload.get('kernel_args', [])
    for arg in ('sheng-pmgr=2', 'native-ufs-root=1', 'native-ufs-diagnostics=1'):
        add('PASS' if arg in args else 'WARN', f'kernel arg {arg}')
    userdata = board.get('userdata', {})
    if userdata.get('first_lba') == 3124736 and userdata.get('last_lba') == 128619514 and userdata.get('lba_bytes') == 4096:
        add('PASS', 'userdata LBAs 3124736..128619514 @4096')
    else:
        add('ERROR', f'userdata LBAs unexpected: {userdata}')
    names = [window.get('name') for window in userdata.get('windows', [])]
    if names == ['OS', 'SystemOS']:
        add('PASS', 'userdata windows OS/SystemOS (SHNGROOT recipe)')
    else:
        add('ERROR', f'userdata windows unexpected: {names}')


def check_bootimg(board: dict) -> None:
    img = board.get('bootimg', {}).get('image', {})
    checks = {'header_version': 4, 'pagesize': 4096, 'base': 0x0, 'kernel_offset': 0x8000,
              'ramdisk_offset': 0x01000000, 'tags_offset': 0x100}
    for key, value in checks.items():
        actual = img.get(key)
        add('PASS' if actual == value else 'ERROR', f'bootimg.image.{key} = {actual!r}')
    nodes = board.get('bootimg', {}).get('dtb_node', [])
    splash = [n for n in nodes if str(n.get('path', '')).endswith('/splash_region')]
    if splash:
        props = {p['name']: p.get('value') for p in splash[0].get('props', [])}
        if props.get('reg') == ['0x0', '0xfc800000', '0x0', '0x2b00000']:
            add('PASS', 'bootimg splash node 0xfc800000/0x2b00000')
        else:
            add('ERROR', f'bootimg splash reg unexpected: {props.get("reg")}')
    else:
        add('ERROR', 'bootimg splash dtb_node missing')


def check_device_tree(device: Path, board: dict) -> None:
    spec = board.get('device_tree', {})
    source = str(spec.get('source', '')).removeprefix('device:')
    path = device / source
    text = read(path, 'board DTS')
    if not text:
        return
    for include in ('sm8735.dtsi',):
        if include in text and (device / 'soc/dts' / include).is_file():
            add('PASS', f'DTS include {include}')
        else:
            add('ERROR', f'DTS include missing: {include}')
    memory = re.search(r'memory@[0-9a-fA-F]+\s*\{[^}]*reg\s*=\s*<([^>]+)>', text)
    if memory:
        cells = [int(x, 16) if x.lower().startswith('0x') else int(x, 10)
                 for x in re.findall(r'0x[0-9a-fA-F]+|\b\d+\b', memory.group(1))]
        if len(cells) < 4:
            add('ERROR', f'DTS memory reg cells unparsed: {memory.group(1)!r}')
            dram = 0
            size = -1
        else:
            size = (cells[2] << 32) | cells[3]
            dram = int(str(board.get('payload', {}).get('dram_size', '0x0')), 0)
            add('PASS' if size == dram else 'ERROR', f'DTS memory size {hex(size)} == payload.dram_size')
    else:
        add('ERROR', 'board DTS memory@ node not parsed')
    if '0xfc800000' in text and 'splash_region' in text:
        add('PASS', 'DTS splash_region 0xfc800000')
    else:
        add('ERROR', 'DTS splash_region missing')

    soc_dtsi = read(device / 'soc/dts/sm8735.dtsi', 'sm8735.dtsi')
    facts = {
        'GIC intc': ('interrupt-controller@17100000', '0x17100000', '0x17180000'),
        'UFS host': ('ufshc@1d84000', '0x1d84000', '0x3000'),
        'UFS PHY': ('phy@1d80000', 'qcom,ufs-phy-qmp-v4-niobe', '0x1d80000'),
        'VTIMER': ('virtual-timer-intid', '27', ''),
        'UART': ('serial@a9c000', '0xa9c000', '0x4000'),
    }
    for label, (needle, first, second) in facts.items():
        ok = needle in soc_dtsi and first in soc_dtsi and (not second or second in soc_dtsi)
        add('PASS' if ok else 'ERROR', f'SoC DTSI {label}')
    if 'stream' in text and '0x60' in text:
        add('PASS', 'DTS documents UFS stream 0x60')
    else:
        add('WARN', 'UFS stream 0x60 not documented in the board DTS')


def check_driver(device: Path) -> None:
    driver = device / 'drivers/LumingUfs'
    if not driver.is_dir():
        add('ERROR', 'drivers/LumingUfs missing')
        return
    source = driver / 'LumingUfs.cpp'
    header = driver / 'GccUfs.h'
    if source.is_file():
        add('PASS', 'driver source LumingUfs.cpp')
    else:
        add('ERROR', 'driver source LumingUfs.cpp missing (rename DadaUfs.cpp)')
    text = read(source, 'LumingUfs.cpp')
    if 'static const char kRootPartition[] = "userdata";' in text:
        add('PASS', 'kRootPartition = "userdata"')
    else:
        add('ERROR', 'kRootPartition is not "userdata" (still the SM8750 linux partition?)')
    accepted = re.search(r'static const char \*const accepted\[\]\s*=\s*\{([^}]+)\}', text)
    if accepted and '"qcom,ufshc"' in accepted.group(1) and '"qcom,sm8735-ufshc"' in accepted.group(1) \
            and 'sm8750' not in accepted.group(1):
        add('PASS', 'accepted compatibles qcom,ufshc + qcom,sm8735-ufshc')
    else:
        add('ERROR', f'accepted compatibles wrong: {accepted.group(1) if accepted else "unparsed"}')
    if '0x60' in text and '15000000' in text:
        add('PASS', 'driver uses apps_smmu 0x15000000 / stream 0x60')
    else:
        add('WARN', 'driver SMMU stream/base not visible in source')
    # DMA rule: the driver must refuse a DMA address above 4 GiB when CAP bit 24 is clear.
    if '0x01000000' in text and ('0x100000000' in text or '4 GiB' in text):
        add('PASS', 'driver keeps the DMA<4GiB/CAP-bit24 rule')
    else:
        add('WARN', 'driver DMA<4GiB/CAP-bit24 guard not detected')
    header_text = read(header, 'GccUfs.h')
    aggre = re.search(r'#define\s+GCC_AGGRE_UFS_PHY_AXI_ENABLE\s+(0x[0-9a-fA-F]+)', header_text)
    if aggre and int(aggre.group(1), 16) == 0x770F4:
        add('PASS', 'GccUfs.h GCC_AGGRE_UFS_PHY_AXI_ENABLE = 0x770f4 (SM8735 tuna)')
    else:
        add('ERROR', f'GccUfs.h AGGRE macro is not 0x770f4: {aggre.group(1) if aggre else "unparsed"}')
    for name, first, second in (
            ('AXI', '0x77018', ''), ('AHB', '0x77028', ''), ('TX0', '0x7702c', ''),
            ('RX0', '0x77030', ''), ('UNIPRO', '0x7706c', ''), ('ICE', '0x7707c', ''),
            ('AUX', '0x770bc', ''), ('RX1', '0x770d8', ''),
            ('GDSC', '0x77004', ''), ('MEM-PHY GDSC', '0x9e000', ''),
            ('RCG2 AXI', '0x77034', ''), ('RCG2 ICE', '0x7708c', ''),
            ('RCG2 UNIPRO', '0x770a4', ''), ('RCG2 AUX', '0x770c0', '')):
        add('PASS' if first in header_text else 'ERROR', f'GccUfs.h {name} = {first}')
    # BootLog sources for the boot-log archive
    for name in ('BootLog.c', 'BootProcessProbe.c'):
        path = device / 'kits/luming' / name
        add('PASS' if path.is_file() else 'ERROR', f'kits/luming/{name}')
    if (driver / 'tests/check_sm8735_facts.py').is_file():
        add('PASS', 'luming UFS facts test present')
    elif (driver / 'tests/check_sm8750_facts.py').is_file():
        add('ERROR', 'tests still named check_sm8750_facts.py')
    else:
        add('WARN', 'UFS facts test missing')



def check_observability(device: Path, board: dict) -> None:
    """Gate: upstream log paths must stay enabled (docs/LOGGING.md)."""
    defconfig = (device / 'configs' / str(board.get('kernel', {}).get('defconfig', ''))).read_text(encoding='utf-8')
    required = {
        'CONFIG_XNU_LUMING_BOOT_LOG=y': 'UFS periodic BootLog writer',
        'CONFIG_XNU_NATIVE_CS_HASH_CACHE=y': '4K code-signing hash cache',
        'CONFIG_XNU_NATIVE_UFS=y': 'UFS transport for the log window',
        'CONFIG_XNU_NATIVE_RAM_BLOCK=y': 'Data/ram block carrier',
    }
    for line, why in required.items():
        if re.search(rf'(?m)^{re.escape(line)}$', defconfig):
            add('PASS', f'observability config {line} ({why})')
        else:
            add('ERROR', f'observability config missing: {line} ({why})')
    if re.search(r'(?m)^CONFIG_XNU_BOOT_PROGRESS=n$', defconfig):
        add('WARN', 'upstream boot-progress screen is off (audited owner-root/Virtio set missing; dada also off)')
    args = board.get('payload', {}).get('kernel_args', [])
    for arg, why in (('luming-log=1', 'UFS BootLog window'),
                     ('serial=3', 'serial console selection (GENI backend missing upstream)'),
                     ('keepsyms=1', 'symbolised panic/backtrace'),
                     ('debug=0x14e', 'XNU debug flags')):
        if arg in args:
            add('PASS', f'observability kernel arg {arg} ({why})')
        elif arg == 'luming-log=1':
            add('WARN', 'luming-log disabled for the owner-bring-up build (BootLog diagnostics not required)')
        else:
            add('ERROR', f'observability kernel arg missing: {arg} ({why})')
    if board.get('payload', {}).get('panic_screen') is True:
        add('PASS', 'panic_screen = true (panic message + registers visible)')
    elif os.environ.get('UNIXNU_ALLOW_NO_PANIC_SCREEN') == '1':
        add('WARN', 'panic_screen is not true (reduced bootstrap payload; panic visibility disabled)')
    else:
        add('ERROR', 'panic_screen is not true (panic visibility disabled)')
    for name, path in (('BootLog.c', device / 'kits/luming/BootLog.c'),
                       ('BootProcessProbe.c', device / 'kits/luming/BootProcessProbe.c'),
                       ('LOGGING.md', device / 'docs/LOGGING.md'),
                       ('read-luming-log.py', device / 'scripts/read-luming-log.py')):
        add('PASS' if path.is_file() else 'ERROR', f'observability file {name}')
    bootlog = (device / 'kits/luming/BootLog.c').read_text(encoding='utf-8') if (device / 'kits/luming/BootLog.c').is_file() else ''
    for needle, why in (('LUMINGL2', 'BootLog header magic'), ('luming-log', 'BootLog boot argument')):
        add('PASS' if needle in bootlog else 'ERROR', f'observability BootLog {why} ({needle})')
    patch = device / 'patches/xnu/device/zzzzzzzzzzzzzzzzz-luming-ufs-log.patch'
    ptext = patch.read_text(encoding='utf-8') if patch.is_file() else ''
    for needle, why in (("'L', 'U', 'M', 'I', 'N', 'G', 'L', '1'", 'panic/exec ring magic'), ('luming_log_', 'panic/exec ring symbols')):
        add('PASS' if needle in ptext else 'ERROR', f'observability panic ring {why} ({needle})')
    reader = (device / 'scripts/read-luming-log.py').read_text(encoding='utf-8') if (device / 'scripts/read-luming-log.py').is_file() else ''
    for needle in ('LUMINGL2', 'LUMINGL1'):
        add('PASS' if needle in reader else 'ERROR', f'observability reader supports {needle}')



def check_luming_payload_path(luming_dir: Path) -> None:
    """Static check of the lumingPkg FDF/DSC format-2 payload path (uefi-builder-owned files).

    This does not read the device; it warns when the FD still carries the format-1 J2HandoffDxe
    fallback that wins over the boot.img ramdisk on a phone whose super partition holds a
    LUMING-J2-BLOB. docs/BOOT-MARKS.md has the runtime super check.
    """
    fdf = luming_dir / 'luming.fdf'
    apriori = luming_dir / 'Include' / 'APRIORI.inc'
    dsc = luming_dir / 'luming.dsc'
    for label, path in (('luming.fdf', fdf), ('Include/APRIORI.inc', apriori), ('luming.dsc', dsc)):
        add('PASS' if path.is_file() else 'WARN', f'firmware payload path file {label}', str(path))
    fdf_text = fdf.read_text(encoding='utf-8', errors='replace') if fdf.is_file() else ''
    ap_text = apriori.read_text(encoding='utf-8', errors='replace') if apriori.is_file() else ''
    dsc_text = dsc.read_text(encoding='utf-8', errors='replace') if dsc.is_file() else ''
    # The ramdisk FAT payload path must be in the APRIORI list, RamDisk before DiskIo/Partition/Fat.
    sequence = ['UniXNURamDiskDxe', 'DiskIoDxe', 'PartitionDxe', 'Fat.inf']
    indices = {}
    for needle in sequence:
        indices[needle] = ap_text.find(needle)
    if all(index >= 0 for index in indices.values()):
        ordered = list(indices.values()) == sorted(indices.values())
        add('PASS' if ordered else 'ERROR',
            'firmware payload path order RamDiskDxe -> DiskIo -> Partition -> Fat (APRIORI)',
            f'apriori indices {indices}')
    else:
        add('WARN', 'firmware payload path incomplete in APRIORI.inc',
            'expected UniXNURamDiskDxe, DiskIoDxe, PartitionDxe and Fat.inf in Include/APRIORI.inc')
    for needle in ('UniXNURamDiskDxe', 'DarwinBoot'):
        add('PASS' if needle in fdf_text else 'WARN', f'firmware FV contains {needle}')
    j2_files = ('J2HandoffDxe' in fdf_text) or ('J2HandoffDxe' in ap_text) or ('J2HandoffDxe' in dsc_text)
    if j2_files:
        add('WARN', 'firmware still contains J2HandoffDxe (format-1 super-blob fallback)',
            'on a device whose super still holds a LUMING-J2-BLOB this SFS wins and DarwinBoot '
            'boots the old A-line kernel instead of the boot.img ramdisk; restore pristine/'
            'format-2 super or build a J2 no-op FD before format-2 boot tests. Runtime check: '
            'dd if=/dev/block/by-name/super bs=4096 count=1 | strings | grep LUMING-J2-BLOB')
        j2_src = luming_dir.parents[2] / 'UniXNUPkg/Driver/J2HandoffDxe/J2HandoffDxe.c'
        j2_text = j2_src.read_text(encoding='utf-8', errors='replace') if j2_src.is_file() else ''
        noop = ('LUMING-J2-NOOP' in j2_text) or ('J2_NOOP' in j2_text) or ('j2 no-op' in j2_text.lower())
        add('PASS' if noop else 'WARN', 'J2HandoffDxe no-op marker present' if noop
            else 'J2HandoffDxe is active (diagnostic build needs a no-op source edit)')
    else:
        add('PASS', 'firmware FD has no J2HandoffDxe (ramdisk-only format-2 payload path)')


def check_firmware(device: Path, board: dict, uefi: Path | None) -> None:
    fw = board.get('firmware', {})
    for key in ('config', 'dsc', 'fd'):
        add('PASS' if fw.get(key) else 'ERROR', f'firmware.{key} = {fw.get(key)!r}')
    for item in fw.get('preflight') or []:
        path = device / item if not Path(item).is_absolute() else Path(item)
        add('PASS' if path.is_file() else 'ERROR', f'firmware preflight script {item}')
    if fw.get('dsc') and not str(fw.get('fd', '')).startswith('Build/'):
        add('ERROR', 'firmware.fd should be a Build/... path template')
    fw_root = uefi if uefi is not None else (device / 'firmware' / 'uefi')
    luming_dir = fw_root / 'Platforms' / 'Xiaomi' / 'lumingPkg'
    if luming_dir.is_dir():
        check_luming_payload_path(luming_dir)
    elif uefi is None:
        add('WARN', 'lumingPkg firmware tree not found for the static payload-path check',
            'expected firmware/uefi/Platforms/Xiaomi/lumingPkg (uefi-builder owned)')
    if uefi is None:
        add('WARN', 'external uefi-luming checkout not supplied (--uefi)', 'FD geometry/module list unchecked')
        return
    dsc = uefi / str(fw.get('dsc', ''))
    add('PASS' if dsc.is_file() else 'ERROR', f'UEFI DSC {dsc.name}', str(dsc))
    if not dsc.is_file():
        return
    text = dsc.read_text(encoding='utf-8', errors='replace')
    fdf = dsc.with_suffix('.fdf')
    fdf_text = fdf.read_text(encoding='utf-8', errors='replace') if fdf.is_file() else ''
    combined = text + '\n' + fdf_text
    for module in ('UniXNU', 'UniXNUDxe', 'UniXNURamDiskDxe', 'DarwinBoot', 'DiskIoDxe', 'Fat'):
        add('PASS' if module in combined else 'WARN', f'UEFI module {module} referenced')
    add('WARN', 'FD base/size 0xA7100000/0x300000 unverified', 'measure the luming reserved region')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', type=Path, default=None)
    parser.add_argument('--unixnu', type=Path, default=None)
    parser.add_argument('--uefi', type=Path, default=None)
    parser.add_argument('--json', type=Path, default=None)
    args = parser.parse_args()
    device = (args.device or Path.cwd()).resolve()
    if not (device / 'board.toml').is_file():
        candidate = HERE.parents[1]
        if (candidate / 'board.toml').is_file():
            device = candidate
        else:
            print(f'ERROR: no board.toml under {device}')
            return 1
    unixnu = (args.unixnu or device.parents[1] / 'unixnu-format2/UniXNU').resolve()
    if not (unixnu / 'components.toml').is_file():
        print(f'ERROR: UniXNU reference not found at {unixnu}')
        return 1
    try:
        board = tomllib.loads((device / 'board.toml').read_text(encoding='utf-8'))
    except Exception as error:  # noqa: BLE001
        print(f'ERROR: board.toml parse failed: {error}')
        return 1

    check_board(device, unixnu, board)
    check_prelink(board)
    check_payload_adt(board)
    check_bootimg(board)
    check_device_tree(device, board)
    check_driver(device)
    check_observability(device, board)
    check_firmware(device, board, args.uefi)

    counts = {'PASS': 0, 'WARN': 0, 'ERROR': 0}
    for level, name, detail in ROWS:
        counts[level] = counts.get(level, 0) + 1
        line = f'[{level}] {name}' + (f'  -> {detail}' if detail else '')
        print(line)
    print(f"\ncheck-luming: {counts['PASS']} pass, {counts['WARN']} warn, {counts['ERROR']} error")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({'device': str(device), 'unixnu': str(unixnu),
                                         'counts': counts,
                                         'rows': [{'level': l, 'check': n, 'detail': d} for l, n, d in ROWS]},
                                        indent=2) + '\n', encoding='utf-8')
    return 0 if counts['ERROR'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
