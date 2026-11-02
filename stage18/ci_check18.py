from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from qualify_stage18_kernel import inspect,linked_calls,REQUIRED
expected=json.loads((HERE/'validation.json').read_text())
installed=json.loads(Path('ci-artifacts/stage18-install-report.json').read_text())
previous=json.loads(Path('ci-artifacts/stage17-install-report.json').read_text())
assert installed['applied'] and installed['before']==expected['before'] and installed['after']==expected['after']
for rel in previous['after']:
    if rel in installed['before']:assert installed['before'][rel]==previous['after'][rel]
paths=list(Path('unixnu/out').glob('**/kernel/kernel.macho'));assert len(paths)==1
kernel=paths[0];info=inspect(kernel);raw=kernel.read_bytes()
assert all('_'+n in info['defined'] for n in REQUIRED)
for marker in [b'CDX18WaitState',b'luming-display-wait-probe',b'boundary-samples']:assert marker in raw
reports=list(Path('unixnu/out').glob('**/tree/build/native-legacy-display/build-report.json'))
reports+=list(Path('unixnu/build/native-legacy-display').glob('build-report.json'));assert reports
report=json.loads(reports[0].read_text())
assert report['generated_abi_sha256']==expected['generated_abi_sha256']
assert report['virtual_entries']==358 and 176 in report['owned_entries']
for materialized,template in [('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp'),('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp')]:
    assert report['source_sha256'][materialized]==installed['after'][template]
for rel in installed['after']:assert hashlib.sha256((Path('device')/rel).read_bytes()).hexdigest()==installed['after'][rel]
result=dict(stage=18,sha256=info['sha256'],bytes=info['bytes'],wait_calls=linked_calls(kernel),qualified=True,runtime_verified=False)
Path('ci-artifacts/stage18-kernel-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
