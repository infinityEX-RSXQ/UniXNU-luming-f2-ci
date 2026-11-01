"""Exercise the actual generator and later device patches on pinned sources."""
from pathlib import Path
import ast, difflib, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, time, urllib.request
HERE=Path(__file__).resolve().parent
DEVICE=Path('D:/civitoip20/lumingios-cdx/builds/stage10-ci-work/repo')
GIT=Path('C:/Program Files/Git/cmd/git.exe')
os.environ['PATH']=str(GIT.parent)+os.pathsep+os.environ['PATH']
sys.path.insert(0,str(HERE))
from install_stage11 import install
from instrument_crash_snapshot import exception_instrument, exit_instrument, CAPTURE, SUMMARY

def run(args,cwd=None):
    p=subprocess.run([str(x) for x in args],cwd=cwd,text=True,capture_output=True)
    assert p.returncode==0, '\n'.join(map(str,args))+'\n'+p.stdout+'\n'+p.stderr
    return p.stdout

fixture=HERE/('validation-fixture-'+str(time.time_ns()))
assert not fixture.exists(), 'Use a fresh validation directory, never overwrite'
device=fixture/'device'; feed=fixture/'feed'
for rel in ['scripts/ci/gen_aslr_patch.py','scripts/ci/instrument_aslr_short_diagnostics.py',
            'stage10/stage10-runtime/LegacyDisplayProbe.cpp','patches/xnu/device/series']:
    p=device/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((DEVICE/rel).read_bytes())
report=install(device,True)
for rel in ['bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c']:
    source=HERE/'reference'/rel
    if not source.exists():
        url='https://raw.githubusercontent.com/apple-oss-distributions/xnu/d8b80295118ef25ac3a784134bcf95cd8e88109f/'+rel
        raw=urllib.request.urlopen(url,timeout=30).read();source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(raw)
    p=feed/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(source.read_bytes())
patch=device/'patches/xnu/device/zzzzz-cdx-generated-aslr.patch'
report['generator_stdout']=run([sys.executable,device/'scripts/ci/gen_aslr_patch.py',
    HERE/'reference/core',feed,patch,device/'patches/xnu/device/series'])
generated=patch.read_text()
# CI is macOS/LF. Python's Windows write_text defaults to CRLF for the old
# generator's final output, so normalize only this host fixture to CI bytes.
patch.write_text(generated,encoding='utf-8',newline='\n')
assert generated.count('CDX11_CAPTURE:')==1 and generated.count('CDX11_FINAL:')==1
run([GIT,'init','-q'],feed)
run([GIT,'apply','--check',patch],feed)
run([GIT,'apply',patch],feed)
exception=(feed/'osfmk/kern/exception.c').read_text()
exit_text=(feed/'bsd/kern/kern_exit.c').read_text()
assert exception_instrument(exception)==exception and exit_instrument(exit_text)==exit_text
# Removing the inserted blocks restores the stage9 texts exactly, including
# every exception return, panic condition, sync/coredump and panic argument.
spec=importlib.util.spec_from_file_location('old_inst',DEVICE/'scripts/ci/instrument_aslr_short_diagnostics.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
assert exception.replace(CAPTURE,'')==old.exception_instrument((HERE/'reference/osfmk/kern/exception.c').read_text())
assert exit_text.replace(SUMMARY,'')==(HERE/'reference/bsd/kern/kern_exit.c').read_text()
# Anchor drift must stop before source writes.
try: exit_instrument(exit_text.replace(SUMMARY,'').replace('sync(p, (void *)NULL, (int *)NULL);','sync_modified(p);'))
except AssertionError: pass
else: raise AssertionError('Did not reject drift')

selected=[]
targets={'bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c'}
for line in (DEVICE/'patches/xnu/device/series').read_text().splitlines():
    entry=line.strip()
    if not entry or entry.startswith('#') or 'cdx-generated-aslr' in entry: continue
    path=DEVICE/'patches/xnu/device'/entry
    text=path.read_text(encoding='utf-8')
    starts=list(re.finditer(r'(?m)^(?:diff --git |--- a/)',text))
    chunks=[]
    for i,m in enumerate(starts):
        if not m.group().startswith('---'): continue
        end=starts[i+1].start() if i+1<len(starts) else len(text)
        chunk=text[m.start():end]
        rel=chunk.splitlines()[0][6:].split('\t')[0]
        if rel in targets: chunks.append(chunk)
    if not chunks: continue
    selected_patch=fixture/('selected-'+str(len(selected))+'.patch')
    selected_patch.write_text(''.join(chunks),encoding='utf-8',newline='\n')
    run([GIT,'apply','--check',selected_patch],feed)
    run([GIT,'apply',selected_patch],feed)
    selected.append(entry)
final_exit=(feed/'bsd/kern/kern_exit.c').read_text()
assert final_exit.count(SUMMARY)==1 and final_exit.count('panic_with_options(')>=2
assert final_exit.index('proc_crash_coredump(p);') < final_exit.index('/* CDX11_FINAL:')
assert final_exit.index('sync(p, (void *)NULL, (int *)NULL);',final_exit.index('proc_handle_critical_exit(proc_t p, int rv)')) < final_exit.index('/* CDX11_FINAL:')
for rel in ['scripts/ci/gen_aslr_patch.py','scripts/ci/instrument_crash_snapshot.py']:
    ast.parse((device/rel).read_text())
report.update(passed=True, selected_later_device_patches=selected,
    generated_patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
    generated_patch_bytes=patch.stat().st_size, policy_removal_roundtrip=True,
    instrumentation_idempotent=True, anchor_drift_rejected=True,
    full_kernel_compiled=False, device_operations=False)
(HERE/'integration-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
