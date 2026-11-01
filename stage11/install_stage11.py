"""Install into dsh's isolated stage10 CI device checkout, BEFORE pre_build.

Dry run by default. Does not modify board/defconfig/backend or run device tools.
Existing stage9 generator produces ONE combined source patch with both hooks.
"""
from pathlib import Path
import argparse, hashlib, json
HERE = Path(__file__).resolve().parent
PINS = {
    'scripts/ci/gen_aslr_patch.py': '5d8cc19a4e007e765e7e4f0646710b8ba05a7e78f4127c10fa1952661bf1c36a',
    'scripts/ci/instrument_aslr_short_diagnostics.py': '0539691c11bf879c803c4e79ae851de800b4c727bca694f2f7b97eaa0cfe390d',
    'stage10/stage10-runtime/LegacyDisplayProbe.cpp': '1095ed281386e808eee075b17a7b0180e4c7161a179c9e2dda213071df061485',
}

def digest(b): return hashlib.sha256(b).hexdigest()

def change_generator(text):
    old = 'TARGETS = ("osfmk/kern/exception.c", "bsd/vm/vm_unix.c")'
    new = 'TARGETS = ("osfmk/kern/exception.c", "bsd/vm/vm_unix.c", "bsd/kern/kern_exit.c")'
    assert text.count(old) == 1
    text = text.replace(old,new)
    old = '    for rel in TARGETS:\n        shutil.copy2(feed / rel, tmp / rel)'
    new = '    for rel in TARGETS:\n        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)\n        shutil.copy2(feed / rel, tmp / rel)'
    assert text.count(old) == 1
    text = text.replace(old,new)
    anchor = '    print(r.stdout.strip())\n\n    diff = git(tmp, "diff", "--", *TARGETS).stdout'
    replacement = '''    print(r.stdout.strip())
    # CDX11: same prepared source, after stage9 diagnostics, before diff output.
    extra = Path(__file__).with_name("instrument_crash_snapshot.py")
    subprocess.run([sys.executable, str(extra), str(tmp)], check=True)

    diff = git(tmp, "diff", "--", *TARGETS).stdout
    if "CDX11_CAPTURE" not in diff or "CDX11_FINAL" not in diff:
        raise SystemExit("stage11 crash snapshot missing from generated source patch")'''
    assert text.count(anchor) == 1
    return text.replace(anchor,replacement)

def install(device, apply=False):
    before = {}
    for rel, pin in PINS.items():
        path = device/rel
        raw = path.read_bytes()
        # Windows source packages may carry CRLF; compare the same LF bytes
        # the existing macOS CI compiled, without accepting content changes.
        normalized = raw.replace(b'\r\n', b'\n')
        assert digest(normalized) == pin, f'Pinned stage10 source drift: {path}'
        before[rel] = normalized
    header = (HERE/'CrashSnapshot.h').read_text(encoding='utf-8')
    probe = before['stage10/stage10-runtime/LegacyDisplayProbe.cpp'].decode()
    assert 'CDX11' not in probe and probe.count('volatile uint32_t native_legacy_stage') == 1
    changes = {
        'scripts/ci/gen_aslr_patch.py': change_generator(before['scripts/ci/gen_aslr_patch.py'].decode()).encode(),
        'scripts/ci/instrument_crash_snapshot.py': (HERE/'instrument_crash_snapshot.py').read_bytes(),
        # Inline the helper: the existing three-member archive and its four
        # materialized inputs remain unchanged; no extra include-copy hook.
        'stage10/stage10-runtime/LegacyDisplayProbe.cpp': (probe+'\n// CDX11 owned diagnostics: source-only, no rendering changes.\n#include <libkern/libkern.h>\n'+header).encode(),
    }
    assert not (device/'scripts/ci/instrument_crash_snapshot.py').exists(), 'Refuse overwrite'
    report = {'source_before':{k:digest(v) for k,v in before.items()},
        'source_after':{k:digest(v) for k,v in changes.items()},
        'stage10_backend_unchanged':True, 'board_defconfig_unchanged':True,
        'full_kernel_compiled':False, 'device_operations':False, 'applied':apply}
    if apply:
        for rel, data in changes.items():
            path = device/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    print(json.dumps(install(args.device.resolve(),args.apply),indent=2))
