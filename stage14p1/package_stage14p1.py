from pathlib import Path
import hashlib,importlib.util,json,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
integration=json.loads((HERE/'integration-validation.json').read_text(encoding='utf-8'))
host=json.loads((HERE/'host-validation.json').read_text(encoding='utf-8'))
assert integration['passed'] and all(host[k] for k in ['quiesce_test','reclaim_test','arm64_provider_fixture','arm64_reclaim_fixture'])
spec=importlib.util.spec_from_file_location('q14p1',HERE/'qualify_stage14p1_kernel.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
old=ROOT/'builds/stage14-scanout-41359974470'
try:q.check(old/'kernel.macho',ROOT/'builds/aslr-short-diag-20261101/kernel.macho',
    '561aff1aad00c5b0679ed99879e16f89554c744609ad06875aaac2ca9460e377',old/'build-report.json',HERE/'integration-validation.json')
except AssertionError as e:
    assert 'Missing Stage14.1 definition' in str(e)
    negative=dict(rejected=True,reason=str(e))
else:raise AssertionError('Old Stage14 kernel accepted')
(HERE/'stage14-negative-test.json').write_text(json.dumps(negative,indent=2),encoding='utf-8')
files=[p for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.json']
manifest=dict(stage='14.1',base_ci_run=41359974470,base_commit=integration['base_commit'],checks=host,
    source_patch_check=True,full_kernel_compiled=False,runtime_verified=False,device_operations=False,
    files=[dict(path=p.relative_to(HERE).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files])
mp=HERE/'manifest.json';mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8');files.append(mp)
bundle=ROOT/'DSH-STAGE14P1-DIAGNOSTIC-SOURCE-20261102.zip';assert not bundle.exists()
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(HERE).as_posix())
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    for f in manifest['files']:assert hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256']
report=dict(stage='14.1',bundle=str(bundle),bytes=bundle.stat().st_size,sha256=sha(bundle),
    source_after=integration['after'],checks=host,source_patch_check=True,full_kernel_compiled=False,
    runtime_verified=False,device_operations=False,observation='User reports distorted Apple logo; uncertain whether diagnostic panic text ever appeared.')
(ROOT/'evidence/STAGE14P1-DELIVERY-20261102.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
text=(HERE/'BUILD-REQUEST.md').read_text(encoding='utf-8')
text+='\n## 交付包\n\n`'+str(bundle)+'`\n\nSHA256：`'+report['sha256']+'`\n'
(ROOT/'HANDOVER-DSH-STAGE14P1-DIAGNOSTIC-20261102.md').write_text(text,encoding='utf-8')
print(json.dumps({k:report[k] for k in ['bundle','bytes','sha256']},indent=2))
