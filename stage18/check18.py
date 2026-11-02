from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE));from install_stage18 import install,P,B,G
TMP=Path('D:/Codex/tmp')/('stage18-check-'+str(time.time_ns()));device=TMP/'device'
def sha(b):return hashlib.sha256(b).hexdigest()
pins={}
for rel in (P,B,G):
    source=ROOT/'stage17-ipc-source-20261102/runtime'/Path(rel).name if rel!=G else ROOT/'builds/stage17-ci-work/repo'/rel
    data=source.read_bytes().replace(b'\r\n',b'\n');pins[rel]=sha(data)
    p=device/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
(HERE/'input-pins.json').write_text(json.dumps(pins,indent=2))
guards=json.loads((ROOT/'evidence/STAGE17-WAIT-STATIC-AUDIT-20261102.json').read_text())
(HERE/'original-wait-guards.json').write_text(json.dumps(guards,indent=2))
header=(ROOT/'builds/stage17-ipc-41402982992/OriginalLegacyFramebufferABI.h').read_text()
assert sha(header.encode())=='8465dbcff188e88e66fdbe9a5e24b102c093b06d17f879f7a55fa3d1c58f8016'
header=header.replace('struct OriginalLegacySwapRequest;','struct OriginalLegacySwapRequest;\nclass IOUserClient;')
header=header.replace(' virtual __attribute__((deprecated("Unclassified ABI: never call from source"))) void opaque176();',
    ' virtual IOReturn waitForSwap(IOUserClient *,uint32_t,uint32_t,uint32_t);')
assert 'opaque176' not in header
(HERE/'expected-abi.json').write_text(json.dumps({'sha256':sha(header.encode()),'virtual_entries':358,'new_qualified_slot':176},indent=2))
assert not install(device)['applied'];result=install(device,True)
try:install(device,True)
except AssertionError:pass
else:raise AssertionError('reapplication accepted')
runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
for rel in (P,B,G):(runtime/Path(rel).name).write_bytes((device/rel).read_bytes())
probe=(device/P).read_text();backend=(device/B).read_text();gen=(device/G).read_text()
compile(gen,'builder18','exec')
# Execute only the actual generator's value-only header block with the audited
# method shape. This proves our expected header is its exact output.
audit=json.loads((ROOT/'stage10-display-source-20261101/stage10-audit/raw-legacy-abi.json').read_text())
ns={'pure':audit['abstract_slots'],'OUT':TMP}
exec(gen[gen.index("header='''"):gen.index('compile_owned(ROOT/\'drivers/GopFramebuffer/NativeLegacyDisplay.cpp\'')],ns)
assert (TMP/'OriginalLegacyFramebufferABI.h').read_text()==header
assert backend.count('IOReturn waitForSwap(')==1
completion=backend[backend.index('    bool retireSwap('):backend.index('    // Separately gated retirement')]
post=completion.split('IOMobileFramebufferLegacy::completeCurrentSwap();',1)[1]
assert 'bytes+' not in post and 'reinterpret_cast<const unsigned char *>(request)' not in post
assert completion.index('bytes+0x314')<completion.index('completeCurrentSwap();')<completion.index('cdx18_done_end(')
assert probe.count('struct Cdx18View')==1
# Retain and rerun all Stage15/16/17 meaningful adapter tests on the new source.
(TMP/'Adapter18.fixture.h').write_text(probe[probe.index('static IOSimpleLock *cdx15_lock;'):])
for name in ['TraceModel15.h','Text15.h']:(TMP/name).write_bytes((ROOT/'stage15-trace-source-20261102'/name).read_bytes())
(TMP/'FrameSamples14.fixture.h').write_bytes((ROOT/'stage14-scanout-source-20261102/FrameSamples14.h').read_bytes())
sys.path.insert(0,str(ROOT/'stage15-trace-source-20261102'));from make_core_patch15 import DAEMON
(TMP/'daemon15.fixture.h').write_text(DAEMON)
test=(ROOT/'stage17-ipc-source-20261102/test_adapter17.cpp').read_text().replace('Adapter17.fixture.h','Adapter18.fixture.h')
test=test.replace('static unsigned page17=2;', 'static unsigned wait18=0;static unsigned page17=2;')
test=test.replace('return !strcmp(s,"luming-display-ipc-page")?page17:1;',
    'return !strcmp(s,"luming-display-wait-probe")?wait18:!strcmp(s,"luming-display-ipc-page")?page17:1;')
