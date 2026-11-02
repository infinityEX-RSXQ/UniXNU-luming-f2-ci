from pathlib import Path
import hashlib,json,re,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE));from install_stage17 import install,PINS,PATCH
from make_patch17 import make
sys.path.insert(0,str(ROOT/'stage15-trace-source-20261102'));from make_core_patch15 import DAEMON
TMP=Path('D:/Codex/tmp')/('stage17-check-'+str(time.time_ns()));device=TMP/'device'
oldcore,newcore=make()
for rel in PINS:
    source=ROOT/'stage16-vsync-source-20261102/runtime'/Path(rel).name if rel.endswith('.cpp') else (
        HERE/'series-stage16.txt' if rel.endswith('/series') else ROOT/'stage15-trace-source-20261102'/Path(rel).name)
    p=device/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(source.read_bytes())
assert not install(device)['applied'];result=install(device,True)
series=(device/'patches/xnu/device/series').read_text()
assert series.count(Path(PATCH).name)==1 and series.splitlines()[-1]==Path(PATCH).name
assert series.index('cdx15-observe.patch')<series.index('cdx17-observe.patch')
try:install(device,True)
except AssertionError:pass
else:raise AssertionError('reapplication accepted')
runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
for name in ['LegacyDisplayProbe.cpp','NativeLegacyDisplay.cpp']:(runtime/name).write_bytes((device/'stage10/stage10-runtime'/name).read_bytes())
probe=(runtime/'LegacyDisplayProbe.cpp').read_text()
(TMP/'Adapter17.fixture.h').write_text(probe[probe.index('static IOSimpleLock *cdx15_lock;'):])
for name in ['TraceModel15.h','Text15.h']:(TMP/name).write_bytes((ROOT/'stage15-trace-source-20261102'/name).read_bytes())
(TMP/'FrameSamples14.fixture.h').write_bytes((ROOT/'stage14-scanout-source-20261102/FrameSamples14.h').read_bytes())
(TMP/'daemon15.fixture.h').write_text(DAEMON)
test=(ROOT/'stage16-vsync-source-20261102/test_adapter16.cpp').read_text()
test=test.replace('#include "Adapter16.fixture.h"', '''struct IOExternalMethodArguments {const uint64_t *scalarInput;uint32_t scalarInputCount,scalarOutputCount;};
#include "Adapter17.fixture.h"''')
test=test.replace('static unsigned option(const char *){return 1;}',
    'static unsigned page17=2;static unsigned option(const char *s){return !strcmp(s,"luming-display-ipc-page")?page17:1;}')
