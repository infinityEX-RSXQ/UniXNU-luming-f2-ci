from pathlib import Path
import hashlib,json,re,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'stage15-trace-source-20261102'
sys.path.insert(0,str(HERE));from install_stage16 import install,PINS
sys.path.insert(0,str(OLD));from make_core_patch15 import DAEMON
TMP=Path('D:/Codex/tmp')/('stage16-check-'+str(time.time_ns()));device=TMP/'device'
for rel in PINS:
    source=OLD/'runtime'/Path(rel).name if rel.endswith('.cpp') else OLD/Path(rel).name
    target=device/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
assert not install(device)['applied'];report=install(device,True)
try:install(device,True)
except AssertionError:pass
else:raise AssertionError('double apply accepted')
runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
for name in ['LegacyDisplayProbe.cpp','NativeLegacyDisplay.cpp']:(runtime/name).write_bytes((device/'stage10/stage10-runtime'/name).read_bytes())
probe=(runtime/'LegacyDisplayProbe.cpp').read_text(encoding='utf-8');backend=(runtime/'NativeLegacyDisplay.cpp').read_text(encoding='utf-8')
assert backend.count('bool wanted=vsyncWanted();')==1
assert 'newUserClient(task_t task,void *security,UInt32 type,IOUserClient **client)' in backend
assert probe.index('cdx15_snapshot(reason,sizeof(reason),quiet);')<probe.index('unsigned reclaimed=quiet?cdx14p1_console_reclaim():0;')
adapter=probe[probe.index('static IOSimpleLock *cdx15_lock;'):]
(TMP/'Adapter16.fixture.h').write_text(adapter,encoding='utf-8')
for file in ['TraceModel15.h','Text15.h']:(TMP/file).write_bytes((OLD/file).read_bytes())
(TMP/'FrameSamples14.fixture.h').write_bytes((ROOT/'stage14-scanout-source-20261102/FrameSamples14.h').read_bytes())
(TMP/'daemon15.fixture.h').write_text(DAEMON,encoding='utf-8')
test=(OLD/'test_provider15.cpp').read_text(encoding='utf-8').replace('#include "ProviderTrace15.h"','#include "Adapter16.fixture.h"')
extra=r'''
static void time16Tests(){
    bool clipped=false;cdx16_epoch=1234000000;
    assert(cdx15_ms(0,clipped)==0 && !clipped);
    assert(cdx15_ms(cdx16_epoch+1234,clipped)==1234 && !clipped);
    assert(cdx15_ms(cdx16_epoch-1,clipped)==0 && clipped);cdx16_epoch=0;
}
static void pacing16Tests(){
    cdx16_vsync_observed(0,6,6,60);cdx16_vsync_observed(1,3,39,60);
    assert(cdx16_vsync.startReason==6 && cdx16_vsync.armReason==3);
    assert(cdx16_vsync.startAttempts==1 && cdx16_vsync.armAttempts==1);
    char out[660];cdx15_snapshot(out,sizeof out,true);linesBounded(out);assert(strstr(out,"vst=6 sa=1 ar=3 aa=1"));
}
'''
test=test.replace('int main(){textTests();modelTests();adapterTests();',extra+'int main(){time16Tests();textTests();modelTests();adapterTests();pacing16Tests();')
(TMP/'adapter.cpp').write_text(test,encoding='utf-8')

