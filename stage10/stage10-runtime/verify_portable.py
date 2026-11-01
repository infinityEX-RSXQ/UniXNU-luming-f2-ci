"""Run the upstream CPU-copy/request-state tests against this exact header.

This checks portable bounds and byte-copy behavior; it does not compile XNU.
"""
from pathlib import Path
import argparse,json,shutil,subprocess,tempfile
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--cc',default=shutil.which('clang') or 'clang');args=p.parse_args()
with tempfile.TemporaryDirectory(prefix='portable-',dir=R) as td:
    exe=Path(td)/'request-state.exe'
    cmd=[args.cc,'-Wall','-Wextra','-Werror',str(R/'Test/request-state.c'),'-o',str(exe)]
    build=subprocess.run(cmd,capture_output=True,text=True)
    run=subprocess.run([str(exe)],capture_output=True,text=True) if build.returncode==0 else None
    result={'compile_command':cmd,'compile_exit_code':build.returncode,'compile_output':build.stdout+build.stderr,
        'test_exit_code':run.returncode if run else None,'test_output':run.stdout+run.stderr if run else None,
        'scope':'Host C assertions: layer masks, blank frame state, integer overflow, row padding, source alignment, destination alignment and bounded CPU copy. No macOS runtime, ABI or device claim.'}
    (R/'portable-tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    assert build.returncode==0,result
    assert run.returncode==0,result
print('PASS: host request-state and CPU-copy bounds assertions; no device test.')
