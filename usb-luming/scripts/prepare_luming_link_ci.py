#!/usr/bin/env python3
"""Modify only a disposable CI checkout for an experimental model link."""
import argparse
import os
from pathlib import Path
import subprocess
import shutil

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('workspace', 'patch', 'archive', 'include'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    workspace = a.workspace.resolve()
    if os.environ.get('GITHUB_ACTIONS') != 'true' or Path(os.environ.get('GITHUB_WORKSPACE', '')).resolve() != workspace:
        raise SystemExit('refusing outside the current GitHub Actions workspace')
    core = workspace/'unixnu'
    tree = core/'out/luming/ipados-17.7.11-21H461/luming/tree'
    xnu = tree/'.cache/xnu-work'
    records = tree/'build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837'
    for path in (xnu, records, a.patch, a.archive, a.include):
        if not path.exists(): raise SystemExit('missing required input: '+str(path))
    subprocess.run(['git', 'apply', '--check', str(a.patch.resolve())], cwd=xnu, check=True)
    subprocess.run(['git', 'apply', str(a.patch.resolve())], cwd=xnu, check=True)
    kernel = core/'scripts/unixnu/kernel.py'
    source = kernel.read_text(encoding='utf-8')
    begin = source.index('def xnu_env(ctx):')
    end = source.index('\ndef version_env(', begin)
    segment = source[begin:end]
    needle = '    return env\n'
    if segment.count(needle) != 1: raise RuntimeError('unexpected xnu_env layout')
    replacement = '''    if os.environ.get('LUMING_USB_MODEL_LINK') == '1':
        env['XNU_EXTRA_CFLAGS'] = env.get('XNU_EXTRA_CFLAGS', '') + ' -DXNU_QCOM_USB_DEBUG=1 -I' + os.environ['LUMING_USB_INCLUDE']
        env['XNU_EXTRA_LD_ARCHIVES'] = env.get('XNU_EXTRA_LD_ARCHIVES', '') + ' -Wl,-force_load,' + os.environ['LUMING_USB_ARCHIVE']
    return env
'''
    kernel.write_text(source[:begin]+segment.replace(needle, replacement)+source[end:], encoding='utf-8')
    # Reuse the exact enabled hook units compiled and checked immediately above.
    # The build pipeline scans existing kernel objects before invoking make; deleting
    # them here breaks its corecrypto symbol scan before recompilation can occur.
    hooks = workspace/'tmp/usb-hooks'
    objects = {'pe_kprintf-1.o':'pexpert/DEVELOPMENT/pe_kprintf.o',
               'debug-1.o':'osfmk/DEVELOPMENT/debug.o',
               'printf-1.o':'osfmk/DEVELOPMENT/printf.o',
               'serial_console-1.o':'osfmk/DEVELOPMENT/serial_console.o',
               'serial_general-1.o':'osfmk/DEVELOPMENT/serial_general.o',
               'bsd_init-1.o':'bsd/DEVELOPMENT/bsd_init.o'}
    for source_name, target_name in objects.items():
        src, target = hooks/source_name, records/target_name
        if not src.is_file() or not target.is_file():
            raise SystemExit('missing checked or original object: '+str(src)+' / '+str(target))
        shutil.copyfile(src, target)
    kernel_object = records/'mach.development.bcm2837.unstripped.noctf'
    if not kernel_object.is_file(): raise SystemExit('missing previous kernel: '+str(kernel_object))
    kernel_object.unlink()
    print('Prepared disposable source for model link; hardware unqualified')

if __name__ == '__main__': main()