prefix=r'''
#include <stdint.h>
#ifndef CDX15_ABI_ONLY
#include <assert.h>
#define CHECK(x) assert(x)
#else
#define CHECK(x) ((void)(x))
#endif
typedef int IOReturn;static const int kIOReturnSuccess=0;
struct OSObject {};
static unsigned hzArg=60,fail,reason[2],flagsSeen[2],attempt[2],allocs,releases,wakes,wantReads;
static bool wants;
static void PE_parse_boot_argn(const char *,void *out,unsigned){*(unsigned *)out=hzArg;}
static uint64_t mach_absolute_time(){return 1000;}
static void nanoseconds_to_absolutetime(uint64_t n,uint64_t *out){*out=n;}
static void native_legacy_vsync_observed(unsigned,unsigned){}
static void cdx16_vsync_observed(unsigned phase,unsigned why,unsigned flags,unsigned){reason[phase]=why;flagsSeen[phase]=flags;++attempt[phase];}
struct IOTimerEventSource {
    static IOTimerEventSource *timerEventSource(OSObject *,void (*)(OSObject *,IOTimerEventSource *)){
        ++allocs;static IOTimerEventSource t;return fail==7?nullptr:&t;}
    void wakeAtTime(uint64_t){++wakes;}void release(){++releases;}
};
struct IOWorkLoop {
    int addEventSource(IOTimerEventSource *){return fail==8?-1:0;}
    int runAction(IOReturn (*f)(OSObject *,void *,void *,void *,void *),OSObject *o){return f(o,nullptr,nullptr,nullptr,nullptr);}
};
class NativeLegacyDisplay:public OSObject {public:
    IOTimerEventSource *vsyncTimer=nullptr;bool primary=true,bootMapping=true,vsyncArmed=false;
    uint64_t vsyncNext=0,vsyncInterval=0;unsigned vsyncHz=0;
    bool vsyncWanted(){++wantReads;return wants;}
    IOWorkLoop *getWorkLoop(){static IOWorkLoop loop;return fail==6?nullptr:&loop;}
    static void vsyncFired(OSObject *,IOTimerEventSource *){}
'''
arm=backend[backend.index('    void armVsync() {'):backend.index('    static void vsyncFired')]
start=backend[backend.index('    void startVsync() {'):backend.index('    void stopVsync()')]
suffix=r'''
};
#ifndef CDX15_ABI_ONLY
static void reset(){hzArg=60;fail=0;reason[0]=reason[1]=flagsSeen[0]=flagsSeen[1]=attempt[0]=attempt[1]=allocs=releases=wakes=wantReads=0;wants=false;}
int main(){
    for(unsigned i=1;i<=9;++i){reset();NativeLegacyDisplay d;IOTimerEventSource existing;
        if(i==1)hzArg=0;if(i==2)hzArg=241;if(i==3)d.primary=false;if(i==4)d.bootMapping=false;
        if(i==5)d.vsyncTimer=&existing;if(i>=6 && i<=8)fail=i;
        d.startVsync();CHECK(reason[0]==i && attempt[0]==1);
        if(i<=6)CHECK(!allocs);if(i==7)CHECK(allocs==1 && !releases);if(i==8)CHECK(releases==1);
        if(i==9){CHECK(d.vsyncTimer && d.vsyncHz==60 && d.vsyncInterval==16666666 && !wakes);
            CHECK(reason[1]==3 && wantReads==1 && (flagsSeen[1]&32));
            wants=true;d.armVsync();CHECK(reason[1]==4 && wakes==1 && d.vsyncArmed && wantReads==2);
            d.armVsync();CHECK(reason[1]==2 && wakes==1 && wantReads==2);}
    }
    reset();NativeLegacyDisplay absent;absent.armVsync();CHECK(reason[1]==1 && !wantReads && !wakes);
}
#else
extern "C" unsigned pacing_fixture(NativeLegacyDisplay *d){d->startVsync();d->armVsync();return allocs+releases+wakes+wantReads+reason[0]+flagsSeen[0]+attempt[0];}
#endif
'''
(TMP/'pacing.cpp').write_text(prefix+arm+start+suffix,encoding='utf-8')
LLVM=Path('D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin')
def run(args):
    p=subprocess.run(list(map(str,args)),cwd=HERE,capture_output=True,text=True);assert not p.returncode,p.stdout+'\n'+p.stderr;return p.stdout
host_flags=['-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',TMP]
arm_flags=['-target','arm64-apple-ios17.0','-ffreestanding','-fno-builtin','-fno-exceptions','-fno-rtti','-mgeneral-regs-only','-DCDX15_ABI_ONLY']
output=''
instructions_checked=0
for name in ['adapter','pacing']:
    run([LLVM/'clang++.exe',*host_flags,TMP/(name+'.cpp'),'-o',TMP/(name+'.exe')]);output+=run([TMP/(name+'.exe')])
    run([LLVM/'clang++.exe',*host_flags,*arm_flags,'-c',TMP/(name+'.cpp'),'-o',TMP/(name+'-arm64.o')])
    assembly=run([LLVM/'llvm-objdump.exe','--macho','--disassemble',TMP/(name+'-arm64.o')])
    instructions=[]
    for line in assembly.splitlines():
        m=re.match(r'^\s*[0-9a-f]+:\t(?:[0-9a-f]{2} ){3}[0-9a-f]{2}\t(.+)$',line)
        if m:instructions.append(m.group(1))
    assert len(instructions)>80
    for ins in instructions:
        assert not ins.split()[0].startswith('f') and ins.split()[0] not in ('scvtf','ucvtf'),ins
        assert not re.search(r'\b[bdhqsv](?:[0-9]|[12][0-9]|3[01])(?:\.[0-9a-z]+)?\b',ins),ins
    instructions_checked+=len(instructions)
    (HERE/('test_'+name+'16.cpp')).write_bytes((TMP/(name+'.cpp')).read_bytes())
report.update(passed=True,host_adapter=True,relative_time_fixed=True,pacing_return_paths_tested=9,
    subscriber_read_once=True,arm64_interface_fixtures=True,gpr_only_instructions_checked=instructions_checked,fixture=str(TMP))
(HERE/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(HERE/'test-output.txt').write_text(output+'Stage16 start/arm policy and single subscription read: PASS\n',encoding='utf-8')
print(json.dumps(report,indent=2))
