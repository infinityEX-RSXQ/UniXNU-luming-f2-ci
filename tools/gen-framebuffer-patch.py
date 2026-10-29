#!/usr/bin/env python3
"""Generate and validate zzzzz-fix-darwinboot-physical-framebuffer.patch, then add it to the device series.

The patch makes XNU's video_console initialize_screen() treat a low (non-kernel-VA) boot
framebuffer base address as physical.  UniXNU's DarwinBoot passes the UEFI GOP framebuffer as a
physical address without the iBoot "b0" marker (e.g. 0xFC800000, an even value), so after VM init
the pristine code takes it as a virtual address and writes into an unmapped VA (silent death
before any console output).

Usage: python agents/f2-luming/tools/gen-framebuffer-patch.py [--xnu-file PATH]
Requires the pinned osfmk/console/video_console.c (xnu d8b80295118ef25ac3a784134bcf95cd8e88109f);
defaults to %TEMP%/xnu-vc/video_console.c fetched from raw.githubusercontent.com.
"""
from pathlib import Path
import argparse
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/xnu/device/zzzzz-fix-darwinboot-physical-framebuffer.patch'
SERIES = ROOT / 'patches/xnu/device/series'
GIT = r'C:/Program Files/Git/cmd/git.exe'
OLD = '\t\tmakeMapping = (kernel_map == VM_MAP_NULL) || (0 != (1 & newVideoVirt));\n'
NEW = (
    '\t\t/*\n'
    '\t\t * UniXNU: DarwinBoot hands over the GOP framebuffer as a physical address\n'
    '\t\t * without the iBoot b0 marker (it passes e.g. 0xFC800000 as an even value).\n'
    '\t\t * Treat any non-kernel-VA address as physical so initialize_screen() maps it\n'
    '\t\t * instead of writing pixels to an unmapped virtual address after VM init.\n'
    '\t\t */\n'
    '\t\tmakeMapping = (kernel_map == VM_MAP_NULL) || (0 != (1 & newVideoVirt)) ||\n'
    '\t\t    (newVideoVirt < 0xffff000000000000ULL);\n'
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xnu-file', type=Path,
                    default=Path(tempfile.gettempdir()) / 'xnu-vc/video_console.c')
    args = ap.parse_args()
    pristine = args.xnu_file.read_bytes()
    text = pristine.decode('utf-8')
    if OLD not in text:
        raise SystemExit('pristine makeMapping line not found; wrong xnu revision?')
    edited = text.replace(OLD, NEW).encode('utf-8')

    with tempfile.TemporaryDirectory(prefix='xnu-vc-patch-') as tmp:
        tmp = Path(tmp)
        orig = tmp / 'orig/osfmk/console/video_console.c'
        new = tmp / 'new/osfmk/console/video_console.c'
        orig.parent.mkdir(parents=True)
        new.parent.mkdir(parents=True)
        orig.write_bytes(pristine)
        new.write_bytes(edited)
        proc = subprocess.run([GIT, 'diff', '--no-index', '--no-color',
                               'orig/osfmk/console/video_console.c',
                               'new/osfmk/console/video_console.c'],
                              cwd=tmp, capture_output=True, text=True)
        diff = proc.stdout
        diff = diff.replace('a/orig/', 'a/').replace('b/new/', 'b/')
        diff = diff.replace('--- a/orig/', '--- a/').replace('+++ b/new/', '+++ b/')
        diff = diff.replace('diff --git a/orig/', 'diff --git a/').replace(' b/new/', ' b/')
        # header should now read: diff --git a/osfmk/... b/osfmk/...
        if not diff.startswith('diff --git a/osfmk/console/video_console.c b/osfmk/console/video_console.c'):
            raise SystemExit('unexpected diff header:\n' + diff[:400])
        PATCH.write_text(diff, encoding='utf-8', newline='')

        # validate: clean repo with the pristine file, git apply --check
        check = tmp / 'check'
        (check / 'osfmk/console').mkdir(parents=True)
        (check / 'osfmk/console/video_console.c').write_bytes(pristine)
        subprocess.run([GIT, 'init', '-q'], cwd=check, check=True)
        result = subprocess.run([GIT, 'apply', '--check', str(PATCH)], cwd=check,
                                capture_output=True, text=True)
        if result.returncode:
            raise SystemExit('git apply --check failed:\n' + result.stderr)
        print(f'patch written and applies against pinned video_console.c: {PATCH}')
        print(f'lines: {len(diff.splitlines())}, hunk header: '
              f'{[line for line in diff.splitlines() if line.startswith("@@")]}')

    # add to the device series once, before the boot-progress patch
    lines = SERIES.read_text(encoding='utf-8').splitlines() if SERIES.is_file() else []
    name = PATCH.name
    if name not in [line.strip() for line in lines]:
        header = ('# [2026-10-29] DarwinBoot passes the GOP framebuffer as a physical address '
                  'without the iBoot b0 marker;')
        detail = ('# xnu video_console initialize_screen() treats an even, low address as a '
                  'virtual address after VM init and silently dies.')
        entry = ['# [adapted] fixes the silent no-console death with UniXNU DarwinBoot GOP hand-off',
                 header, detail, name]
        insert_at = next((i for i, line in enumerate(lines) if line.strip().startswith('zzz-boot-progress')), 0)
        lines[insert_at:insert_at] = entry
        SERIES.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('added to patches/xnu/device/series')


if __name__ == '__main__':
    main()
