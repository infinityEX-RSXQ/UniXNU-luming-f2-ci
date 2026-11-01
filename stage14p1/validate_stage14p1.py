from pathlib import Path
import difflib,hashlib,importlib.util,json,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
BASE=ROOT/'builds/stage14-ci-work/fixture2/device'
ORIGINAL=ROOT/'builds/stage14-ci-work/repo'
XNU=ROOT/'builds/aslr-short-diag-20261101/xnu'
GIT=Path('C:/Program Files/Git/cmd/git.exe')
def run(args,cwd=None):
    p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
    assert p.returncode==0,p.stdout+'\n'+p.stderr;return p.stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
fixture=Path('D:/Codex/tmp')/('stage14p1-check-'+str(time.time_ns()));feed=fixture/'feed';device=fixture/'device'
console=feed/'osfmk/console/video_console.c';console.parent.mkdir(parents=True)
console.write_bytes((XNU/'osfmk/console/video_console.c').read_bytes())
run([GIT,'init','-q'],feed)
for name in ['zzzzz-fix-darwinboot-physical-framebuffer.patch','zzzzzzzzzzzzzzzzzzzzzz-cdx14-observation.patch']:
    path=ORIGINAL/'patches/xnu/device'/name
    if not path.exists():path=BASE/'patches/xnu/device'/name
    text=path.read_text(encoding='utf-8')
    if name.startswith('zzzzzzzz'):
        text=text[:text.index('--- a/bsd/kern/kern_exit.c')]
    p=fixture/name;p.write_text(text,encoding='utf-8',newline='\n')
    run([GIT,'apply','--check',p],feed);run([GIT,'apply',p],feed)
before=console.read_text(encoding='utf-8');after=before+'\n'+(HERE/'core_reclaim.c.inc').read_text(encoding='utf-8')
patch=HERE/'zzzzzzzzzzzzzzzzzzzzzzz-cdx14p1-console-reclaim.patch'
patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
    fromfile='a/osfmk/console/video_console.c',tofile='b/osfmk/console/video_console.c',n=3)),encoding='utf-8',newline='\n')
run([GIT,'apply','--check',patch],feed);run([GIT,'apply',patch],feed)
assert console.read_text(encoding='utf-8')==after
sys.path.insert(0,str(HERE));from install_stage14p1 import install
for rel in ['stage10/stage10-runtime/LegacyDisplayProbe.cpp','stage10/stage10-runtime/NativeLegacyDisplay.cpp',
    'patches/xnu/device/zzzzzzzzzzzzzzzzzzzzzz-cdx14-observation.patch','patches/xnu/device/series']:
    p=device/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((BASE/rel).read_bytes())
assert not install(device,False)['applied'];r=install(device,True)
try:install(device,True)
except AssertionError:pass
else:raise AssertionError('Double installation accepted')
runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
for name in ['LegacyDisplayProbe.cpp','NativeLegacyDisplay.cpp']:(runtime/name).write_bytes((device/'stage10/stage10-runtime'/name).read_bytes())
probe=(runtime/'LegacyDisplayProbe.cpp').read_text(encoding='utf-8')
assert probe.index('bool quiet=cdx14p1_quiesce();')<probe.index('unsigned reclaimed=quiet?cdx14p1_console_reclaim():0;')<probe.index('panic("CDX14.1')
assert probe.count('thread_call_allocate(cdx14_snapshot_callback')==1
assert 'cdx14_frame_end(true);' in (runtime/'NativeLegacyDisplay.cpp').read_text(encoding='utf-8')
r.update(passed=True,fixture=str(fixture),core_patch_applied_after_stage14=True,base_ci_run=41359974470,
    base_commit='d47f17cf5e640fce1c382bc4a840c641f407a715',full_kernel_compiled=False,runtime_verified=False)
(HERE/'integration-validation.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(json.dumps(r,indent=2))
