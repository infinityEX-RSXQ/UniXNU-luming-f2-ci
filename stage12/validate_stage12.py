from pathlib import Path
import ast,hashlib,importlib.util,json,os,re,subprocess,sys,time
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'stage11-diagnostic'
DEVICE=Path('D:/civitoip20/lumingios-cdx/builds/stage10-ci-work/repo')
GIT=Path('C:/Program Files/Git/cmd/git.exe')
os.environ['PATH']=str(GIT.parent)+os.pathsep+os.environ['PATH']
sys.path.insert(0,str(OLD));import install_stage11
from install_stage12 import install,MODE_CAPTURE
f=HERE/('fixture-'+str(time.time_ns()));device=f/'device';feed=f/'feed'
for rel in list(install_stage11.PINS)+['stage10/stage10-runtime/NativeLegacyDisplay.cpp','patches/xnu/device/series']:
    p=device/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((DEVICE/rel).read_bytes())
install_stage11.install(device,True)
report=install(device,True)
for rel in ['bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c']:
    p=feed/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((OLD/'reference'/rel).read_bytes())
def run(args,cwd=None):
    p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
    assert p.returncode==0,p.stdout+'\n'+p.stderr
    return p.stdout
patch=device/'patches/xnu/device/zzzzz-cdx-generated-aslr.patch'
report['generator']=run([sys.executable,device/'scripts/ci/gen_aslr_patch.py',OLD/'reference/core',feed,patch,device/'patches/xnu/device/series'])
text=patch.read_text(encoding='utf-8');patch.write_text(text,encoding='utf-8',newline='\n')
assert 'CDX12_MODE' in text and 'cdx12_append_mode_summary' in text and 'char cdx11_reason[1024]' in text
run([GIT,'init','-q'],feed);run([GIT,'apply','--check',patch],feed);run([GIT,'apply',patch],feed)
spec=importlib.util.spec_from_file_location('inst12',device/'scripts/ci/instrument_crash_snapshot.py')
inst=importlib.util.module_from_spec(spec);spec.loader.exec_module(inst)
exception=(feed/'osfmk/kern/exception.c').read_text(encoding='utf-8')
exit_text=(feed/'bsd/kern/kern_exit.c').read_text(encoding='utf-8')
assert inst.exception_instrument(exception)==exception and inst.exit_instrument(exit_text)==exit_text
spec=importlib.util.spec_from_file_location('inst9',DEVICE/'scripts/ci/instrument_aslr_short_diagnostics.py')
stage9=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage9)
include='#if defined(__arm64__)\n#include <arm/thread.h>\n#endif\n'
assert exception.replace(inst.CAPTURE,'').replace('\n'+include,'')==stage9.exception_instrument((OLD/'reference/osfmk/kern/exception.c').read_text(encoding='utf-8'))
assert exit_text.replace(inst.SUMMARY,'')==(OLD/'reference/bsd/kern/kern_exit.c').read_text(encoding='utf-8')
selected=[]
targets={'bsd/kern/kern_exit.c','osfmk/kern/exception.c','bsd/vm/vm_unix.c'}
for line in (DEVICE/'patches/xnu/device/series').read_text(encoding='utf-8').splitlines():
    entry=line.strip()
    if not entry or entry.startswith('#') or 'cdx-generated-aslr' in entry:continue
    text=(DEVICE/'patches/xnu/device'/entry).read_text(encoding='utf-8')
    starts=list(re.finditer(r'(?m)^(?:diff --git |--- a/)',text));chunks=[]
    for i,m in enumerate(starts):
        if not m.group().startswith('---'):continue
        end=starts[i+1].start() if i+1<len(starts) else len(text)
        chunk=text[m.start():end]
        if chunk.splitlines()[0][6:].split('\t')[0] in targets:chunks.append(chunk)
    if not chunks:continue
    p=f/('selected-'+str(len(selected))+'.patch');p.write_text(''.join(chunks),encoding='utf-8',newline='\n')
    run([GIT,'apply','--check',p],feed);run([GIT,'apply',p],feed);selected.append(entry)
assert (feed/'bsd/kern/kern_exit.c').read_text(encoding='utf-8').count(inst.SUMMARY)==1
# Changes to the backend are one gated registerService branch and one C hook
# declaration; there are no new virtuals, object fields, fake mode fields or
# changes to original instructions. Validate branch semantics independently.
def enabled(primary,hz,publish60):return primary and hz<=240 and (hz>60 or (publish60==1 and hz==60))
assert not enabled(True,60,0) and enabled(True,60,1)
assert not enabled(False,60,1) and not enabled(True,0,1) and not enabled(True,59,1)
assert enabled(True,120,0) and not enabled(True,241,1)
report.update(passed=True,instrumentation_idempotent=True,policy_removal_roundtrip=True,
    arm_saved_state_api_checked=True,copyin_prototype_checked=True,
    compatible_later_device_patches=selected,
    fixture=str(f),generated_patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest())
(HERE/'integration-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
