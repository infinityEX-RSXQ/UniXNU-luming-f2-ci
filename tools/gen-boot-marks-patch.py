#!/usr/bin/env python3
"""Generate and validate zzzzz-luming-boot-marks.patch (diagnostic stage bands).

Adds five calls to luming_boot_mark() (kits/luming/BootMarks.c, built into libLumingBootLog.a):
  1 after arm_vm_init()            -> VM available
  2 after "kprintf initialized"    -> kprintf subsystem up
  3 after PE_create_console()      -> console created
  4 after PE_init_platform(TRUE)   -> platform expert up
  5 before PE_init_iokit()         -> entering IOKit (video console attach point)

Usage: python agents/f2-luming/tools/gen-boot-marks-patch.py [--xnu-dir DIR]
The pinned files are downloaded from apple-oss-distributions/xnu @ d8b8029... if not present.
"""
from pathlib import Path
import argparse
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/xnu/device/zzzzz-luming-boot-marks.patch'
SERIES = ROOT / 'patches/xnu/device/series'
PIN = 'd8b80295118ef25ac3a784134bcf95cd8e88109f'
BASE = f'https://raw.githubusercontent.com/apple-oss-distributions/xnu/{PIN}'
GIT = r'C:/Program Files/Git/cmd/git.exe'

CALL = (
    '\t/* luming diagnostic boot marks (bring-up only): see kits/luming/BootMarks.c */\n'
    '\textern void luming_boot_mark(unsigned int);\n'
    '\tluming_boot_mark({stage});\n'
)


def fetch(rel: str, directory: Path) -> str:
    target = directory / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        with urllib.request.urlopen(f'{BASE}/{rel}', timeout=90) as response:
            target.write_bytes(response.read())
    return target.read_text(encoding='utf-8')


def insert_after(text: str, needle: str, block: str) -> str:
    if needle not in text:
        raise SystemExit(f'anchor not found: {needle!r}')
    return text.replace(needle, needle + block, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xnu-dir', type=Path, default=Path(tempfile.gettempdir()) / 'xnu-src')
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='xnu-boot-marks-') as tmp:
        tmp = Path(tmp)
        orig = tmp / 'orig'
        new = tmp / 'new'
        for rel in ('osfmk/arm/arm_init.c', 'osfmk/kern/startup.c'):
            source = fetch(rel, args.xnu_dir)
            (orig / rel).parent.mkdir(parents=True, exist_ok=True)
            (new / rel).parent.mkdir(parents=True, exist_ok=True)
            (orig / rel).write_text(source, encoding='utf-8')

        arm = (orig / 'osfmk/arm/arm_init.c').read_text(encoding='utf-8')
        arm = insert_after(arm, '\tarm_vm_init(xmaxmem, args);\n', CALL.format(stage=1))
        arm = insert_after(arm, '\tkprintf("kprintf initialized\\n");\n', CALL.format(stage=2))
        arm = insert_after(arm, '\tPE_create_console();\n', CALL.format(stage=3))
        arm = insert_after(arm, '\tPE_init_platform(TRUE, &BootCpuData);\n', CALL.format(stage=4))
        (new / 'osfmk/arm/arm_init.c').write_text(arm, encoding='utf-8')

        startup = (orig / 'osfmk/kern/startup.c').read_text(encoding='utf-8')
        startup = insert_after(startup, '\tkernel_bootstrap_log("PE_init_iokit");\n', CALL.format(stage=5))
        (new / 'osfmk/kern/startup.c').write_text(startup, encoding='utf-8')

        diffs = []
        for rel in ('osfmk/arm/arm_init.c', 'osfmk/kern/startup.c'):
            part = subprocess.run(
                [GIT, 'diff', '--no-index', '--no-color', f'orig/{rel}', f'new/{rel}'],
                cwd=tmp, capture_output=True, text=True).stdout
            part = part.replace('a/orig/', 'a/').replace('b/new/', 'b/')
            part = part.replace('--- a/orig/', '--- a/').replace('+++ b/new/', '+++ b/')
            part = part.replace('diff --git a/orig/', 'diff --git a/').replace(' b/new/', ' b/')
            diffs.append(part)
        diff = ''.join(diffs)
        if 'a/osfmk/arm/arm_init.c b/osfmk/arm/arm_init.c' not in diff or \
                'a/osfmk/kern/startup.c b/osfmk/kern/startup.c' not in diff:
            raise SystemExit('unexpected diff header:\n' + diff[:500])
        # add a leading description comment to the patch body
        header = ('# luming diagnostic boot marks: five framebuffer colour bands marking early boot stages.\n'
                  '# Bring-up only. Pair with kits/luming/BootMarks.c (libLumingBootLog.a).\n')
        PATCH.write_bytes((header + diff).encode('utf-8'))
        print(f'wrote {PATCH}')

        check = tmp / 'check'
        for rel in ('osfmk/arm/arm_init.c', 'osfmk/kern/startup.c'):
            (check / rel).parent.mkdir(parents=True, exist_ok=True)
            (check / rel).write_bytes((orig / rel).read_bytes())
        subprocess.run([GIT, 'init', '-q'], cwd=check, check=True)
        result = subprocess.run([GIT, 'apply', '--check', str(PATCH)], cwd=check,
                                capture_output=True, text=True)
        if result.returncode:
            raise SystemExit('git apply --check failed:\n' + result.stderr)
        print('git apply --check against pinned xnu: PASS')

    lines = SERIES.read_text(encoding='utf-8').splitlines()
    name = PATCH.name
    if name not in [line.strip() for line in lines]:
        fb = next((i for i, line in enumerate(lines)
                   if line.strip().startswith('zzzzz-fix-darwinboot')), -1)
        insert_at = fb + 1 if fb >= 0 else 0
        lines[insert_at:insert_at] = [
            '# [diagnostic, bring-up only] five framebuffer bands: arm_vm_init, kprintf, console,',
            '# PE_init_platform(TRUE), PE_init_iokit; remove for production builds.',
            name,
        ]
        SERIES.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('added to patches/xnu/device/series')


if __name__ == '__main__':
    main()
