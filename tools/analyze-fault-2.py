#!/usr/bin/env python3
"""Offline analysis for task-341: map VAs to Mach-O file offsets, locate call sites and prepare
PSCI-marker / candidate-fix byte patches for kernel.macho (no device operations).

Usage: python agents/f2-luming/tools/analyze-fault-2.py
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KERNEL = ROOT / 'build/payload51/EFI/UniXNU/Payloads/kernel.macho'
NM = ROOT / 'tmp/k51.nm'
OUT = ROOT / 'tmp/task341-analysis.json'

LC_SEGMENT_64 = 0x19


def parse_macho(path: Path):
    data = path.read_bytes()
    magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _reserved = struct.unpack_from('<IiiIIII I', data, 0)
    assert magic == 0xFEEDFACF, hex(magic)
    off = 32
    segments, sections = [], []
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', data, off)
        if cmd == LC_SEGMENT_64:
            segname = data[off + 8:off + 24].split(b'\0')[0].decode()
            vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, sflags = struct.unpack_from(
                '<QQQQiiII', data, off + 24)
            segments.append(dict(name=segname, vmaddr=vmaddr, vmsize=vmsize, fileoff=fileoff,
                                 filesize=filesize, maxprot=maxprot, initprot=initprot, nsects=nsects))
            so = off + 72
            for _s in range(nsects):
                sectname = data[so:so + 16].split(b'\0')[0].decode()
                segname2 = data[so + 16:so + 32].split(b'\0')[0].decode()
                addr, size = struct.unpack_from('<QQ', data, so + 32)
                offset, align, reloff, nreloc, sflags2 = struct.unpack_from('<IIIII', data, so + 48)
                sections.append(dict(sect=sectname, seg=segname2, addr=addr, size=size, offset=offset,
                                     flags=sflags2))
                so += 80
        off += cmdsize
    return data, segments, sections


def main():
    data, segments, sections = parse_macho(KERNEL)
    print('segments:')
    for seg in segments:
        print(f"  {seg['name']:<18} vm={seg['vmaddr']:#018x} vmsize={seg['vmsize']:#x} "
              f"fileoff={seg['fileoff']:#x} filesize={seg['filesize']:#x} prot={seg['initprot']}")

    def va_to_off(va: int):
        for seg in segments:
            if seg['vmaddr'] <= va < seg['vmaddr'] + seg['vmsize']:
                delta = va - seg['vmaddr']
                if delta < seg['filesize']:
                    return seg['fileoff'] + delta, seg
                return None, seg
        return None, None

    def seg_of(va: int):
        for seg in segments:
            if seg['vmaddr'] <= va < seg['vmaddr'] + seg['vmsize']:
                return seg
        return None

    def sect_of(va: int):
        for sec in sections:
            if sec['addr'] <= va < sec['addr'] + sec['size']:
                return sec
        return None

    symbols = {}
    for line in NM.read_text(errors='replace').splitlines():
        parts = line.strip().split()
        if len(parts) >= 3 and parts[0].startswith('fffffff'):
            try:
                symbols[int(parts[0], 16)] = parts[2]
            except ValueError:
                pass

    def sym(va: int):
        return symbols.get(va, '?')

    targets = {
        0xfffffff007838450: 'OSMetaClass::instanceConstructed',
        0xfffffff0078c78f0: 'IOWorkLoop::workLoop',
        0xfffffff0078c77d0: 'IOWorkLoop::init',
        0xfffffff007839810: 'OSObject_typed_operator_new',
        0xfffffff007839a58: 'OSObject::OSObject',
        0xfffffff0078c75e4: 'IOWorkLoop::MetaClass::MetaClass',
        0xfffffff0078c76b0: 'IOWorkLoop::MetaClass::MetaClass (C2)',
    }
    print('\ngMetaClass 0xfffffff007b69a58 seg=', seg_of(0xfffffff007b69a58),
          'section=', sect_of(0xfffffff007b69a58), 'sym=', sym(0xfffffff007b69a58))
    print('IOWorkLoop::gMetaClass symbol matches:', (0xfffffff007b69a58 in symbols, symbols.get(0xfffffff007b69a58)))

    # scan __TEXT_EXEC for BL/B targets of interest
    calls = {va: [] for va in targets}
    text_exec = next(seg for seg in segments if seg['name'] == '__TEXT_EXEC')
    base = text_exec['vmaddr']
    blob = data[text_exec['fileoff']:text_exec['fileoff'] + text_exec['filesize']]
    for i in range(0, len(blob) - 3, 4):
        insn = struct.unpack_from('<I', blob, i)[0]
        top6 = insn >> 26
        if top6 in (0b100101, 0b000101):  # BL, B
            imm = insn & 0x03FFFFFF
            if imm & 0x02000000:
                imm -= 0x04000000
            target = base + i + (imm << 2)
            if target in calls:
                calls[target].append(base + i)
    print('\ncall sites:')
    for va, sites in calls.items():
        print(f"  {va:#018x} {targets[va]}: {[hex(s) for s in sites]}")

    # VA -> file offsets and bytes for markers/fixes
    points = {
        # next marker targets inside instanceConstructed (priority order)
        'marker M1 after first OSIncrementAtomic (0x7838468)': 0xfffffff007838468,
        'marker M2 after superClassLink load (0x7838470)': 0xfffffff007838470,
        'marker M3 epilogue / chain end (0x7838474)': 0xfffffff007838474,
        'marker M0 before first atomic (0x7838460)': 0xfffffff007838460,
        # candidate fixes
        'fix: skip call in workLoop (NOP bl @0x78c7930)': 0xfffffff0078c7930,
        'fix: skip call in workLoopWithOptions (NOP bl @0x78c79b4)': 0xfffffff0078c79b4,
        'fix: instanceConstructed entry ret @0x7838450': 0xfffffff007838450,
        'fix: chain deref ldr x19,[x19,#0x10] @0x783846c': 0xfffffff00783846c,
    }
    print('\nVA mapping / current bytes:')
    rows = []
    for label, va in points.items():
        off, seg = va_to_off(va)
        cur = data[off:off + 16].hex() if off is not None else None
        print(f'  {label}: va={va:#018x} off={off:#x} seg={seg["name"] if seg else None} cur16={cur}')
        rows.append(dict(label=label, va=va, file_offset=off, segment=seg['name'] if seg else None,
                         current16=cur, symbol=sym(va)))
    print('\nselected section flags (gMetaClass context):')
    for sec in sections:
        if sec['sect'] in ('__common', '__bss', '__data', '__const'):
            print(f"  {sec['seg']},{sec['sect']} addr={sec['addr']:#x} size={sec['size']:#x} flags={sec['flags']:#x}")
    OUT.write_text(json.dumps(dict(segments=segments, sections=sections, calls={hex(k): v for k, v in calls.items()},
                                   points=rows, gmeta=dict(seg=seg_of(0xfffffff007b69a58),
                                                            section=sect_of(0xfffffff007b69a58))), indent=2) + '\n')
    print(f'\nwrote {OUT}')


if __name__ == '__main__':
    main()