extra=r'''
static void test18(){
    cdx18::State s={};Cdx18View a={1,1,1,0},b={1,2,0,1};
    auto x=cdx18::waitBegin(s,100,58,1,0x80000000,0,a);
    auto y=cdx18::waitBegin(s,100,58,2,0,50,a);
    auto d=cdx18::doneBegin(s,2,0xf,a);
    cdx18::waitEnd(s,y,0,b);cdx18::doneEnd(s,d,b);cdx18::waitEnd(s,x,0xe00002d5,b);
    assert(s.waits[0].id==1 && s.waits[0].status==0xe00002d5 && s.waits[1].status==0);
    assert(s.completions[0].raw32c==15 && s.completions[0].post.completed==2);
    cdx18::waitEnd(s,x,9,a);assert(s.unmatched==1 && s.waits[0].status==0xe00002d5);
    for(unsigned i=2;i<16;++i)assert(cdx18::waitBegin(s,0,0,i,0,0,a));
    assert(!cdx18::waitBegin(s,0,0,18,0,0,a) && s.lost==1);
    for(unsigned i=1;i<8;++i)assert(cdx18::doneBegin(s,i,0,a));
    assert(!cdx18::doneBegin(s,20,0,a) && s.lost==2);
    cdx18::State max={};max.next=UINT64_MAX;assert(!cdx18::waitBegin(max,0,0,0,0,0,a) && max.saturated);
    cdx18_state={};cdx15_state={};cdx15_enabled=1;
    MockProc proc={58,"backboardd"};IOUserClient client={91};cdx15_client_open(&proc,0,&client,0);
    auto t=cdx18_wait_begin(&client,1,0x80000000,0,&a);assert(t && cdx18_state.waits[0].pid==58);
    cdx18_wait_end(t,0xe00002d5,&b);assert(cdx18_state.waits[0].done);
    auto z=cdx18_done_begin(2,15,&a);cdx18_done_end(z,&b);
    auto u=cdx18_wait_begin(nullptr,2,0,0,&a);assert(u && !cdx18_state.waits[1].pid);
    char out[660];wait18=1;cdx15_snapshot(out,sizeof out,true);linesBounded(out);
    assert(strstr(out,"CDX18") && strstr(out,"i=1 f=80000000 t=0 r=e00002d5") && strstr(out,"c=1/2"));
    // Worst-width untrusted integers never overrun rows/buffer; omissions explicit.
    cdx18_state={};for(unsigned i=0;i<16;++i){cdx18_state.next=UINT64_MAX-40+i;
        auto t=cdx18::waitBegin(cdx18_state,UINT64_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,a);
        cdx18::waitEnd(cdx18_state,t,UINT32_MAX,b);}
    cdx15_snapshot(out,sizeof out,true);linesBounded(out);assert(strlen(out)<660 && strstr(out,"omit="));
    // Each individual worst-width line fits <=88 including newline.
    char row[700];Cdx15Text text(row,sizeof row);
    assert(text.line("W%llx p%u i=%x f=%x t=%x r=%x d=%u\n",(unsigned long long)UINT64_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,1U));
    assert(text.line("W%llx v=%u/%u c=%x/%x h=%u/%u q=%u/%u\n",(unsigned long long)UINT64_MAX,1U,1U,UINT32_MAX,UINT32_MAX,1U,1U,1U,1U));
    assert(text.line("D%llx i=%x x=%x d=%u v=%u/%u c=%x/%x\n",(unsigned long long)UINT64_MAX,UINT32_MAX,UINT32_MAX,1U,1U,1U,UINT32_MAX,UINT32_MAX));
    wait18=0;assert(!depth);
}
'''
test=test.replace('int main(){time16Tests();',extra+'int main(){time16Tests();')
test=test.replace('test17();puts(', 'test17();test18();puts(')
(TMP/'adapter.cpp').write_text(test);(HERE/'test_adapter18.cpp').write_text(test)
LLVM=Path('D:/civitoip20/.tools/llvm/clang+llvm-23.1.4-x86_64-pc-windows-msvc/bin')
def run(args):
    p=subprocess.run(list(map(str,args)),cwd=TMP,capture_output=True,text=True)
    assert p.returncode==0,p.stdout+'\n'+p.stderr
    return p.stdout
flags=['-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',TMP]
run([LLVM/'clang++.exe',*flags,TMP/'adapter.cpp','-o',TMP/'adapter.exe']);output=run([TMP/'adapter.exe'])
run([LLVM/'clang++.exe',*flags,'-I',HERE,HERE/'test_backend18.cpp','-o',TMP/'backend.exe']);run([TMP/'backend.exe'])
arm=['-target','arm64-apple-ios17.0','-ffreestanding','-fno-builtin','-fno-exceptions','-fno-rtti','-mgeneral-regs-only','-DCDX15_ABI_ONLY']
run([LLVM/'clang++.exe',*flags,*arm,'-c',TMP/'adapter.cpp','-o',TMP/'adapter-arm64.o'])
assembly=run([LLVM/'llvm-objdump.exe','--macho','--disassemble',TMP/'adapter-arm64.o'])
ins=[m.group(1) for m in re.finditer(r'^\s*[0-9a-f]+:\t(?:[0-9a-f]{2} ){3}[0-9a-f]{2}\t(.+)$',assembly,re.M)]
assert len(ins)>100
for x in ins:
    assert not x.split()[0].startswith('f') and x.split()[0] not in ('scvtf','ucvtf'),x
    assert not re.search(r'\b[bdhqsv](?:[0-9]|[12][0-9]|3[01])(?:\.[0-9a-z]+)?\b',x),x
result.update(passed=True,host_adapter=True,prior_stage15_16_17_tests=True,paired_concurrency=True,
    bounded_output=True,generated_header_exact=True,completion_no_post_release_read=True,backend_gate_and_passthrough=True,
    arm64_interface_fixture=True,gpr_only_instructions_checked=len(ins),fixture=str(TMP))
(HERE/'validation.json').write_text(json.dumps(result,indent=2));(HERE/'test-output.txt').write_text(output+'Stage18 paired wait/completion, owner, overflow, bounded output: PASS\n')
print(json.dumps(result,indent=2))
