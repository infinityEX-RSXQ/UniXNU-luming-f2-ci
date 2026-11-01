from pathlib import Path
import json,subprocess,sys
HERE=Path(__file__).resolve().parent;TMP=Path('D:/Codex/tmp/stage14p1-host');TMP.mkdir(exist_ok=True)
LLVM=Path('D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin')
def run(args):
    p=subprocess.run(list(map(str,args)),cwd=HERE,capture_output=True,text=True)
    assert p.returncode==0,p.stdout+'\n'+p.stderr;return p.stdout
run([LLVM/'clang++.exe','-std=c++17','-Wall','-Wextra','-Werror',HERE/'test_quiesce.cpp','-o',TMP/'test-quiesce.exe'])
log=run([TMP/'test-quiesce.exe'])
prefix='''#include <stddef.h>
#ifndef ABI_ONLY
#include <assert.h>
#include <stdio.h>
#endif
static int gc_initialized=1,gc_enabled,disableConsoleOutput=1;
static unsigned cdx14_vt_owned=1,lockHeld,ops[3],opCount;
#define kPEReleaseScreen 5
#define kPETextMode 2
#define kPEAcquireScreen 4
#define VCPUTC_LOCK_LOCK() (++lockHeld)
#define VCPUTC_LOCK_UNLOCK() (--lockHeld)
static void initialize_screen(void *info,unsigned op){
    (void)info;
    if(opCount<3)ops[opCount++]=op;
    if(op==kPEAcquireScreen){gc_enabled=1;disableConsoleOutput=0;}
}
'''
test='''
#ifndef ABI_ONLY
int main(void){
    gc_initialized=0;assert(cdx14p1_console_reclaim()==0 && cdx14_vt_owned==1 && opCount==0);
    gc_initialized=1;assert(cdx14p1_console_reclaim()==1);
    assert(!lockHeld && !cdx14_vt_owned && gc_enabled && !disableConsoleOutput);
    assert(opCount==3 && ops[0]==5 && ops[1]==2 && ops[2]==4);
    puts("Stage14.1 reclaim: uninitialized guard, latch clear, release/text/acquire order PASS");
}
#endif
'''
core=TMP/'core-reclaim-fixture.c';core.write_text(prefix+(HERE/'core_reclaim.c.inc').read_text(encoding='utf-8')+test,encoding='utf-8')
run([LLVM/'clang.exe','-std=c11','-Wall','-Wextra','-Werror',core,'-o',TMP/'test-reclaim.exe'])
log+=run([TMP/'test-reclaim.exe'])
run([LLVM/'clang.exe','-target','arm64-apple-ios17.0','-ffreestanding','-mgeneral-regs-only','-DABI_ONLY',
    '-std=c11','-Wall','-Wextra','-Werror','-c',core,'-o',TMP/'reclaim-arm64.o'])
# Compile the real updated provider helper/callback section, with interface declarations only.
base=HERE.parent/'stage14-scanout-source-20261102/abi_provider14.cpp'
abi=base.read_text(encoding='utf-8').split('#include "FrameSamples14.h"')[0]
abi+='extern void IOSleep(unsigned);\n'
probe=(HERE/'runtime/LegacyDisplayProbe.cpp').read_text(encoding='utf-8')
start=probe.index('// Integer-only, bounded samples')
# Strip the old inlined include guard markers by taking the entire guarded section: no #pragma once is emitted.
frame_start=probe.rfind('// SPDX-License-Identifier:',0,start)
abi+=probe[frame_start:]
abi_file=TMP/'provider-interface.cpp';abi_file.write_text(abi,encoding='utf-8')
run([LLVM/'clang++.exe','-target','arm64-apple-ios17.0','-ffreestanding','-fno-exceptions','-fno-rtti',
    '-mgeneral-regs-only','-std=c++17','-Wall','-Wextra','-Werror','-c',abi_file,'-o',TMP/'provider-arm64.o'])
(HERE/'host-check-output.txt').write_text(log,encoding='utf-8')
(HERE/'host-validation.json').write_text(json.dumps(dict(quiesce_test=True,reclaim_test=True,
    arm64_provider_fixture=True,arm64_reclaim_fixture=True,full_kernel_compiled=False,runtime_verified=False),indent=2),encoding='utf-8')
print(log)
