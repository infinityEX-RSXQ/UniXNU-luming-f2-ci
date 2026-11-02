from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from qualify_stage17_kernel import inspect,calls,REQUIRED
kernels=list(Path('unixnu/out').glob('**/kernel/kernel.macho'));assert len(kernels)==1
kernel=kernels[0];raw=kernel.read_bytes();info=inspect(kernel)
assert all('_'+s in info['defined'] for s in REQUIRED)
for s in [b'CDX17 snapshot (intentional)',b'CDX17IPCState',b'luming-display-ipc-page']:assert s in raw
expected=json.loads((HERE/'validation.json').read_text())
installed=json.loads(Path('ci-artifacts/stage17-install-report.json').read_text())
previous=json.loads(Path('ci-artifacts/stage16-install-report.json').read_text())
assert installed['applied'] and installed['before']==expected['before'] and installed['after']==expected['after']
import hashlib
series=(HERE/'series-stage16.txt').read_text().rstrip()+'\nzzzzzzzzzzzzzzzzzzzzzzzz-cdx17-observe.patch\n'
assert hashlib.sha256(series.encode()).hexdigest()==installed['after']['patches/xnu/device/series']
# The existing gen_aslr_patch.py subsequently replaces the disabled diagnostic
# comment with the generated patch at the first active entry. Verify its exact
# deterministic transformation, rather than comparing pre-build and final files.
lines=[s for s in series.splitlines() if 'cdx-generated-aslr' not in s and 'cdx-exception-aslr-diagnostic' not in s]
insert=next(i for i,s in enumerate(lines) if s.strip() and not s.lstrip().startswith('#'))
lines.insert(insert,'zzzzz-cdx-generated-aslr.patch')
assert Path('device/patches/xnu/device/series').read_bytes()==('\n'.join(lines)+'\n').encode()
for rel in previous['after']:assert installed['before'][rel]==previous['after'][rel]
reports=list(Path('unixnu/out').glob('**/tree/build/native-legacy-display/build-report.json'))
reports+=list(Path('unixnu/build/native-legacy-display').glob('build-report.json'));assert reports
report=json.loads(reports[0].read_text())
final18=json.loads(Path('ci-artifacts/stage18-install-report.json').read_text())
for rel in ('stage10/stage10-runtime/LegacyDisplayProbe.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'):assert final18['before'][rel]==installed['after'][rel]
for a,b in [('kits/luming-cpu-display/LegacyDisplayProbe.cpp','LegacyDisplayProbe.cpp'),('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','NativeLegacyDisplay.cpp')]:
    assert report['source_sha256'][a]==final18['after']['stage10/stage10-runtime/'+b]
assert report['generated_abi_sha256']=='8c996ed2c36eb973fc4f4a4ed644498710dacec6120ae1e4f524ab5653120e8a'
assert report['virtual_entries']==358 and not report['original_instructions_modified']
assert report['original_kernelcache_sha256']=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
out=dict(stage=17,sha256=info['sha256'],bytes=info['bytes'],source_chain_verified=True,abi_unchanged=True,core_calls=calls(kernel),qualified=True,runtime_verified=False)
Path('ci-artifacts/stage17-kernel-check.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
