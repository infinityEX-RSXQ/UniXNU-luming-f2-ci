"""Portable fixtures are interface/model tests, not a full XNU build."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
LLVM=Path('D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin')
TMP=Path('D:/Codex/tmp/stage15-host');TMP.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(HERE));from make_core_patch15 import DAEMON,ipc,XNU
def run(args):
    p=subprocess.run(list(map(str,args)),cwd=HERE,capture_output=True,text=True)
    assert not p.returncode,p.stdout+'\n'+p.stderr
    return p.stdout
samples=(ROOT/'stage14-scanout-source-20261102/FrameSamples14.h').read_text(encoding='utf-8')
# The fixture uses the same pixel sampler actually inlined in the runtime.
assert samples[samples.index('struct Cdx14Samples'):].strip() in (HERE/'runtime/LegacyDisplayProbe.cpp').read_text(encoding='utf-8')
(TMP/'FrameSamples14.fixture.h').write_text(samples,encoding='utf-8')
(TMP/'daemon15.fixture.h').write_text(DAEMON,encoding='utf-8')
flags=['-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',TMP]
run([LLVM/'clang++.exe',*flags,HERE/'test_provider15.cpp','-o',TMP/'provider15.exe'])
output=run([TMP/'provider15.exe'])
arm=['-target','arm64-apple-ios17.0','-ffreestanding','-fno-builtin','-fno-exceptions','-fno-rtti','-mgeneral-regs-only']
run([LLVM/'clang++.exe',*flags,*arm,'-DCDX15_ABI_ONLY','-c',HERE/'test_provider15.cpp','-o',TMP/'provider15-arm64.o'])

prefix=r'''
#include <stdint.h>
#ifndef CDX15_ABI_ONLY
#include <assert.h>
#define CHECK(x) assert(x)
#else
#define CHECK(x) ((void)(x))
#endif
typedef int IOReturn;
struct IOExternalMethodArguments {};struct IOExternalMethodArgumentsOpaque {};
enum {kIPCLockNone,kIPCLockRead,kIPCLockWrite};
static int step,seenLock;static uint64_t nextToken=10;
extern "C" uint64_t cdx15_ipc_begin(void *,uint32_t selector){CHECK(step==0 && selector==42);step=1;return nextToken;}
extern "C" void cdx15_ipc_end(uint64_t token,uint32_t status){CHECK(step==4 && token==nextToken && status==17);step=5;}
struct IOUserClient {
    bool defaultLocking,defaultLockingSingleThreadExternalMethod,uc2022;
    void ipcEnter(int m){CHECK(step==1);step=2;seenLock=m;}
    void ipcExit(int m){CHECK(step==3 && m==seenLock);step=4;}
    virtual IOReturn externalMethod(uint32_t,IOExternalMethodArguments *){CHECK(step==2);step=3;return 17;}
    IOReturn callExternalMethod(uint32_t,IOExternalMethodArguments *);
};
struct IOUserClient2022: IOUserClient {
    using IOUserClient::externalMethod;
    IOReturn externalMethod(uint32_t,IOExternalMethodArgumentsOpaque *){CHECK(step==2);step=3;return 17;}
};
'''
source=ipc((XNU/'iokit/Kernel/IOUserClient.cpp').read_text(encoding='utf-8'))
start=source.index('IOReturn\nIOUserClient::callExternalMethod(');end=source.index('\n}\n',start)+3
suffix=r'''
#ifndef CDX15_ABI_ONLY
int main(){IOUserClient2022 c;
    for(unsigned mode=0;mode<8;++mode){c.defaultLocking=mode&1;c.defaultLockingSingleThreadExternalMethod=mode&2;c.uc2022=mode&4;
        step=0;CHECK(c.callExternalMethod(42,nullptr)==17 && step==5);
        CHECK(seenLock==((mode&1)?((mode&2)?kIPCLockWrite:kIPCLockRead):kIPCLockNone));}
}
#endif
'''
fixture=TMP/'ipc15.cpp';fixture.write_text(prefix+source[start:end]+suffix,encoding='utf-8')
run([LLVM/'clang++.exe',*flags,fixture,'-o',TMP/'ipc15.exe']);run([TMP/'ipc15.exe'])
run([LLVM/'clang++.exe',*flags,*arm,'-DCDX15_ABI_ONLY','-c',fixture,'-o',TMP/'ipc15-arm64.o'])
instruction_count=0
for name in ['provider15','ipc15']:
    assembly=run([LLVM/'llvm-objdump.exe','--macho','--disassemble',TMP/(name+'-arm64.o')])
    instructions=[]
    for line in assembly.splitlines():
        m=re.match(r'^\s*[0-9a-f]+:\t(?:[0-9a-f]{2} ){3}[0-9a-f]{2}\t(.+)$',line)
        if m:instructions.append(m.group(1))
    assert len(instructions)>80
    for ins in instructions:
        assert not ins.split()[0].startswith('f') and ins.split()[0] not in ('scvtf','ucvtf'),ins
        assert not re.search(r'\b[bdhqsv](?:[0-9]|[12][0-9]|3[01])(?:\.[0-9a-z]+)?\b',ins),ins
    instruction_count+=len(instructions)
    (TMP/(name+'-arm64.asm')).write_text(assembly,encoding='utf-8')
report=dict(passed=True,provider_model_and_adapter_tests=True,late_sample_detected_post_copy_change=True,
    lock_boundary_fixture=True,summary_boundaries=True,core_dispatch_and_return_preserved=True,
    arm64_interface_fixtures=True,gpr_only_instructions_checked=instruction_count,
    full_kernel_compiled=False,runtime_verified=False,scratch=str(TMP),
    fixture_sha256=hashlib.sha256((HERE/'test_provider15.cpp').read_bytes()).hexdigest())
(HERE/'host-check-output.txt').write_text(output+'Core IPC wrapper: 8 locking/dispatch combinations PASS\n',encoding='utf-8')
(HERE/'host-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
