"""Default-off two-sample stackshot consumer; preserve Stage18/backend unchanged."""
from pathlib import Path
import argparse
import hashlib
import json
HERE=Path(__file__).resolve().parent
P='stage10/stage10-runtime/LegacyDisplayProbe.cpp'
B='stage10/stage10-runtime/NativeLegacyDisplay.cpp'
G='stage10/stage10-build/build-luming-cpu-legacy-display.py'
PINS={P:'77aad4d83579a0cf53f039ee0b72fe098385bbaced1ef2182b45b5fd6b1d2fef',
      B:'3f75b236341f9a75f44590c09eda645ac7a5f25272629f12636360a1f9afc509',
      G:'6dfb103955461816f3b4f4617728e23320fdf8ccc408cde951cbfc53e645da9f'}
def sha(b):return hashlib.sha256(b).hexdigest()
def once(t,a,b):
    assert t.count(a)==1,repr(a)
    return t.replace(a,b)
def install(device,apply=False):
    before={p:(device/p).read_bytes().replace(b'\r\n',b'\n') for p in PINS}
    for p,h in PINS.items():assert sha(before[p])==h,'Stage18 r2 drift: '+p
    probe=before[P].decode()
    probe=once(probe,'static thread_call_t cdx14_snapshot_call;',
        'extern "C" bool cdx19_capture_next(void);\nstatic thread_call_t cdx14_snapshot_call;')
    old='static void cdx14_snapshot_callback(thread_call_param_t,thread_call_param_t) {\n'
    new=old+'''    if(option("luming-display-stackshot")==1){
        if(cdx19_capture_next()){
            uint64_t deadline;clock_interval_to_deadline(15,NSEC_PER_SEC,&deadline);
            thread_call_enter_delayed(cdx14_snapshot_call,deadline);return;
        }
        bool quiet19=cdx14p1_quiesce();char stackReason[820]={};
        cdx15_snapshot(stackReason,sizeof(stackReason),quiet19);
        unsigned reclaimed19=quiet19?cdx14p1_console_reclaim():0;
        panic("CDX19 stackshot (intentional) r=%u\\n%s",reclaimed19,stackReason);
    }
'''
    probe=once(probe,old,new)
    anchor='extern "C" uint64_t cdx15_ipc_begin(void *object,uint32_t selector) {'
    probe=once(probe,anchor,(HERE/'Model19.h').read_text()+'\n'+(HERE/'Adapter19.h').read_text()+'\n'+anchor)
    anchor='    if(option("luming-display-wait-probe")==1){'
    probe=once(probe,anchor,'''    if(option("luming-display-stackshot")==1){
        cdx19_format(text,quiet,state.copy,state.ret);return;
    }
'''+anchor)
    changes={P:probe.encode()}
    result=dict(stage=19,before={p:sha(b) for p,b in before.items()},after={P:sha(changes[P]),B:sha(before[B]),G:sha(before[G])},
        backend_unchanged=True,generator_unchanged=True,display_abi_unchanged=True,
        original_methods_unchanged=True,source_kernel_api='stack_snapshot_from_kernel',
        default_off=True,full_kernel_compiled=False,runtime_verified=False,applied=apply)
    if apply:
        for p,b in changes.items():(device/p).write_bytes(b)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
