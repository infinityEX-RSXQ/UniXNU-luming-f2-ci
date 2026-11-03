"""Create a source-only handoff with an independently checked file manifest."""
from pathlib import Path
import hashlib,json,zipfile
HERE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':
    validation=json.loads((HERE/'validation.json').read_text())
    assert validation['host_checks_passed']
    assert json.loads((HERE/'ci-preflight.json').read_text())['passed']
    paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
           and p.name!='MANIFEST.json' and p.suffix not in ('.pyc','.exe','.o','.zip')]
    manifest={p.relative_to(HERE).as_posix():sha(p.read_bytes()) for p in sorted(paths)}
    (HERE/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    archive=HERE.parent/'DSH-STAGE21-STACKSHOT-SOURCE-20261104.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in paths+[HERE/'MANIFEST.json']:z.write(p,'stage19/'+p.relative_to(HERE).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for rel,h in manifest.items():assert sha(z.read('stage19/'+rel))==h
    result=dict(path=str(archive),sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,files=len(paths)+1,
        source_only=True,full_kernel_compiled=False,runtime_verified=False)
    (HERE.parent/'evidence/STAGE21-SOURCE-PACKAGE-20261104.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
