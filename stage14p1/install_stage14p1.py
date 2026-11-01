"""Source-only incremental installer after the successful dsh Stage14 installer."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
PINS={
 'stage10/stage10-runtime/LegacyDisplayProbe.cpp':'d3c4e0edc57fb9f2d5de583b80907cf4637018fd79a2791192776e3862043f0a',
 'stage10/stage10-runtime/NativeLegacyDisplay.cpp':'6063488553c940f4462e8722ac73ce46e99fb8f28035f219db470a95c5927bdf',
 'patches/xnu/device/zzzzzzzzzzzzzzzzzzzzzz-cdx14-observation.patch':'137b514e570a4edeb593f071774c5975399a9f0a64cd8ec26e862e90c2d0e158',
}
LEASE='''extern "C" bool cdx14p1_scanout_enter(void);
extern "C" void cdx14p1_scanout_leave(void);
struct Cdx14p1ScanoutLease {
    bool held;
    Cdx14p1ScanoutLease():held(cdx14p1_scanout_enter()){}
    ~Cdx14p1ScanoutLease(){if(held)cdx14p1_scanout_leave();}
    Cdx14p1ScanoutLease(const Cdx14p1ScanoutLease &)=delete;
    Cdx14p1ScanoutLease &operator=(const Cdx14p1ScanoutLease &)=delete;
};
'''
def sha(b):return hashlib.sha256(b).hexdigest()
def once(t,a,b):
    assert t.count(a)==1,repr(a);return t.replace(a,b)
def install(device,apply=False):
    raw={p:(device/p).read_bytes().replace(b'\r\n',b'\n') for p in PINS}
    for p,h in PINS.items():assert sha(raw[p])==h,'Successful Stage14 source drift: '+p
    probe=raw['stage10/stage10-runtime/LegacyDisplayProbe.cpp'].decode()
    probe=once(probe,'extern "C" void cdx14_after_release(void);',
        'extern "C" void cdx14_after_release(void);\nextern "C" void cdx14p1_schedule_snapshot(void);')
    probe=once(probe,'    if(option("luming-display-console-handoff")!=1)return true;',
        '    if(option("luming-display-console-handoff")!=1) {cdx14p1_schedule_snapshot();return true;}')
    anchor='static thread_call_t cdx14_snapshot_call;'
    helper=(HERE/'ScanoutQuiesce.h').read_text(encoding='utf-8')
    probe=once(probe,anchor,helper+'\nextern "C" unsigned cdx14p1_console_reclaim(void);\n'+anchor)
    anchor='static void cdx14_snapshot_callback(thread_call_param_t,thread_call_param_t) {\n'
    probe=once(probe,anchor,anchor+'    bool quiet=cdx14p1_quiesce();\n'
        '    unsigned vtBefore[5]={};cdx14_console_snapshot(vtBefore);\n'
        '    unsigned reclaimed=quiet?cdx14p1_console_reclaim():0;\n')
    probe=once(probe,'panic("CDX14 diagnostic snapshot (intentional)\\n"',
        'panic("CDX14.1 diagnostic snapshot (intentional)\\n"\n'
        '        "quiet=%u active=%u reclaim=%u before=%u/%u/%u\\n"')
    anchor='        (unsigned long long)cdx14_frame.sequence,cdx14_frame.sampled,cdx14_frame.blankCount,cdx14_frame.valid,'
    probe=once(probe,anchor,'        (unsigned)quiet,__atomic_load_n(&cdx14p1_writers,__ATOMIC_SEQ_CST),reclaimed,\n'
        '        vtBefore[0],vtBefore[1],vtBefore[2],\n'+anchor)
    anchor='extern "C" void cdx14_after_release(void) {\n    if(option("luming-display-vt-latch")==1)cdx14_console_commit();'
    probe=once(probe,anchor,'extern "C" void cdx14p1_schedule_snapshot(void) {')
    probe+='\nextern "C" void cdx14_after_release(void) {\n'
    probe+='    if(option("luming-display-vt-latch")==1)cdx14_console_commit();\n'
    probe+='    cdx14p1_schedule_snapshot();\n}\n'
    backend=raw['stage10/stage10-runtime/NativeLegacyDisplay.cpp'].decode()
    backend=once(backend,'class NativeLegacyDisplay : public IOMobileFramebufferLegacy {',LEASE+'\nclass NativeLegacyDisplay : public IOMobileFramebufferLegacy {')
    backend=once(backend,'    void kickOnce() {','    void kickOnce() {\n        Cdx14p1ScanoutLease lease;if(!lease.held)return;')
    patch='zzzzzzzzzzzzzzzzzzzzzzz-cdx14p1-console-reclaim.patch'
    series=(device/'patches/xnu/device/series').read_text(encoding='utf-8');assert patch not in series
    changes={'stage10/stage10-runtime/LegacyDisplayProbe.cpp':probe.encode(),
        'stage10/stage10-runtime/NativeLegacyDisplay.cpp':backend.encode(),
        'patches/xnu/device/'+patch:(HERE/patch).read_bytes(),
        'patches/xnu/device/series':(series.rstrip()+'\n'+patch+'\n').encode()}
    report=dict(stage='14.1',applied=apply,before={k:sha(b) for k,b in raw.items()},
        after={k:sha(b) for k,b in changes.items()},full_kernel_compiled=False,runtime_verified=False,device_operations=False)
    if apply:
        for p,b in changes.items():(device/p).write_bytes(b)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
