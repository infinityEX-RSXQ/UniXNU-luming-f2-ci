from pathlib import Path
import json,re,subprocess,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from make_core_patch import CONSOLE_DECL,DAEMON_DECL,EXCEPTION_DECL
CLANG=Path('D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin')
TMP=Path('D:/Codex/tmp/stage14-host');TMP.mkdir(exist_ok=True)
def run(args):
    p=subprocess.run(list(map(str,args)),cwd=HERE,capture_output=True,text=True)
    assert p.returncode==0,p.stdout+'\n'+p.stderr;return p.stdout
prefix=r'''
#include <stdint.h>
#include <stddef.h>
#ifndef CDX14_ABI_ONLY
#include <stdio.h>
#include <string.h>
#include <assert.h>
#else
int printf(const char *,...);int snprintf(char *,size_t,const char *,...);int strcmp(const char *,const char *);
#endif
typedef int boolean_t;
#define TRUE 1
#define FALSE 0
static unsigned mock_panic,mock_serial,mock_locked;
static boolean_t gc_enabled=TRUE;
static int disableConsoleOutput;
static unsigned panic_active(void){return mock_panic;}
static int console_is_serial(void){return mock_serial;}
#define VCPUTC_LOCK_LOCK() (++mock_locked)
#define VCPUTC_LOCK_UNLOCK() (--mock_locked)
struct reason {unsigned osr_namespace;uint64_t osr_code;};
struct proc {char p_comm[32];unsigned pid;struct reason *p_exit_reason;};
typedef struct proc *proc_t;
#define PROC_HAS_EXITREASON(p) ((p)->p_exit_reason!=NULL)
static unsigned proc_getpid(proc_t p){return p->pid;}
'''
test=r'''
#ifndef CDX14_ABI_ONLY
int main(void){
    unsigned out[5];assert(!cdx14_vt_should_block());
    cdx14_console_commit();cdx14_console_snapshot(out);
    assert(out[0]==1 && out[1]==0 && out[2]==1 && !mock_locked);
    assert(cdx14_vt_should_block());mock_panic=1;assert(!cdx14_vt_should_block());mock_panic=0;
    mock_serial=1;disableConsoleOutput=0;cdx14_console_commit();assert(!disableConsoleOutput);
    struct reason why={2,5};struct proc p={"liveactivitiesd",120,&why};
    for(unsigned i=0;i<20;++i){cdx14_observe_exit(&p,5);cdx14_daemon_exception(p.p_comm,6,1,0x1234);}
    assert(cdx14_daemons[3].count==20 && cdx14_exceptions[3].count==20);
    struct proc other={"unrelated",77,NULL};cdx14_observe_exit(&other,0);cdx14_daemon_exception(other.p_comm,1,2,3);
    assert(cdx14_daemons[3].count==20);
    char full[512];cdx14_daemon_summary(full,sizeof full);assert(strstr(full,"ns=2 code=5"));
    cdx14_exception_summary(full,sizeof full);assert(strstr(full,"c1=1234"));
    for(unsigned size=1;size<512;++size){
        char b[514];memset(b,'X',sizeof b);
        size_t n=cdx14_daemon_summary(b,size);assert(n<size && b[n]==0 && b[size]=='X');
        memset(b,'X',sizeof b);n=cdx14_exception_summary(b,size);assert(n<size && b[n]==0 && b[size]=='X');
    }
    puts("Stage14 core: locked ownership, serial preservation, panic bypass, daemon records/bounds PASS");
}
#else
void cdx14_fixture_calls(proc_t p){(void)cdx14_vt_should_block();cdx14_observe_exit(p,0);}
#endif
'''
source=TMP/'core-policy-fixture.c';source.write_text(prefix+CONSOLE_DECL+DAEMON_DECL+EXCEPTION_DECL+test,encoding='utf-8')
run([CLANG/'clang.exe','-std=c11','-Wall','-Wextra','-Werror',source,'-o',TMP/'core-policy-test.exe'])
core_output=run([TMP/'core-policy-test.exe']);assert core_output.count('CDX14 exit ')==4 and core_output.count('CDX14 exc ')==4
run([CLANG/'clang++.exe','-std=c++17','-Wall','-Wextra','-Werror',HERE/'test_provider14.cpp','-o',TMP/'provider-test.exe'])
provider_output=run([TMP/'provider-test.exe'])
run([CLANG/'clang.exe','-target','arm64-apple-ios17.0','-DCDX14_ABI_ONLY','-Wno-unused-function',
    '-ffreestanding','-fno-builtin','-mgeneral-regs-only','-std=c11','-Wall','-Wextra','-Werror','-c',source,'-o',TMP/'core-policy-arm64.o'])
disasm=run([CLANG/'llvm-objdump.exe','--macho','--disassemble',TMP/'core-policy-arm64.o'])
assert '_cdx14_console_commit:' in disasm
(HERE/'core-policy-arm64.asm').write_text(disasm,encoding='utf-8')
run([CLANG/'clang++.exe','-target','arm64-apple-ios17.0','-ffreestanding','-fno-exceptions','-fno-rtti',
    '-mgeneral-regs-only','-std=c++17','-Wall','-Wextra','-Werror','-c',HERE/'abi_provider14.cpp','-o',TMP/'provider-arm64.o'])
provider_asm=run([CLANG/'llvm-objdump.exe','--macho','--disassemble',TMP/'provider-arm64.o'])
for assembly in [disasm,provider_asm]:
    instructions=[]
    for line in assembly.splitlines():
        m=re.match(r'^\s*[0-9a-f]+:\t(?:[0-9a-f]{2} ){3}[0-9a-f]{2}\t(.+)$',line)
        if m:instructions.append(m.group(1))
    assert len(instructions)>100
    for ins in instructions:
        assert not ins.split()[0].startswith('f') and ins.split()[0] not in ('scvtf','ucvtf')
        assert not re.search(r'\b[bdhqsv](?:[0-9]|[12][0-9]|3[01])(?:\.[0-9a-z]+)?\b',ins)
(HERE/'provider-arm64.asm').write_text(provider_asm,encoding='utf-8')
(HERE/'host-check-output.txt').write_text(core_output+provider_output,encoding='utf-8')
report=dict(core_policy_tests=True,provider_tests=True,daemon_logs_bounded=True,
    arm64_core_interface_fixture_compiled=True,arm64_provider_interface_fixture_compiled=True,
    no_fp_simd_in_fixtures=True,full_kernel_compiled=False,runtime_verified=False)
(HERE/'host-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(core_output+provider_output)
