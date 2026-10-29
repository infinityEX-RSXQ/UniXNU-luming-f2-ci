#!/usr/bin/env python3
"""Add the static format-2 payload-path / J2 warning gate to scripts/check-luming.py."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'scripts/check-luming.py'
t = p.read_text(encoding='utf-8')

FUNC = '''
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


'''
anchor = "def check_firmware(device: Path, board: dict, uefi: Path | None) -> None:"
if 'def check_luming_payload_path' not in t:
    t = t.replace(anchor, FUNC + anchor)

anchor2 = """    if uefi is None:
        add('WARN', 'external uefi-luming checkout not supplied (--uefi)', 'FD geometry/module list unchecked')
        return"""
replacement2 = """    fw_root = uefi if uefi is not None else (device / 'firmware' / 'uefi')
    luming_dir = fw_root / 'Platforms' / 'Xiaomi' / 'lumingPkg'
    if luming_dir.is_dir():
        check_luming_payload_path(luming_dir)
    elif uefi is None:
        add('WARN', 'lumingPkg firmware tree not found for the static payload-path check',
            'expected firmware/uefi/Platforms/Xiaomi/lumingPkg (uefi-builder owned)')
    if uefi is None:
        add('WARN', 'external uefi-luming checkout not supplied (--uefi)', 'FD geometry/module list unchecked')
        return"""
if anchor2 not in t:
    raise SystemExit('check_firmware early-return anchor not found')
t = t.replace(anchor2, replacement2, 1)
p.write_text(t, encoding='utf-8')
print('payload-path/J2 gate added')
