#!/usr/bin/env python3
"""Generate and validate zzzzz-luming-start-signals.patch.

Three binary signals from osfmk/arm64/start.s for the no-output window before arm_vm_init():
  A. _start_first_cpu, right after x20/x21 are saved and the MMU is still OFF:
     fill the first 256 KiB of the GOP framebuffer (PA 0xFC800000) with RED (0x00FF0000).
  B. common_start, immediately BEFORE the MMU-enable `msr SCTLR_EL1, x0`: fill 256 KiB at
     FB+2 MiB with GREEN (0x0000FF00), MMU still OFF.
  C. immediately AFTER the MMU-enable `msr SCTLR_EL1, x0; isb sy`: PSCI SYSTEM_RESET
     (movz/movk w0, 0x84000009; smc #0) so the device reboots if this point is reached.

Registers x27/x28 are unused anywhere in the pinned start.s; x29 is also unused in this file and
is used as the colour scratch. x26 is loaded later (line 479), so it is not touched by marker A.
x27/x28/x29 are clobbered by design in this diagnostic build.

Usage: python agents/f2-luming/tools/gen-start-signals-patch.py [--xnu-dir DIR]
"""
from pathlib import Path
import argparse
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/xnu/device/zzzzz-luming-start-signals.patch'
SERIES = ROOT / 'patches/xnu/device/series'
PIN = 'd8b80295118ef25ac3a784134bcf95cd8e88109f'
BASE = f'https://raw.githubusercontent.com/apple-oss-distributions/xnu/{PIN}'
GIT = r'C:/Program Files/Git/cmd/git.exe'
FB_PATCH = ROOT / 'patches/xnu/device/zzzzz-fix-darwinboot-physical-framebuffer.patch'
MARKS_PATCH = ROOT / 'patches/xnu/device/zzzzz-luming-boot-marks.patch'
FLUSH_PATCH = ROOT / 'patches/xnu/device/zzzzz-luming-early-console-flush.patch'

