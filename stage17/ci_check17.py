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
assert hashlib.sha256(Path('device/patches/xnu/device/series').read_bytes()).hexdigest()==installed['after']['patches/xnu/device/series']
for rel in previous['after']:assert installed['before'][rel]==previous['after'][rel]
reports=list(Path('unixnu/out').glob('**/tree/build/native-legacy-display/build-report.json'))
reports+=list(Path('unixnu/build/native-legacy-display').glob('build-report.json'));assert reports
report=json.loads(reports[0].read_text())
for a,b in [('kits/luming-cpu-display/LegacyDisplayProbe.cpp','LegacyDisplayProbe.cpp'),('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','NativeLegacyDisplay.cpp')]:
    assert report['source_sha256'][a]==installed['after']['stage10/stage10-runtime/'+b]
assert report['generated_abi_sha256']=='8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016'
assert report['virtual_entries']==358 and not report['original_instructions_modified']
assert report['original_kernelcache_sha256']=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
out=dict(stage=17,sha256=info['sha256'],bytes=info['bytes'],source_chain_verified=True,abi_unchanged=True,core_calls=calls(kernel),qualified=True,runtime_verified=False)
Path('ci-artifacts/stage17-kernel-check.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
