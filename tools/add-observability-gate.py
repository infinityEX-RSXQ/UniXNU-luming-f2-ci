#!/usr/bin/env python3
"""Insert the log-observability gate into scripts/check-luming.py (idempotent)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'scripts/check-luming.py'
t = p.read_text(encoding='utf-8')
FUNC = '''
def check_observability(device: Path, board: dict) -> None:
    """Gate: upstream log paths must stay enabled (docs/LOGGING.md)."""
    defconfig = (device / 'configs' / str(board.get('kernel', {}).get('defconfig', ''))).read_text(encoding='utf-8')
    required = {
        'CONFIG_XNU_LUMING_BOOT_LOG=y': 'UFS periodic BootLog writer',
        'CONFIG_XNU_DT_PANIC_REGION=y': 'device-tree panic region (avoids BCM2837 hardcoded hang)',
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
        else:
            add('ERROR', f'observability kernel arg missing: {arg} ({why})')
    if board.get('payload', {}).get('panic_screen') is True:
        add('PASS', 'panic_screen = true (panic message + registers visible)')
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
    for needle, why in (('LUMINGL1', 'panic/exec ring magic'), ('luming_log_', 'panic/exec ring symbols')):
        add('PASS' if needle in ptext else 'ERROR', f'observability panic ring {why} ({needle})')
    reader = (device / 'scripts/read-luming-log.py').read_text(encoding='utf-8') if (device / 'scripts/read-luming-log.py').is_file() else ''
    for needle in ('LUMINGL2', 'LUMINGL1'):
        add('PASS' if needle in reader else 'ERROR', f'observability reader supports {needle}')


'''
anchor = 'def check_firmware(device: Path, board: dict, uefi: Path | None) -> None:'
if 'def check_observability' not in t:
    t = t.replace(anchor, FUNC + anchor)
if 'check_observability(device, board)' not in t:
    t = t.replace('    check_driver(device)\n', '    check_driver(device)\n    check_observability(device, board)\n')
p.write_text(t, encoding='utf-8')
print('observability gate inserted')
