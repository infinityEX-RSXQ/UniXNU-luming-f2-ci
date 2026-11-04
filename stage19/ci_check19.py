from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from qualify_stage19_kernel import inspect,capture_call
expected=json.loads((HERE/'validation.json').read_text())
installed=json.loads(Path('ci-artifacts/stage19-install-report.json').read_text())
previous=json.loads(Path('ci-artifacts/stage18-install-report.json').read_text())
assert installed['applied'] and installed['before']==expected['before'] and installed['after']==expected['after']
for rel in installed['before']:assert installed['before'][rel]==previous['after'][rel]
for rel,h in installed['after'].items():assert hashlib.sha256((Path('device')/rel).read_bytes()).hexdigest()==h
kernels=list(Path('unixnu/out').glob('**/kernel/kernel.macho'));assert len(kernels)==1
kernel=kernels[0];info=inspect(kernel);raw=kernel.read_bytes()
for marker in (b'CDX24 q=',b'CDX23 q=',b'CDX22 q=',b'luming-display-stack-thread',b'CDX21 q=',b'CDX21State0',b'CDX21State1',b'luming-display-stack-owner',b'luming-display-stackshot',b'CDX19Raw0',b'CDX19Raw1',b'CDX19State0',b'CDX19State1',b'CDX19 stackshot (intentional)'):
    assert marker in raw,marker
reports=list(Path('unixnu/out').glob('**/tree/build/native-legacy-display/build-report.json'))
reports+=list(Path('unixnu/build/native-legacy-display').glob('build-report.json'));assert reports
report=json.loads(reports[0].read_text())
for materialized,template in [('kits/luming-cpu-display/LegacyDisplayProbe.cpp','stage10/stage10-runtime/LegacyDisplayProbe.cpp'),('drivers/GopFramebuffer/NativeLegacyDisplay.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp')]:
    assert report['source_sha256'][materialized]==installed['after'][template]
assert report['generated_abi_sha256']==expected['generated_abi_sha256'] and report['virtual_entries']==358
assert not report['original_instructions_modified']
result=dict(stage=19,sha256=info['sha256'],bytes=info['bytes'],stackshot_call=capture_call(kernel),qualified=True,runtime_verified=False)
Path('ci-artifacts/stage19-kernel-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
