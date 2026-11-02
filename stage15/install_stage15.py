"""Incremental source instrumentation after successful Stage14.1, before pre_build."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
PINS={
 'stage10/stage10-runtime/LegacyDisplayProbe.cpp':'f3f236517c920eaa6905404ac4601970db0cf2ed74233b94f36105fab255b775',
 'stage10/stage10-runtime/NativeLegacyDisplay.cpp':'8624070dc2a0c0b177b3799ea65b59d3f469dd4be8ab5ffbab59f02be9caa09b',
 'patches/xnu/device/zzzzzzzzzzzzzzzzzzzzzzz-cdx14p1-console-reclaim.patch':'6f495723a41214d857b64e0776c0e56efcbe57cb203fcf3fc8c30119507931e2',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def once(t,a,b):assert t.count(a)==1,repr(a);return t.replace(a,b)
def install(device,apply=False):
    raw={p:(device/p).read_bytes().replace(b'\r\n',b'\n') for p in PINS}
    for p,h in PINS.items():assert sha(raw[p])==h,'Stage14.1 input drift: '+p
    probe=raw['stage10/stage10-runtime/LegacyDisplayProbe.cpp'].decode()
    decl='''extern "C" void cdx15_mapping_observed(IOMemoryMap *,uint32_t,uint32_t,uint64_t);
extern "C" void cdx15_client_open(task_t,uint32_t,IOUserClient *,IOReturn);
extern "C" void cdx15_validation(const void *,bool,uint32_t);
extern "C" void cdx15_copy(const void *,uint32_t);
extern "C" void cdx15_vsync(unsigned,unsigned);
extern "C" void cdx15_snapshot(char *,size_t,bool);
'''
    probe=once(probe,'#include <kern/task.h>','#include <kern/task.h>\n#include <kern/thread.h>\n#include <IOKit/IOLocks.h>')
    probe=once(probe,'static unsigned consoleOwnership;','static unsigned consoleOwnership;\n'+decl)
    probe=once(probe,'    return cdx13_publish_ui_scale(width,height);',
        '    bool ok=cdx13_publish_ui_scale(width,height);\n    if(ok)cdx15_mapping_observed(mapping,width,height,v.v_rowBytes);\n    return ok;')
    probe=once(probe,'void native_legacy_swap_validation_observed(bool accepted,unsigned reason,const void *,const void *) {',
        'void native_legacy_swap_validation_observed(bool accepted,unsigned reason,const void *request,const void *) {\n    cdx15_validation(request,accepted,reason);')
    probe=once(probe,'void native_legacy_transfer_observed(IOReturn status,const void *,uint64_t bytes) {',
        'void native_legacy_transfer_observed(IOReturn status,const void *request,uint64_t bytes) {\n    cdx15_copy(request,(uint32_t)status);')
    probe=once(probe,'void native_legacy_vsync_observed(unsigned event,unsigned) {',
        'void native_legacy_vsync_observed(unsigned event,unsigned hz) {\n    cdx15_vsync(event,hz);')
    start=probe.index('static void cdx14_snapshot_callback(thread_call_param_t,thread_call_param_t) {')
    end=probe.index('extern "C" void cdx14p1_schedule_snapshot(void)',start)
    probe=probe[:start]+'''static void cdx14_snapshot_callback(thread_call_param_t,thread_call_param_t) {
    bool quiet=cdx14p1_quiesce();
    char reason[660]={};
    // Last-destination sampling MUST precede console clear/reacquisition.
    cdx15_snapshot(reason,sizeof(reason),quiet);
    unsigned reclaimed=quiet?cdx14p1_console_reclaim():0;
    panic("CDX15 snapshot (intentional) r=%u\\n%s",reclaimed,reason);
}
'''+probe[end:]
    for name in ['TraceModel15.h','Text15.h','ProviderTrace15.h']:probe+='\n'+(HERE/name).read_text(encoding='utf-8')
    backend=raw['stage10/stage10-runtime/NativeLegacyDisplay.cpp'].decode()
    backend=once(backend,'class NativeLegacyDisplay : public IOMobileFramebufferLegacy {','''extern "C" void cdx15_head(const void *);
extern "C" void cdx15_gate(uint32_t);
extern "C" void cdx15_target_observed(void);
extern "C" uint64_t cdx15_retire_begin(const void *);
extern "C" void cdx15_retire_end(const void *,uint64_t);
extern "C" void cdx15_vsync(unsigned,unsigned);
extern "C" void cdx15_client_open(task_t,uint32_t,IOUserClient *,IOReturn);
class NativeLegacyDisplay : public IOMobileFramebufferLegacy {''')
    anchor='        if(enabled!=1 || transferred || !logicalPM || !bootMapping || !primary)return;'
    backend=once(backend,anchor,'''        uint32_t gates=(enabled==1?1U:0U)|(transferred?2U:0U)|(logicalPM?4U:0U)|(bootMapping?8U:0U)|(primary?16U:0U);
        cdx15_gate(gates);
'''+anchor)
    backend=once(backend,'        if(!request || !isValidated(request))return;',
        '        bool validated=request && isValidated(request);\n'
        '        cdx15_gate(gates|(request?32U:0U)|(validated?64U:0U));\n'
        '        if(!validated)return;\n        cdx15_head(request);')
    backend=once(backend,'            native_legacy_frame_observed(1,0,0,0,0,0);',
        '            cdx15_target_observed();\n            native_legacy_frame_observed(1,0,0,0,0,0);')
    backend=once(backend,'        cdx14_frame_end(true);','        cdx15_target_observed();\n        cdx14_frame_end(true);')
    backend=once(backend,'        IOMobileFramebufferLegacy::completeCurrentSwap();',
        '        uint64_t cdx15_generation=cdx15_retire_begin(request);\n'
        '        IOMobileFramebufferLegacy::completeCurrentSwap();\n        cdx15_retire_end(request,cdx15_generation);')
    anchor='        native_legacy_client_observed(status,status==kIOReturnSuccess && client?*client:nullptr);return status;'
    backend=once(backend,anchor,'        cdx15_client_open(task,type,status==kIOReturnSuccess && client?*client:nullptr,status);\n'+anchor)
    backend=once(backend,'        vsyncArmed=false;\n        if(!vsyncTimer)return;',
        '        vsyncArmed=false;cdx15_vsync(8,vsyncHz);\n        if(!vsyncTimer)return;')
    backend=once(backend,'        vsyncArmed=true;vsyncTimer->wakeAtTime(vsyncNext);',
        '        vsyncArmed=true;vsyncTimer->wakeAtTime(vsyncNext);cdx15_vsync(7,vsyncHz);')
    backend=once(backend,'        OSSafeReleaseNULL(vsyncTimer);vsyncArmed=false;',
        '        OSSafeReleaseNULL(vsyncTimer);vsyncArmed=false;cdx15_vsync(6,vsyncHz);')
    patch='zzzzzzzzzzzzzzzzzzzzzzzz-cdx15-observe.patch'
    series=(device/'patches/xnu/device/series').read_text(encoding='utf-8');assert patch not in series
    changes={'stage10/stage10-runtime/LegacyDisplayProbe.cpp':probe.encode(),
        'stage10/stage10-runtime/NativeLegacyDisplay.cpp':backend.encode(),
        'patches/xnu/device/'+patch:(HERE/patch).read_bytes(),
        'patches/xnu/device/series':(series.rstrip()+'\n'+patch+'\n').encode()}
    result=dict(stage=15,applied=apply,before={p:sha(b) for p,b in raw.items()},after={p:sha(b) for p,b in changes.items()},
        full_kernel_compiled=False,runtime_verified=False,device_operations=False)
    if apply:
        for p,b in changes.items():(device/p).write_bytes(b)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
