from pathlib import Path
import hashlib,importlib.util,json,os,re,subprocess,sys,time
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'stage11-diagnostic'
DEVICE=Path('D:/civitoip20/lumingios-cdx/builds/stage10-ci-work/repo')
GIT=Path('C:/Program Files/Git/cmd/git.exe')
os.environ['PATH']=str(GIT.parent)+os.pathsep+os.environ['PATH']
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
stage11=module('stage11',OLD/'install_stage11.py')
stage12=module('stage12',HERE.parent/'stage12-mode/install_stage12.py')
from install_stage13 import install
fixture=HERE/('fixture-'+str(time.time_ns()));device=fixture/'device';feed=fixture/'feed'
for rel in list(stage11.PINS)+['stage10/stage10-runtime/NativeLegacyDisplay.cpp','patches/xnu/device/series']:
    p=device/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((DEVICE/rel).read_bytes())
stage11.install(device,True);stage12.install(device,True)
assert install(device,False)['applied']==False
report=install(device,True)
try:install(device,True)
except AssertionError:pass
else:raise AssertionError('Second install must reject source drift/double patch')
for rel in ['bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c']:
    p=feed/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((OLD/'reference'/rel).read_bytes())
def run(args,cwd=None):
    p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True);assert p.returncode==0,p.stdout+'\n'+p.stderr;return p.stdout
patch=device/'patches/xnu/device/zzzzz-cdx-generated-aslr.patch'
report['generator']=run([sys.executable,device/'scripts/ci/gen_aslr_patch.py',OLD/'reference/core',feed,patch,device/'patches/xnu/device/series'])
patch.write_text(patch.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
text=patch.read_text(encoding='utf-8');assert 'cdx13_capture_validity' in text and 'get_saved_state_reg(thread->machine.upcb, 28)' in text
assert 'cdx13_append_mode_summary' in text and 'code[1] == 0x19f3d0744ULL' in text
run([GIT,'init','-q'],feed);run([GIT,'apply','--check',patch],feed);run([GIT,'apply',patch],feed)
inst=module('instrument13',device/'scripts/ci/instrument_crash_snapshot.py')
exception=(feed/'osfmk/kern/exception.c').read_text(encoding='utf-8');exit_text=(feed/'bsd/kern/kern_exit.c').read_text(encoding='utf-8')
assert inst.exception_instrument(exception)==exception and inst.exit_instrument(exit_text)==exit_text
stage9=module('stage9',DEVICE/'scripts/ci/instrument_aslr_short_diagnostics.py')
include='#if defined(__arm64__)\n#include <arm/thread.h>\n#endif\n'
assert exception.replace(inst.CAPTURE,'').replace('\n'+include,'')==stage9.exception_instrument((OLD/'reference/osfmk/kern/exception.c').read_text(encoding='utf-8'))
assert exit_text.replace(inst.SUMMARY,'')==(OLD/'reference/bsd/kern/kern_exit.c').read_text(encoding='utf-8')
selected=[];targets={'bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c'}
for line in (DEVICE/'patches/xnu/device/series').read_text(encoding='utf-8').splitlines():
    entry=line.strip()
    if not entry or entry.startswith('#') or 'cdx-generated-aslr' in entry:continue
    text=(DEVICE/'patches/xnu/device'/entry).read_text(encoding='utf-8');starts=list(re.finditer(r'(?m)^(?:diff --git |--- a/)',text));chunks=[]
    for i,m in enumerate(starts):
        if not m.group().startswith('---'):continue
        end=starts[i+1].start() if i+1<len(starts) else len(text);chunk=text[m.start():end]
        if chunk.splitlines()[0][6:].split('\t')[0] in targets:chunks.append(chunk)
    if not chunks:continue
    p=fixture/('selected-'+str(len(selected))+'.patch');p.write_text(''.join(chunks),encoding='utf-8',newline='\n')
    run([GIT,'apply','--check',p],feed);run([GIT,'apply',p],feed);selected.append(entry)
report.update(passed=True,fixture=str(fixture),source_instrumentation_idempotent=True,installer_rejects_reapply=True,
    policy_removal_roundtrip=True,compatible_later_device_patches=selected,
    generated_patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest())
(HERE/'integration-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(HERE/'example-generated-source.patch').write_bytes(patch.read_bytes())
runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
for name in ['LegacyDisplayProbe.cpp','NativeLegacyDisplay.cpp']:(runtime/name).write_bytes((device/'stage10/stage10-runtime'/name).read_bytes())
print(json.dumps(report,indent=2))
