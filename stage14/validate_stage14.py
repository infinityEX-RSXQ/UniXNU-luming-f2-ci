from pathlib import Path
import hashlib,importlib.util,json,os,re,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
WORK=Path('D:/Codex/workspaces/2026-10-29/zai/work')
BASE=WORK/'stage13-mode/fixture-1793543559382351700/device'
ROOT=Path('D:/civitoip20/lumingios-cdx')
ORIGINAL=ROOT/'builds/stage13-ci-work/repo'
REFERENCE=WORK/'stage11-diagnostic/reference'
GIT=Path('C:/Program Files/Git/cmd/git.exe')
os.environ['PATH']=str(GIT.parent)+os.pathsep+os.environ['PATH']
sys.path.insert(0,str(HERE))
from install_stage14 import install
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def run(args,cwd=None):
    p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
    assert p.returncode==0,p.stdout+'\n'+p.stderr;return p.stdout
fixture=Path('D:/Codex/tmp')/('stage14-check-'+str(time.time_ns()));device=fixture/'device';feed=fixture/'feed'
shutil.copytree(BASE,device,ignore=shutil.ignore_patterns('.cache','.git'))
report=install(device,False);assert not report['applied'];report=install(device,True)
try:install(device,True)
except AssertionError:pass
else:raise AssertionError('Double install accepted')
for rel in ['bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c']:
    p=feed/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((REFERENCE/rel).read_bytes())
console=feed/'osfmk/console/video_console.c';console.parent.mkdir(parents=True)
console.write_bytes((ROOT/'builds/aslr-short-diag-20261101/xnu/osfmk/console/video_console.c').read_bytes())
patch=device/'patches/xnu/device/zzzzz-cdx-generated-aslr.patch'
report['generator_output']=run([sys.executable,device/'scripts/ci/gen_aslr_patch.py',REFERENCE/'core',feed,patch,device/'patches/xnu/device/series'])
patch.write_text(patch.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
run([GIT,'init','-q'],feed);run([GIT,'apply','--check',patch],feed);run([GIT,'apply',patch],feed)
targets={'bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c','osfmk/console/video_console.c'}
selected=[]
for line in (device/'patches/xnu/device/series').read_text(encoding='utf-8').splitlines():
    entry=line.strip()
    if not entry or entry.startswith('#') or 'cdx-generated-aslr' in entry:continue
    p=device/'patches/xnu/device'/entry
    if not p.exists():p=ORIGINAL/'patches/xnu/device'/entry
    text=p.read_text(encoding='utf-8');starts=list(re.finditer(r'(?m)^(?:diff --git |--- a/)',text));chunks=[]
    for i,m in enumerate(starts):
        if not m.group().startswith('---'):continue
        end=starts[i+1].start() if i+1<len(starts) else len(text);chunk=text[m.start():end]
        if chunk.splitlines()[0][6:].split('\t')[0] in targets:chunks.append(chunk)
    if not chunks:continue
    p=fixture/('selected-'+str(len(selected))+'.patch');p.write_text(''.join(chunks),encoding='utf-8',newline='\n')
    run([GIT,'apply','--check',p],feed);run([GIT,'apply',p],feed);selected.append(entry)
inst=module('extra14',device/'scripts/ci/instrument_aslr_short_diagnostics.py')
ex=(feed/'osfmk/kern/exception.c').read_text(encoding='utf-8')
assert inst.exception_instrument(ex)==ex and ex.count('/* CDX14_DAEMON_EXC */')==1
assert ex.count('/* CDX11_CAPTURE:')==1 and 'get_saved_state_reg(thread->machine.upcb, 28)' in ex
runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
for name in ['LegacyDisplayProbe.cpp','NativeLegacyDisplay.cpp']:(runtime/name).write_bytes((device/'stage10/stage10-runtime'/name).read_bytes())
backend=(runtime/'NativeLegacyDisplay.cpp').read_text(encoding='utf-8')
assert backend.index('cdx14_frame_end(true);')<backend.index('OSSafeReleaseNULL(source);transferred=true;')
assert 'cdx14_frame_end(false);' in backend
report.update(passed=True,fixture=str(fixture),compatible_source_patches=selected,
    exception_instrumentation_idempotent=True,full_kernel_compiled=False,runtime_verified=False,
    generated_patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest())
(HERE/'example-generated-source.patch').write_bytes(patch.read_bytes())
(HERE/'integration-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
