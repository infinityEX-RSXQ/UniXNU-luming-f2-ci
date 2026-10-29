#!/usr/bin/env python3
"""Generate and validate zzzzz-luming-early-console-flush.patch.

Diagnostic build: after PE_create_console() (and after the boot-marks band 3, so the text is not
painted over) call PE_init_printf(TRUE), which in pexpert/gen/pe_gen.c is exactly vcattach():
it flushes the buffered boot log to the video console now instead of waiting for
PE_init_iokit()->vcattach().

The patch is generated against the tree **after** zzzzz-luming-boot-marks.patch (its context
contains the mark-3 block), because the device series applies fb fix -> boot marks -> early flush.
Validation therefore runs the full series order against the pinned xnu files.

Usage: python agents/f2-luming/tools/gen-early-console-flush-patch.py [--xnu-dir DIR]
"""
from pathlib import Path
import argparse
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/xnu/device/zzzzz-luming-early-console-flush.patch'
SERIES = ROOT / 'patches/xnu/device/series'
PIN = 'd8b80295118ef25ac3a784134bcf95cd8e88109f'
BASE = f'https://raw.githubusercontent.com/apple-oss-distributions/xnu/{PIN}'
GIT = r'C:/Program Files/Git/cmd/git.exe'
FILES = ('osfmk/arm/arm_init.c', 'osfmk/kern/startup.c')
FB_PATCH = ROOT / 'patches/xnu/device/zzzzz-fix-darwinboot-physical-framebuffer.patch'
MARKS_PATCH = ROOT / 'patches/xnu/device/zzzzz-luming-boot-marks.patch'

INSERT = (
    '\n\t/*\n'
    '\t * luming bring-up: flush the buffered boot log to the video console now,\n'
    '\t * instead of waiting for PE_init_iokit()->vcattach().\n'
    '\t * PE_init_printf(TRUE) is vcattach() in pexpert/gen/pe_gen.c.\n'
    '\t */\n'
    '\tPE_init_printf(TRUE);\n'
    '\n'
)


def fetch(rel: str, directory: Path) -> Path:
    target = directory / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        with urllib.request.urlopen(f'{BASE}/{rel}', timeout=90) as response:
            target.write_bytes(response.read())
    return target


def apply(repo: Path, patch: Path) -> None:
    result = subprocess.run([GIT, 'apply', '--check', str(patch)], cwd=repo,
                            capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'git apply --check {patch.name} failed:\n{result.stderr}')
    result = subprocess.run([GIT, 'apply', str(patch)], cwd=repo,
                            capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'git apply {patch.name} failed:\n{result.stderr}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xnu-dir', type=Path, default=Path(tempfile.gettempdir()) / 'xnu-src')
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='xnu-early-flush-') as tmp:
        tmp = Path(tmp)
        pristine = tmp / 'pristine'
        post_marks = tmp / 'post_marks'
        for rel in FILES:
            source = fetch(rel, args.xnu_dir).read_bytes()
            for root in (pristine, post_marks):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source)

        # the marks patch applies on pristine; apply it, then build the early-flush edit on top
        subprocess.run([GIT, 'init', '-q'], cwd=post_marks, check=True)
        apply(post_marks, MARKS_PATCH)

        arm = (post_marks / 'osfmk/arm/arm_init.c').read_text(encoding='utf-8')
        anchor = '\tluming_boot_mark(3);\n'
        if anchor not in arm:
            raise SystemExit('mark-3 anchor not found in post-marks arm_init.c')
        arm = arm.replace(anchor, anchor + INSERT, 1)
        (post_marks / 'osfmk/arm/arm_init.c').write_text(arm, encoding='utf-8')

        # diff post-marks -> post-marks+flush for arm_init.c only
        # reconstruct the post-marks arm_init.c in a scratch copy for the "before" side
        scratch = tmp / 'scratch'
        for rel in FILES:
            target = scratch / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((pristine / rel).read_bytes())
        subprocess.run([GIT, 'init', '-q'], cwd=scratch, check=True)
        apply(scratch, MARKS_PATCH)

        before = tmp / 'before/osfmk/arm/arm_init.c'
        after = tmp / 'after/osfmk/arm/arm_init.c'
        before.parent.mkdir(parents=True, exist_ok=True)
        after.parent.mkdir(parents=True, exist_ok=True)
        before.write_bytes((scratch / 'osfmk/arm/arm_init.c').read_bytes())
        after.write_bytes((post_marks / 'osfmk/arm/arm_init.c').read_bytes())

        diff = subprocess.run(
            [GIT, 'diff', '--no-index', '--no-color', 'before/osfmk/arm/arm_init.c',
             'after/osfmk/arm/arm_init.c'],
            cwd=tmp, capture_output=True, text=True).stdout
        diff = diff.replace('a/before/', 'a/').replace('b/after/', 'b/')
        diff = diff.replace('--- a/before/', '--- a/').replace('+++ b/after/', '+++ b/')
        diff = diff.replace('diff --git a/before/', 'diff --git a/').replace(' b/after/', ' b/')
        header = ('# luming bring-up: flush buffered boot log to the video console right after\n'
                  '# PE_create_console() (PE_init_printf(TRUE) == vcattach()); diagnostic build only.\n')
        PATCH.write_bytes((header + diff).encode('utf-8'))
        print(f'wrote {PATCH} ({len(header + diff)} bytes)')

        # validate the full series order against a fresh pinned tree
        check = tmp / 'series_check'
        for rel in FILES:
            target = check / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((pristine / rel).read_bytes())
        (check / 'osfmk/console').mkdir(parents=True, exist_ok=True)
        vc = args.xnu_dir / 'video_console.c'
        if not vc.is_file():
            with urllib.request.urlopen(f'{BASE}/osfmk/console/video_console.c', timeout=90) as r:
                vc.write_bytes(r.read())
        (check / 'osfmk/console/video_console.c').write_bytes(vc.read_bytes())
        subprocess.run([GIT, 'init', '-q'], cwd=check, check=True)
        for patch in (FB_PATCH, MARKS_PATCH, PATCH):
            apply(check, patch)
        result = subprocess.run([GIT, 'apply', '--check', '--reverse', str(PATCH)],
                                cwd=check, capture_output=True, text=True)
        print('series validation: fb fix -> boot marks -> early console flush: PASS '
              f'(reverse-check exit {result.returncode})')
        if result.returncode:
            raise SystemExit(result.stderr)

    lines = SERIES.read_text(encoding='utf-8').splitlines()
    name = PATCH.name
    if name not in [line.strip() for line in lines]:
        marks = next((i for i, line in enumerate(lines)
                      if line.strip().startswith('zzzzz-luming-boot-marks')), -1)
        insert_at = marks + 1 if marks >= 0 else 0
        lines[insert_at:insert_at] = [
            '# [diagnostic, bring-up only] PE_init_printf(TRUE) == vcattach() after console creation:',
            '# shows the buffered boot log immediately instead of waiting for PE_init_iokit().',
            name,
        ]
        SERIES.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('added to patches/xnu/device/series')


if __name__ == '__main__':
    main()
