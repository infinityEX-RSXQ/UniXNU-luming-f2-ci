from pathlib import Path
import hashlib,importlib.util,json,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
integration=json.loads((HERE/'integration-validation.json').read_text(encoding='utf-8'))
host=json.loads((HERE/'host-validation.json').read_text(encoding='utf-8'))
assert integration['passed'] and host['core_policy_tests'] and host['provider_tests'] and host['no_fp_simd_in_fixtures']
spec=importlib.util.spec_from_file_location('qual14',HERE/'qualify_stage14_kernel.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
old=ROOT/'builds/stage13-ui-scale-41320061953'
try:q.check(old/'kernel.macho',ROOT/'builds/aslr-short-diag-20261101/kernel.macho',
    'f2517633fedf3dc1382ca6eedefc0bad01ac0b57a40f2170d4157030c416692d',old/'build-report.json',HERE/'integration-validation.json')
except AssertionError as e:
    assert 'Missing Stage14 definition' in str(e)
    negative=dict(rejected=True,reason=str(e))
else:raise AssertionError('Old kernel accepted')
(HERE/'stage13-negative-test.json').write_text(json.dumps(negative,indent=2),encoding='utf-8')
files=[p for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.json']
manifest=dict(stage=14,base_ci_run=41320061953,base_commit='6535914a16f5aa5b8cf88c8e63988403397face0',
    full_kernel_compiled=False,runtime_verified=False,device_operations=False,
    tests=host,source_patch_chain_passed=True,files=[dict(path=p.relative_to(HERE).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files])
mp=HERE/'manifest.json';mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8');files.append(mp)
bundle=ROOT/'DSH-STAGE14-SCANOUT-SOURCE-20261102.zip';assert not bundle.exists()
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(HERE).as_posix())
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    for f in manifest['files']:assert hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256']
report=dict(stage=14,bundle=str(bundle),bytes=bundle.stat().st_size,sha256=sha(bundle),checks=host,
    source_after=integration['after'],source_patch_chain_passed=True,device_operations=False,
    runtime_verified=False,full_kernel_compiled=False)
(ROOT/'evidence/STAGE14-DELIVERY-20261102.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
text=(HERE/'BUILD-REQUEST.md').read_text(encoding='utf-8')
text+='\n## 交付包\n\n`'+str(bundle)+'`\n\nSHA256：`'+report['sha256']+'`\n'
(ROOT/'HANDOVER-DSH-STAGE14-SCANOUT-20261102.md').write_text(text,encoding='utf-8')
print(json.dumps({k:report[k] for k in ['bundle','bytes','sha256']},indent=2))
