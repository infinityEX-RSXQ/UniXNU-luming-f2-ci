#!/usr/bin/env python3
"""Compile isolated candidate hook units with actual XNU records; never touch device."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import build

UNITS = {
    'pexpert/DEVELOPMENT/pe_kprintf.o.json': 'pexpert/arm/pe_kprintf.c',
    'osfmk/DEVELOPMENT/debug.o.json': 'osfmk/kern/debug.c',
    'osfmk/DEVELOPMENT/printf.o.json': 'osfmk/kern/printf.c',
    'osfmk/DEVELOPMENT/serial_console.o.json': 'osfmk/console/serial_console.c',
    'osfmk/DEVELOPMENT/serial_general.o.json': 'osfmk/console/serial_general.c',
    'bsd/DEVELOPMENT/bsd_init.o.json': 'bsd/kern/bsd_init.c',
}

def run(argv, cwd=None):
    result = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        print(result.stdout[-10000:], result.stderr[-10000:], file=sys.stderr)
        raise RuntimeError(f'command failed ({result.returncode}): {argv[0]}')
    return result.stdout

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('xnu', 'records', 'archive', 'nm', 'patch', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    module = Path(__file__).resolve().parents[1]
    out = a.output.resolve()
    if not any(x in ('tmp', '.cache') for x in out.parts) or module in out.parents:
        p.error('output must be outside module under tmp/ or .cache/')
    out.mkdir(parents=True, exist_ok=False)
    tree = out/'source'
    for name in UNITS.values():
        src = a.xnu/name
        dest = tree/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    run(['git', 'apply', '--check', a.patch.resolve()], tree)
    run(['git', 'apply', a.patch.resolve()], tree)
    def symbols(*args):
        return {line.split()[-1] for line in run([a.nm.resolve(), *args]).splitlines()
                if line.strip() and not line.endswith(':')}
    exports = symbols('--defined-only', '--extern-only', a.archive.resolve())
    checks = {}
    for record_name, name in UNITS.items():
        record = json.loads((a.records/record_name).read_text().rstrip().rstrip(','))
        flags, cwd = build.compile_flags(record)
        for enabled in (0, 1):
            obj = out/(Path(name).stem+'-'+str(enabled)+'.o')
            argv = flags + ['-UXNU_QCOM_USB_DEBUG', f'-DXNU_QCOM_USB_DEBUG={enabled}',
                            '-I'+str(module/'include'), '-Wno-reserved-identifier',
                            '-Wno-pre-c11-compat', '-c', str(tree/name), '-o', str(obj)]
            run(argv, cwd)
            imports = symbols('--undefined-only', obj)
            hooks = {x for x in imports if x.startswith('_qcom_usb_debug_')}
            if not enabled and hooks: raise RuntimeError('disabled unit imports USB hooks: '+name)
            if enabled and name != 'osfmk/console/serial_general.c' and not hooks:
                raise RuntimeError('enabled unit missing USB hooks: '+name)
            if not hooks <= exports: raise RuntimeError('archive missing '+str(hooks-exports))
            checks[name+':enabled='+str(enabled)] = sorted(hooks)
            print('PASS', name, 'enabled='+str(enabled), flush=True)
    report = {'hardware_verified':False, 'kernel_linked':False,
              'patch_sha256':hashlib.sha256(a.patch.read_bytes()).hexdigest(), 'checks':checks}
    (out/'hook-check-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Hook units compiled enabled and disabled; full kernel not linked')

if __name__ == '__main__': main()