A = '''
	/*
	 * luming diagnostic start-signal A (bring-up only): RED block at the GOP framebuffer
	 * physical address while the MMU is still OFF. x27/x28/x29 are unused in bootstrap.
	 */
	movz	x27, #0xFC80, lsl #16			// x27 = 0xFC800000 (FB PA)
	movz	w29, #0xFF, lsl #16				// red 0x00FF0000
	mov	x28, #0x10000						// 256 KiB / 4
Lluming_start_signal_a:
	str	w29, [x27], #4
	subs	x28, x28, #1
	b.ne	Lluming_start_signal_a
	dsb	sy
'''
B = '''
	/*
	 * luming diagnostic start-signal B (bring-up only): GREEN block at FB+2 MiB while the
	 * MMU is still OFF, immediately before SCTLR_EL1 is written.
	 */
	movz	x27, #0xFC80, lsl #16			// x27 = 0xFC800000 (FB PA)
	movz	x28, #0x20, lsl #16				// + 0x200000 (2 MiB)
	add	x27, x27, x28
	movz	w29, #0xFF00					// green 0x0000FF00 (16-bit imm, shift 0; movz lsl #8 is invalid)
	mov	x28, #0x10000						// 256 KiB / 4
Lluming_start_signal_b:
	str	w29, [x27], #4
	subs	x28, x28, #1
	b.ne	Lluming_start_signal_b
	dsb	sy

'''
C = '''	/*
	 * luming diagnostic start-signal C (bring-up only): the MMU is now ON. Reset through
	 * PSCI (SYSTEM_RESET = 0x84000009) so an automatic reboot proves this point was reached.
	 */
	movz	w0, #0x8400, lsl #16
	movk	w0, #9
	smc	#0
	hvc	#0
Lluming_start_signal_c:
	b	Lluming_start_signal_c
'''


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
    start = fetch('osfmk/arm64/start.s', args.xnu_dir).read_text(encoding='utf-8')

    anchor_a = '\tmov\t\tx21, #0\n'
    if start.count(anchor_a) != 1:
        raise SystemExit('anchor A not unique')
    patched = start.replace(anchor_a, anchor_a + A, 1)

    anchor_b = '\tMOV64   x0, SCTLR_EL1_DEFAULT\n'
    if patched.count(anchor_b) != 1:
        raise SystemExit('anchor B not unique')
    patched = patched.replace(anchor_b, B + anchor_b, 1)

    anchor_c = '\tMOV64   x0, SCTLR_EL1_DEFAULT\n\tMSR_SCTLR_EL1_X0\n\tisb\t\tsy\n'
    if patched.count(anchor_c) != 1:
        raise SystemExit('anchor C not unique')
    patched = patched.replace(
        anchor_c,
        '\tMOV64   x0, SCTLR_EL1_DEFAULT\n\tMSR_SCTLR_EL1_X0\n\tisb\t\tsy\n' + C, 1)

    with tempfile.TemporaryDirectory(prefix='xnu-start-signals-') as tmp:
        tmp = Path(tmp)
        (tmp / 'orig/osfmk/arm64').mkdir(parents=True)
        (tmp / 'new/osfmk/arm64').mkdir(parents=True)
        (tmp / 'orig/osfmk/arm64/start.s').write_text(start, encoding='utf-8', newline='')
        (tmp / 'new/osfmk/arm64/start.s').write_text(patched, encoding='utf-8', newline='')
        diff = subprocess.run(
            [GIT, 'diff', '--no-index', '--no-color', 'orig/osfmk/arm64/start.s',
             'new/osfmk/arm64/start.s'],
            cwd=tmp, capture_output=True, text=True).stdout
        diff = diff.replace('a/orig/', 'a/').replace('b/new/', 'b/')
        diff = diff.replace('--- a/orig/', '--- a/').replace('+++ b/new/', '+++ b/')
        diff = diff.replace('diff --git a/orig/', 'diff --git a/').replace(' b/new/', ' b/')
        if 'a/osfmk/arm64/start.s b/osfmk/arm64/start.s' not in diff:
            raise SystemExit('unexpected diff header:\n' + diff[:500])
        header = ('# luming diagnostic start signals A/B/C for osfmk/arm64/start.s (bring-up only):\n'
                  '# A red FB block before MMU, B green FB block before SCTLR_EL1, C PSCI reset after MMU.\n')
        PATCH.write_bytes((header + diff).encode('utf-8'))
        print(f'wrote {PATCH} ({len(header + diff)} bytes)')

        # standalone apply-check against the pinned start.s
        check = tmp / 'standalone'
        (check / 'osfmk/arm64').mkdir(parents=True)
        (check / 'osfmk/arm64/start.s').write_text(start, encoding='utf-8', newline='')
        subprocess.run([GIT, 'init', '-q'], cwd=check, check=True)
        apply(check, PATCH)
        print('standalone git apply --check against pinned start.s: PASS')

        # full series order: fb fix -> start signals -> boot marks -> early console flush
        series = tmp / 'series'
        files = {
            'osfmk/arm64/start.s': start,
            'osfmk/arm/arm_init.c': fetch('osfmk/arm/arm_init.c', args.xnu_dir).read_text(encoding='utf-8'),
            'osfmk/kern/startup.c': fetch('osfmk/kern/startup.c', args.xnu_dir).read_text(encoding='utf-8'),
        }
        vc = fetch('osfmk/console/video_console.c', args.xnu_dir).read_text(encoding='utf-8')
        files['osfmk/console/video_console.c'] = vc
        for rel, text in files.items():
            target = series / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8', newline='')
        subprocess.run([GIT, 'init', '-q'], cwd=series, check=True)
        for patch in (FB_PATCH, PATCH, MARKS_PATCH, FLUSH_PATCH):
            apply(series, patch)
        print('full series order (fb fix -> start signals -> boot marks -> early flush): PASS')

    lines = SERIES.read_text(encoding='utf-8').splitlines()
    name = PATCH.name
    if name not in [line.strip() for line in lines]:
        fb = next((i for i, line in enumerate(lines)
                   if line.strip().startswith('zzzzz-fix-darwinboot')), -1)
        insert_at = fb + 1 if fb >= 0 else 0
        lines[insert_at:insert_at] = [
            '# [diagnostic, bring-up only] start.s A/B/C signals: red FB before MMU, green FB at',
            '# SCTLR_EL1 write, PSCI SYSTEM_RESET right after MMU enable; apply before boot-marks.',
            name,
        ]
        SERIES.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('added to patches/xnu/device/series')


if __name__ == '__main__':
    main()
