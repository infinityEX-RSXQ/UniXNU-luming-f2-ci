from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from qualify_stage16_kernel import inspect,ipc_calls,REQUIRED
paths=list(Path('unixnu/out').glob('**/kernel/kernel.macho'));assert len(paths)==1
kernel=paths[0];info=inspect(kernel);raw=kernel.read_bytes()
assert all('_'+n in info['defined'] for n in REQUIRED)
for marker in [b'CDX16 snapshot (intentional)',b'CDX16VsyncState',b'vst=%u sa=%u ar=%u aa=%u sf=%x af=%x hz=%u']:
    assert marker in raw,'missing Stage16 marker: '+repr(marker)
expected=json.loads((HERE/'validation.json').read_text())
installed=json.loads(Path('ci-artifacts/stage16-install-report.json').read_text())
previous=json.loads(Path('ci-artifacts/stage15-install-report.json').read_text())
assert installed['applied'] and installed['before']==expected['before'] and installed['after']==expected['after']
for rel in installed['after']:assert previous['after'][rel]==installed['before'][rel]
reports=list(Path('unixnu/out').glob('**/tree/build/native-legacy-display/build-report.json'))
reports+=list(Path('unixnu/build/native-legacy-display').glob('build-report.json'));assert reports
report=json.loads(reports[0].read_text())
for materialized,template in [('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'),
    ('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp')]:
    assert report['source_sha256'][materialized]==installed['after'][template]
assert report['generated_abi_sha256']=='8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016'
assert report['virtual_entries']==358 and not report['original_instructions_modified']
assert report['original_kernelcache_sha256']=='f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7'
result=dict(stage=16,kernel=str(kernel),sha256=info['sha256'],bytes=info['bytes'],
    source_chain_verified=True,abi_unchanged=True,core_calls=ipc_calls(kernel),qualified=True,runtime_verified=False)
Path('ci-artifacts/stage16-kernel-check.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
