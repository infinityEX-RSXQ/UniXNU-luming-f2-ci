"""Host checks, source pins and ARM64 interface checks; not a full Mac build."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE));from install_stage19 import install,P,B,G,PINS
TMP=Path('D:/Codex/tmp')/('stage19-check-'+str(time.time_ns()));device=TMP/'device'
LLVM=Path('D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin')
def sha(b):return hashlib.sha256(b).hexdigest()
def run(args):
    p=subprocess.run(list(map(str,args)),cwd=TMP,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
    return p.stdout
TMP.mkdir(parents=True)
for rel in PINS:
    source=ROOT/'stage18-wait-source-20261102/runtime'/Path(rel).name
    target=device/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes().replace(b'\r\n',b'\n'))
assert not install(device)['applied'];result=install(device,True)
try:install(device,True)
except AssertionError:pass
else:raise AssertionError('reapplication accepted')
runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
for rel in PINS:(runtime/Path(rel).name).write_bytes((device/rel).read_bytes())
assert result['before'][B]==result['after'][B] and result['before'][G]==result['after'][G]
probe=(device/P).read_text()
assert probe.index('if(cdx19_capture_next())')<probe.index('bool quiet19=cdx14p1_quiesce();char stackReason[820]')
adapter=(HERE/'Adapter19.h').read_text()
assert (HERE/'Format21.h').read_text() in adapter
assert (HERE/'Format22.h').read_text() in adapter
assert 'IOSimpleLockLock' not in adapter and 'runAction' not in adapter
for forbidden in ('task_suspend(', 'thread_suspend(', 'thread_getstatus(', 'machine_thread_get_state('):assert forbidden not in adapter
assert adapter.count('stack_snapshot_from_kernel(')==2 # declaration plus one runtime call site
assert adapter.index('stack_snapshot_from_kernel(-1,')<adapter.index('cdx19::parse(buffer,')
assert 'const auto *self=' not in (HERE/'Model19.h').read_text()
(HERE/'Text15.fixture.h').write_bytes((ROOT/'stage15-trace-source-20261102/Text15.h').read_bytes())
flags=['-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',HERE]
outputs=[]
for name in ('model','adapter'):
    run([LLVM/'clang++.exe',*flags,HERE/('test_'+name+'19.cpp'),'-o',TMP/(name+'.exe')])
    outputs.append(run([TMP/(name+'.exe')]))
run([LLVM/'clang++.exe',*flags,HERE/'test_relations21.cpp','-o',TMP/'relations21.exe'])
outputs.append(run([TMP/'relations21.exe']))
# Recompile every prior adapter test with the actual Stage19 materialized tail.
old=ROOT/'stage18-wait-source-20261102'
prior=json.loads((old/'validation.json').read_text())
for name in ('TraceModel15.h','Text15.h','FrameSamples14.fixture.h','daemon15.fixture.h'):
    (TMP/name).write_bytes((Path(prior['fixture'])/name).read_bytes())
(TMP/'Adapter19.fixture.h').write_text(probe[probe.index('static IOSimpleLock *cdx15_lock;'):])
test=(old/'test_adapter18.cpp').read_text().replace('Adapter18.fixture.h','Adapter19.fixture.h')
test=test.replace('static unsigned option(const char *s){return ', 'static unsigned option(const char *s){return !strcmp(s,"luming-display-stackshot")?0:')
test=test.replace('struct Active {void setProperty(const char *,OSData *){unlocked();}};',
                  'struct Active {bool setProperty(const char *,OSData *){unlocked();return true;}};')
newmock='''
typedef int kern_return_t;
extern "C" void *memset(void *,int,size_t);
static void bzero(void *p,size_t n){memset(p,0,n);}
static void *IOMalloc(size_t){unlocked();return nullptr;}
static void IOFree(void *,size_t){unlocked();}
static bool ml_at_interrupt_context(){unlocked();return false;}
static bool ml_get_interrupts_enabled(){unlocked();return true;}
extern "C" kern_return_t stack_snapshot_from_kernel(int,void *,uint32_t,uint64_t,uint64_t,uint32_t,unsigned *){unlocked();return 6;}
'''
test=test.replace('#include "TraceModel15.h"',newmock+'\n#include "TraceModel15.h"')
(HERE/'test_prior19.cpp').write_text(test);(TMP/'prior.cpp').write_text(test)
run([LLVM/'clang++.exe',*flags,'-I',TMP,TMP/'prior.cpp','-o',TMP/'prior.exe']);outputs.append(run([TMP/'prior.exe']))
arm=['-target','arm64-apple-ios17.0','-ffreestanding','-fno-builtin','-fno-exceptions','-fno-rtti','-mgeneral-regs-only','-fapple-kext','-mkernel','-DCDX15_ABI_ONLY']
run([LLVM/'clang++.exe',*flags,'-I',TMP,*arm,'-fstack-usage','-c',TMP/'prior.cpp','-o',TMP/'adapter-arm64.o'])
assembly=run([LLVM/'llvm-objdump.exe','--macho','--disassemble',TMP/'adapter-arm64.o'])
stackUsage={}
for row in (TMP/'adapter-arm64.su').read_text().splitlines():
    fn,amount,mode=row.split('\t');stackUsage[fn]=int(amount)
assert max(stackUsage.values())<=4096,('kernel diagnostic stack frame too large',stackUsage)
instructions=[m.group(1) for m in re.finditer(r'^\s*[0-9a-f]+:\t(?:[0-9a-f]{2} ){3}[0-9a-f]{2}\t(.+)$',assembly,re.M)]
assert len(instructions)>1000
for ins in instructions:
    assert not ins.split()[0].startswith('f') and ins.split()[0] not in ('scvtf','ucvtf'),ins
    assert not re.search(r'\b[bdhqsv](?:[0-9]|[12][0-9]|3[01])(?:\.[0-9a-z]+)?\b',ins),ins
# Pin the layout definitions and kernel-consumer implementation, not private
# task/thread offsets. CI must verify these before compiling Stage19.
source=ROOT/'builds/aslr-short-diag-20261101/xnu'
sources=['bsd/kern/sys_ulock.c','osfmk/ipc/ipc_port.c','osfmk/kern/lock_mtx.c','osfmk/kern/locks.c','osfmk/kern/block_hint.h','osfmk/kern/kcdata.h','osfmk/kern/debug.h','osfmk/kern/kern_stackshot.c','osfmk/kdp/ml/arm/kdp_machdep.c']
sourcePins={p:sha((source/p).read_bytes().replace(b'\r\n',b'\n')) for p in sources}
(HERE/'xnu-source-pins.json').write_text(json.dumps(sourcePins,indent=2))
# Confirm this accepted source-built kernel really contains the consumer.
kernel=ROOT/'builds/stage18-wait-41544084405/kernel.macho'
assert sha(kernel.read_bytes())=='8ba11aab6079d5adf32bad5f0d10cf97ec63b1c3b884ff1fdd4ca675cdec8586'
nm=run([LLVM/'llvm-nm.exe','--defined-only',kernel])
assert re.search(r'\b_stack_snapshot_from_kernel$',nm,re.M)
result.update(host_checks_passed=True,stage22_typed_chain_tests=True,stage21_owner_join_tests=True,stage21_batch_boundaries_tested=True,prior_stage15_16_17_18_tests=True,
    generated_abi_sha256='8c996ed2c36eb973fc4f4a4ed644498710dacec6120ae1e4f524ab5653120e8a',
    kcdata_malformed_and_truncation_tests=True,default_off_two_sample_and_failure_tests=True,
    source_api_present_in_stage18=True,source_kernel_pins=sourcePins,
    gpr_only_instructions_checked=len(instructions),max_local_stack_frame=max(stackUsage.values()),fixture=str(TMP))
(HERE/'validation.json').write_text(json.dumps(result,indent=2))
(HERE/'test-output.txt').write_text('\n'.join(outputs))
print(json.dumps(result,indent=2))
