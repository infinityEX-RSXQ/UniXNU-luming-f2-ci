#!/usr/bin/env python3
"""Wire the upstream observability paths for luming: UFS BootLog, panic/exec ring, panic screen.

No hand-made probes: this only enables/renames the log facilities that upstream dada/sheng ship
(periodic UFS log writer, device-log ring+panic flush, payload panic screen, serial boot arg).
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def edit(rel, pairs, must=True):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        if old not in text and must:
            print(f'WARN {rel}: pattern not found: {old[:80]!r}')
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')
    print(f'edited {rel}')


def dedupe(path, prefix):
    lines = path.read_text(encoding='utf-8').splitlines()
    out, seen = [], set()
    for line in lines:
        if line.startswith(prefix):
            if line in seen:
                continue
            seen.add(line)
        out.append(line)
    path.write_text('\n'.join(out) + '\n', encoding='utf-8')


def main():
    # 1) board.toml: panic screen (sheng keeps it on) + serial/keepsyms/bootlog arguments
    board = ROOT / 'board.toml'
    dedupe(board, 'trust_cache_sha256 = ')
    edit('board.toml', [
        ('dram_size = "0x23ffff000"\npanic_screen = false',
         'dram_size = "0x23ffff000"\n'
         '# [adapted sheng] panic_screen = true patches a panic screen into the kernel copy: the\n'
         '# formatted panic message and registers stay visible on the framebuffer (docs/guide/debugging.md\n'
         '# §Panic screen in UniXNU). dada ships false; sheng ships true and is the reference used here.\n'
         '# Payload build logs/probe installation in logs/payload-patch.log; if the patcher refuses the\n'
         '# kernel the payload step reports it (upstream-supported path, no hand-made probe).\n'
         'panic_screen = true'),
        ('  "-v",\n  "debug=0x14e",\n  "boot-progress=2",',
         '  "-v",\n  "debug=0x14e",\n'
         '  # Upstream observability paths (docs/LOGGING.md):\n'
         '  #   serial=3   serial console selection (backend: see docs/LOGGING.md; no GENI driver yet)\n'
         '  #   keepsyms=1 symbolize backtraces in panic/console output\n'
         '  #   luming-log=1 opens the UFS log window and starts the periodic BootLog writer\n'
         '  #   boot-progress=2 keeps the upstream boot-progress boot argument (screen needs CONFIG on)\n'
         '  "serial=3",\n  "keepsyms=1",\n  "boot-progress=2",'),
        ('  "native-ufs-diagnostics=1",\n  "-no_slto_panic",',
         '  "native-ufs-diagnostics=1",\n  "luming-log=1",\n  "-no_slto_panic",'),
    ])

    # 2) defconfig: remove the non-standard [archives] header and document the log paths
    edit('configs/luming_defconfig', [
        ('[archives]\nCONFIG_XNU_BUILD_ARCHIVES=y', 'CONFIG_XNU_BUILD_ARCHIVES=y'),
        ('CONFIG_XNU_BOOT_PROGRESS=n\nCONFIG_XNU_DT_PANIC_REGION=y',
         '# ---- Observability (upstream paths only; docs/LOGGING.md) ----------------------------------\n'
         '# UFS periodic log writer + boot process probe: BootLog.c/BootProcessProbe.c write the kernel\n'
         '# message buffer and board rows into the last 32 MiB of userdata every 2 s (luming-log=1).\n'
         'CONFIG_XNU_LUMING_BOOT_LOG=y\n'
         '# DT panic region lookup: without it pexpert would map the BCM2837 hardcoded 0x3c0fc000 and\n'
         '# hang before any console exists (dada/sheng both set this).\n'
         'CONFIG_XNU_DT_PANIC_REGION=y\n'
         '# Static code-signing hash cache required by the 4K/source build; keeps panic/backtrace paths\n'
         '# intact when the executable segment is hashed.\n'
         'CONFIG_XNU_NATIVE_CS_HASH_CACHE=y\n'
         '# The upstream boot-progress screen is NOT enabled: scripts/build-xnu-4k-baseline.sh gates it on\n'
         '# the audited owner-root/Virtio-block/source-corecrypto set that this board does not carry yet\n'
         '# (dada keeps it off for the same reason). The kernel still prints through the video console,\n'
         '# the serial boot arg and the UFS BootLog. [missing: audited boot-progress set]\n'
         'CONFIG_XNU_BOOT_PROGRESS=n\n'
         '# Native VirtIO console is QEMU-only (upstream XNU_NATIVE_VIRTIO_CONSOLE); the luming UART is a\n'
         '# GENI device and has no upstream format-2 console driver yet (docs/LOGGING.md, serial path).\n'
         'CONFIG_XNU_NATIVE_VIRTIO_CONSOLE=n'),
    ])

    # 3) BootLog.c: luming magic/argument, keep upstream logic/identifiers otherwise
    edit('kits/luming/BootLog.c', [
        ('// Diagnostic log on UFS (boot argument dada-log=1)', '// Diagnostic log on UFS (boot argument luming-log=1)'),
        ('DADA_LOG_WINDOW_BLOCKS = 8192', 'LUMING_LOG_WINDOW_BLOCKS = 8192'),
        ('DADA_LOG_WINDOW_BLOCKS', 'LUMING_LOG_WINDOW_BLOCKS'),
        ('// "DADALOG2"', '// "LUMINGL2"'),
        ('memcpy(h.magic, "DADALOG2", 8);', 'memcpy(h.magic, "LUMINGL2", 8);'),
        ('PE_parse_boot_argn("dada-log", &mode, sizeof mode)', 'PE_parse_boot_argn("luming-log", &mode, sizeof mode)'),
        ('native_ufs_log_probe(0xE0, "dada-log off")', 'native_ufs_log_probe(0xE0, "luming-log off")'),
    ])

    # 4) panic/exec ring patch: rebrand the header magic and internal names to luming
    patch = ROOT / 'patches/xnu/device/zzzzzzzzzzzzzzzzz-luming-ufs-log.patch'
    text = patch.read_text(encoding='utf-8')
    text = text.replace("'D', 'A', 'D', 'A', 'L', 'O', 'G', '1'", "'L', 'U', 'M', 'I', 'N', 'G', 'L', '1'")
    text = text.replace('DADA_LOG_BYTES', 'LUMING_LOG_BYTES').replace('DADA_LOG_', 'LUMING_LOG_')
    text = text.replace('dada_log_', 'luming_log_').replace('dada-log', 'luming-log')
    text = text.replace('DADALOG1', 'LUMINGL1')
    patch.write_text(text, encoding='utf-8')
    print('edited panic/exec ring patch (LUMINGL1, luming_log_* symbols)')

    # 5) reader: support both LUMINGL2 (periodic BootLog) and LUMINGL1 (panic/exec flush)
    reader = ROOT / 'scripts/read-luming-log.py'
    rtext = reader.read_text(encoding='utf-8')
    rtext = rtext.replace('block 0 is the header (magic LUMINGLOG2), blocks 1..32 the kernel message buffer and blocks 33.. a ring of 16-block text\nslots.',
                          'block 0 is the header. Two writers share the window:\n'
                          '  LUMINGL2 - periodic BootLog (blocks 0 header, 1..128 kernel message buffer, 129.. text slots)\n'
                          '  LUMINGL1 - panic/exec flush ring (block 0 header, 1..N text)\n'
                          'The reader prints whichever writer wrote the newest valid header.')
    rtext = rtext.replace("MAGIC = b'LUMINGLOG2'", "MAGIC = b'LUMINGL2'\nPANIC_MAGIC = b'LUMINGL1'")
    reader.write_text(rtext, encoding='utf-8')
    print('edited scripts/read-luming-log.py header/magic docs')


if __name__ == '__main__':
    main()
