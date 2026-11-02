"""Observe the qualified original wait/completion; preserve their results."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
P='stage10/stage10-runtime/LegacyDisplayProbe.cpp'
B='stage10/stage10-runtime/NativeLegacyDisplay.cpp'
G='stage10/stage10-build/build-luming-cpu-legacy-display.py'
def sha(b):return hashlib.sha256(b).hexdigest()
def once(t,a,b):
    assert t.count(a)==1,repr(a)
    return t.replace(a,b)
def install(device,apply=False):
    pins=json.loads((HERE/'input-pins.json').read_text())
    before={p:(device/p).read_bytes().replace(b'\r\n',b'\n') for p in pins}
    for p,h in pins.items():assert sha(before[p])==h,'Stage17 input drift: '+p
    probe=before[P].decode()
    anchor='extern "C" uint64_t cdx15_ipc_begin(void *object,uint32_t selector) {'
    probe=once(probe,anchor,(HERE/'Model18.h').read_text()+'\n'+(HERE/'Adapter18.h').read_text()+'\n'+anchor)
    anchor='    if(option("luming-display-ipc-page")!=2){'
    probe=once(probe,anchor,(HERE/'Snapshot18.h').read_text()+'\n'+anchor)
    backend=before[B].decode()
    backend=once(backend,'#include <IOKit/IOLib.h>','#include <IOKit/IOLib.h>\n#include <IOKit/IOUserClient.h>')
    declarations='''struct Cdx18View {uint32_t valid,completed,current,queued;};
extern "C" uint64_t cdx18_wait_begin(IOUserClient *,uint32_t,uint32_t,uint32_t,const Cdx18View *);
extern "C" void cdx18_wait_end(uint64_t,uint32_t,const Cdx18View *);
extern "C" uint64_t cdx18_done_begin(uint32_t,uint32_t,const Cdx18View *);
extern "C" void cdx18_done_end(uint64_t,const Cdx18View *);
'''
    anchor='class NativeLegacyDisplay : public IOMobileFramebufferLegacy {'
    backend=once(backend,anchor,declarations+anchor)
    anchor='    void free() override {stopVsync();'
    backend=once(backend,anchor,(HERE/'Backend18.h').read_text()+anchor)
    anchor='        IOMobileFramebufferLegacy::completeCurrentSwap();'
    backend=once(backend,anchor,'''        uint64_t cdx18_token=0;
        if(enabled18()) {
            Cdx18View pre=gatedView18();uint32_t id=0,raw32c=0;
            if(pre.valid){
                const auto *bytes=reinterpret_cast<const unsigned char *>(request);
                memcpy(&id,bytes+0x314,4);memcpy(&raw32c,bytes+0x32c,4);
            }
            cdx18_token=cdx18_done_begin(id,raw32c,&pre);
        }
'''+anchor+'''
        // The original call may release request. Never dereference it here.
        if(cdx18_token){Cdx18View post=gatedView18();cdx18_done_end(cdx18_token,&post);}''')
    gen=before[G].decode()
    gen=once(gen,'struct OriginalLegacySwapRequest;','struct OriginalLegacySwapRequest;\nclass IOUserClient;')
    gen=once(gen,"    if i==184:header+=", "    if i==176:header+=' virtual IOReturn waitForSwap(IOUserClient *,uint32_t,uint32_t,uint32_t);\\n'\n    elif i==184:header+=")
    assert gen.count('155,184,188')==2
    gen=gen.replace('155,184,188','155,176,184,188')
    # Fail closed against every independently audited original instruction and
    # the selector-6 dispatch shape before linking any new parent import.
    guards=json.loads((HERE/'original-wait-guards.json').read_text())
    check='\n# Stage18: exact 21H461 wait/completion byte guards, raw -> postslide explicit.\n'
    check+='require(int(methods[176]["address"],16)==0xfffffff00578d998,"Stage18 original slot176 identity")\n'
    for name,g in guards['guards'].items():
        check+=f'require(read({int(g["raw_va"],16):#x}+SLIDE,{len(bytes.fromhex(g["bytes"]))})==bytes.fromhex({g["bytes"]!r}),"Stage18 original guard: {name}")\n'
    check+='require(read(0xfffffff006f35550+SLIDE,24)==struct.pack("<Q4I",0xfffffff006779518,3,0,0,0),"Stage18 selector6 exact dispatch")\n'
    gen=once(gen,"bindings={'__ZN25IOMobileFramebufferLegacyC2EPK11OSMetaClass'",check+"\nbindings={'__ZN25IOMobileFramebufferLegacyC2EPK11OSMetaClass'")
    gen=once(gen,'owned=[];native=[]',"bindings['__ZN25IOMobileFramebufferLegacy11waitForSwapEP12IOUserClientjjj']=0xfffffff00578d998\nowned=[];native=[]")
    changes={P:probe.encode(),B:backend.encode(),G:gen.encode()}
    report=dict(stage=18,before={p:sha(b) for p,b in before.items()},after={p:sha(b) for p,b in changes.items()},
        generated_abi_sha256=json.loads((HERE/'expected-abi.json').read_text())['sha256'],applied=apply,
        original_instructions_modified=False,prelinked_dispatch_changed=False,scheduling_policy_changed=False,
        full_kernel_compiled=False,runtime_verified=False)
    if apply:
        for p,b in changes.items():(device/p).write_bytes(b)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
