#!/usr/bin/env python3
"""Build the luming UFS diagnostic log writer (package/BootLog.c) against this kernel's own compile record."""
import json
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/luming-boot-log'
OUT.mkdir(parents=True, exist_ok=True)
record = json.loads((ROOT / 'build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837/osfmk/DEVELOPMENT/startup.o.json').read_text().strip().rstrip(','))
base = ROOT / 'kits/luming'
if not (base / 'BootLog.c').is_file():
    device = Path(os.environ.get('UNIXNU_DEVICE', ''))
    if (device / 'kits/luming/BootLog.c').is_file():
        base = device / 'kits/luming'
source = base / 'BootLog.c'
obj = OUT / 'BootLog.o'
command = []
args = record['arguments']
i = 0
while i < len(args):
    arg = args[i]
    if arg == record['file']:
        command.append(str(source))
    elif arg in ('-o', '-MF', '-MT', '-MJ'):
        if arg == '-o':
            command += ['-o', str(obj)]
        i += 1
    elif arg == '-Xclang' and args[i + 1].startswith('-W'):
        i += 1
    elif arg == '-D' and args[i + 1].startswith('XNU_BOOT_PROGRESS='):
        i += 1
    elif not arg.startswith(('-W', '-DXNU_BOOT_PROGRESS=')):
        command.append(arg)
    i += 1
command += ['-mgeneral-regs-only', '-I', str(ROOT / '.cache/xnu-work/osfmk')]
result = subprocess.run(command, cwd=record['directory'], capture_output=True, text=True, timeout=120)
if result.returncode:
    raise SystemExit(result.stdout[-4000:] + result.stderr[-4000:])
proc_source = base / 'BootProcessProbe.c'
proc_obj = OUT / 'BootProcessProbe.o'
proc_command = [str(proc_source) if arg == str(source) else str(proc_obj) if arg == str(obj) else arg for arg in command]
result = subprocess.run(proc_command, cwd=record['directory'], capture_output=True, text=True, timeout=120)
if result.returncode:
    raise SystemExit(result.stdout[-4000:] + result.stderr[-4000:])
# The diagnostic boot marks are part of the same archive (kits/luming/BootMarks.c); they paint
# stage bands on the GOP framebuffer before the XNU console attaches (diagnostic builds only).
if (base / 'BootMarks.c').is_file():
    marks_source = base / 'BootMarks.c'
    marks_obj = OUT / 'BootMarks.o'
    marks_command = [str(marks_source) if arg == str(source) else str(marks_obj) if arg == str(obj) else arg
                     for arg in command]
    result = subprocess.run(marks_command, cwd=record['directory'], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise SystemExit(result.stdout[-4000:] + result.stderr[-4000:])
    archive_members = [str(obj), str(proc_obj), str(marks_obj)]
else:
    archive_members = [str(obj), str(proc_obj)]
archive = OUT / 'libLumingBootLog.a'
archive.unlink(missing_ok=True)
subprocess.run(['xcrun', 'ar', 'rcs', str(archive), *archive_members], check=True)
(OUT / 'build-report.json').write_text(json.dumps({
    'source_sha256': __import__('hashlib').sha256(source.read_bytes()).hexdigest(),
    'archive_sha256': __import__('hashlib').sha256(archive.read_bytes()).hexdigest(),
}, indent=2) + '\n')
print('PASS: luming UFS diagnostic log writer built')