extra=r'''
static void test17(){
    cdx15_state={};cdx17_state={};cdx16_epoch=0;cdx15_map_changed=0;
    static uint32_t pixels[96]={};static IOMemoryMap map={pixels,sizeof pixels,1};
    cdx15_mapping=&map;cdx15_width=cdx15_height=8;cdx15_stride=48;
    MockProc proc={58,"backboardd"};IOUserClient client={91},other={123};
    cdx15_client_open(&proc,0,&client,0);
    uint64_t values[3]={1,2,3};IOExternalMethodArguments args={values,3,1};
    cdx17_ipc_arguments(0,reinterpret_cast<IOExternalMethodArguments *>(1));
    auto a=cdx15_ipc_begin(&client,6);auto b=cdx15_ipc_begin(&client,72);
    cdx17_ipc_arguments(a,&args);args.scalarInputCount=2;cdx17_ipc_arguments(b,&args);
    assert(cdx17_state.rows[0].captured==3 && cdx17_state.rows[1].captured==2);
    assert(cdx17_state.rows[0].scalar[2]==3);
    cdx15_ipc_end(a,0x123);assert(cdx17_state.rows[0].errors==1 && cdx17_state.rows[0].status==0x123);
    auto port=cdx17_port_begin(&client,5,1,1);assert(port);
    assert(!cdx17_port_begin(&other,5,0,1));cdx17_port_end(port,1,0);
    assert(cdx17_state.rows[2].kind==2 && cdx17_state.rows[2].hasPort);
    // Notifications and method tokens are independently correlated, including same numeric token.
    assert(!cdx17::find(cdx17_state,a,0) && cdx17::find(cdx17_state,b,0));
    char out[660];page17=0;cdx15_snapshot(out,sizeof out,true);linesBounded(out);
    assert(strstr(out,"p58 s6 n1 d1 f1 r123") && strstr(out,"p58 Q5 n1 d1 f0 r0 b1"));
    assert(strstr(out,"pending=1 portRPC=1") && strlen(out)+39<700);
    page17=1;cdx15_snapshot(out,sizeof out,true);assert(strstr(out,"a=1/2/3") && strstr(out,"pending p58 k0 s72"));
    cdx15_ipc_end(b,0);
    // No borrowed argument pointer survives the call. Short/null buffers are bounded.
    auto c=cdx15_ipc_begin(&client,6);args={values,0,0};cdx17_ipc_arguments(c,&args);
    assert(!cdx17_state.rows[0].captured);args={nullptr,UINT32_MAX,0};cdx17_ipc_arguments(c,&args);
    assert(!cdx17_state.rows[0].captured);cdx15_ipc_end(c,0);
    cdx17::State full={};for(unsigned i=0;i<32;++i)assert(cdx17::begin(full,i+1,91,58,i,0,false,1));
    assert(!cdx17::begin(full,100,91,58,100,0,false,1) && full.drop==1);
    for(unsigned i=0;i<32;++i)cdx17::end(full,i+1,0,0,2);
    for(unsigned i=32;i<64;++i){assert(cdx17::begin(full,i+1,91,58,i,0,false,1));cdx17::end(full,i+1,0,0,2);}
    assert(!cdx17::begin(full,101,91,58,101,0,false,1) && full.used==64);
    full.rows[0].begun=UINT32_MAX;assert(cdx17::begin(full,200,91,58,0,0,false,1));assert(full.saturated);
    cdx17_state=full;page17=0;cdx15_snapshot(out,sizeof out,true);linesBounded(out);
    assert(strlen(out)+39<700 && strstr(out,"omit=") && strstr(out,"clip=1"));
    assert(!depth);page17=2;
}
'''
test=test.replace('int main(){time16Tests();',extra+'int main(){time16Tests();')
test=test.replace('pacing16Tests();puts(', 'pacing16Tests();test17();puts(')
assert 'test17();puts(' in test
(TMP/'adapter.cpp').write_text(test)
# Verify exact original wrapper semantics by stripping ONLY our observer statements.
stripped=newcore
start=stripped.index('extern "C" uint64_t cdx17_port_begin');end=stripped.index('/* Routine io_connect_set_notification_port */',start)
stripped=stripped[:start]+stripped[end:]
stripped='\n'.join(line for line in stripped.split('\n') if not any(x in line for x in
    ['uint64_t cdx17_token =','cdx17_port_end(cdx17_token,','cdx17_ipc_arguments(cdx15_token,']))
assert stripped==oldcore,'original dispatch/locking/return changed'
# Apply the actual generated patch, not just the generator transform.
core=TMP/'core/iokit/Kernel/IOUserClient.cpp';core.parent.mkdir(parents=True);core.write_text(oldcore,newline='\n')
GIT='C:/Program Files/Git/cmd/git.exe'
def run(args,cwd=HERE):
    r=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True);assert not r.returncode,r.stdout+'\n'+r.stderr;return r.stdout
run([GIT,'apply','--check',HERE/Path(PATCH).name],TMP/'core');run([GIT,'apply',HERE/Path(PATCH).name],TMP/'core')
assert core.read_text()==newcore
LLVM=Path('D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin')
flags=['-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',TMP]
run([LLVM/'clang++.exe',*flags,TMP/'adapter.cpp','-o',TMP/'adapter.exe']);output=run([TMP/'adapter.exe'])
arm=['-target','arm64-apple-ios17.0','-ffreestanding','-fno-builtin','-fno-exceptions','-fno-rtti','-mgeneral-regs-only','-DCDX15_ABI_ONLY']
run([LLVM/'clang++.exe',*flags,*arm,'-c',TMP/'adapter.cpp','-o',TMP/'adapter-arm64.o'])
assembly=run([LLVM/'llvm-objdump.exe','--macho','--disassemble',TMP/'adapter-arm64.o'])
ins=[m.group(1) for m in re.finditer(r'^\s*[0-9a-f]+:\t(?:[0-9a-f]{2} ){3}[0-9a-f]{2}\t(.+)$',assembly,re.M)]
assert len(ins)>100
for x in ins:
    assert not x.split()[0].startswith('f') and x.split()[0] not in ('scvtf','ucvtf'),x
    assert not re.search(r'\b[bdhqsv](?:[0-9]|[12][0-9]|3[01])(?:\.[0-9a-z]+)?\b',x),x
(HERE/'test_adapter17.cpp').write_text(test)
result.update(passed=True,host_adapter=True,prior_stage15_16_tests=True,patch_applies_after_stage15=True,
    original_dispatch_locks_returns_preserved=True,patch_series_registration_checked=True,
    arm64_interface_fixture=True,gpr_only_instructions_checked=len(ins),fixture=str(TMP))
(HERE/'validation.json').write_text(json.dumps(result,indent=2))
(HERE/'test-output.txt').write_text(output+'Stage17 known clients, port RPC, bounded inputs, pending, saturation: PASS\n')
print(json.dumps(result,indent=2))
