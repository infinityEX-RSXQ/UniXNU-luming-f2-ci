from pathlib import Path
import hashlib,importlib.util,json,os,re,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
BASE=ROOT/'builds/stage14p1-ci-work/p1-fixture/device'
REPO=ROOT/'builds/stage14p1-ci-work/repo'
WORK=Path('D:/Codex/workspaces/2026-10-29/zai/work');REF=WORK/'stage11-diagnostic/reference'
XNU=ROOT/'builds/aslr-short-diag-20261101/xnu';GIT=Path('C:/Program Files/Git/cmd/git.exe')
os.environ['PATH']=str(GIT.parent)+os.pathsep+os.environ['PATH']
sys.path.insert(0,str(HERE));from make_core_patch15 import build;from install_stage15 import install,PINS
def run(args,cwd=None):
    p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
    assert p.returncode==0,p.stdout+'\n'+p.stderr;return p.stdout
build();fixture=Path('D:/Codex/tmp')/('stage15-check-'+str(time.time_ns()));device=fixture/'device';feed=fixture/'feed'
rels=list(PINS)+['patches/xnu/device/series','scripts/ci/gen_aslr_patch.py',
    'scripts/ci/instrument_aslr_short_diagnostics.py','scripts/ci/instrument_crash_snapshot.py']
for rel in rels:
    p=device/rel;p.parent.mkdir(parents=True,exist_ok=True);source=BASE/rel
    if not source.exists():source=REPO/rel
    p.write_bytes(source.read_bytes())
assert not install(device,False)['applied'];report=install(device,True)
try:install(device,True)
except AssertionError:pass
else:raise AssertionError('Double install accepted')
for rel in ['bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c']:
    p=feed/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((REF/rel).read_bytes())
rel='iokit/Kernel/IOUserClient.cpp';p=feed/rel;p.parent.mkdir(parents=True);p.write_bytes((XNU/rel).read_bytes())
patch=device/'patches/xnu/device/zzzzz-cdx-generated-aslr.patch'
report['generator_output']=run([sys.executable,device/'scripts/ci/gen_aslr_patch.py',REF/'core',feed,patch,device/'patches/xnu/device/series'])
patch.write_text(patch.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
report['generated_aslr_sha256']=hashlib.sha256(patch.read_bytes()).hexdigest()
assert report['generated_aslr_sha256']=='16541d2ae10b2c26fc9f5db477c577d5fd32591825b5db1230a407f73730e90b'
run([GIT,'init','-q'],feed);run([GIT,'apply','--check',patch],feed);run([GIT,'apply',patch],feed)
targets={'bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c','iokit/Kernel/IOUserClient.cpp'};selected=[]
for line in (device/'patches/xnu/device/series').read_text(encoding='utf-8').splitlines():
    entry=line.strip()
    if not entry or entry.startswith('#') or 'cdx-generated-aslr' in entry:continue
    p=device/'patches/xnu/device'/entry
    if not p.exists():p=BASE/'patches/xnu/device'/entry
    if not p.exists():p=REPO/'patches/xnu/device'/entry
    text=p.read_text(encoding='utf-8');starts=list(re.finditer(r'(?m)^(?:diff --git |--- a/)',text));chunks=[]
    for i,m in enumerate(starts):
        if not m.group().startswith('---'):continue
        end=starts[i+1].start() if i+1<len(starts) else len(text);chunk=text[m.start():end]
        if chunk.splitlines()[0][6:].split('\t')[0] in targets:chunks.append(chunk)
    if not chunks:continue
    p=fixture/('part-'+str(len(selected))+'.patch');p.write_text(''.join(chunks),encoding='utf-8',newline='\n')
    run([GIT,'apply','--check',p],feed);run([GIT,'apply',p],feed);selected.append(entry)
runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
for name in ['LegacyDisplayProbe.cpp','NativeLegacyDisplay.cpp']:(runtime/name).write_bytes((device/'stage10/stage10-runtime'/name).read_bytes())
probe=(runtime/'LegacyDisplayProbe.cpp').read_text(encoding='utf-8')
assert probe.index('cdx15_snapshot(reason,sizeof(reason),quiet);')<probe.index('unsigned reclaimed=quiet?cdx14p1_console_reclaim():0;',probe.index('cdx15_snapshot(reason,sizeof(reason),quiet);'))
backend=(runtime/'NativeLegacyDisplay.cpp').read_text(encoding='utf-8')
assert backend.count('cdx15_target_observed();')==2 and 'newUserClient(task_t task,void *security,UInt32 type,IOUserClient **client)' in backend
assert backend.count('cdx15_retire_begin(request)')==1 and backend.count('cdx15_retire_end(request,cdx15_generation)')==1
ipc=(feed/'iokit/Kernel/IOUserClient.cpp').read_text(encoding='utf-8')
assert ipc.count('cdx15_ipc_begin(this, selector)')==1 and ipc.count('cdx15_ipc_end(cdx15_token, (uint32_t)ret)')==1
report.update(passed=True,fixture=str(fixture),compatible_device_patches=selected,
    aslr_patch_unchanged=True,source_abi_signatures_preserved=True,full_kernel_compiled=False,runtime_verified=False)
(HERE/'integration-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
