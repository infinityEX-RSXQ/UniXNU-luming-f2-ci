"""Observe why Stage15 vsync has zero notifications; preserve scheduling policy."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
PINS={
 'stage10/stage10-runtime/LegacyDisplayProbe.cpp':'53c63b9bd5583ba3692f853ef9dde085467e63b7812b4d9b1f0e62e0e0322d7c',
 'stage10/stage10-runtime/NativeLegacyDisplay.cpp':'830f091534c3c777da55c429675230506c91875c6bc87d78a784516523aae2b6',
 'patches/xnu/device/zzzzzzzzzzzzzzzzzzzzzzzz-cdx15-observe.patch':'5bd651af5b44260d769109b7cf8f14d06739b181b7b7e86cbc7203281f6bcda5',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def once(t,a,b):assert t.count(a)==1,repr(a);return t.replace(a,b)
def install(device,apply=False):
    before={p:(device/p).read_bytes().replace(b'\r\n',b'\n') for p in PINS}
    for p,h in PINS.items():assert sha(before[p])==h,'Stage15 successful CI input drift: '+p
    probe=before['stage10/stage10-runtime/LegacyDisplayProbe.cpp'].decode()
    probe=once(probe,'CDX15 snapshot (intentional) r=%u','CDX16 snapshot (intentional) r=%u')
    anchor='static bool cdx15_on(){return __atomic_load_n(&cdx15_enabled,__ATOMIC_ACQUIRE)!=0;}\n'
    probe=once(probe,anchor,anchor+(HERE/'Vsync16.h').read_text(encoding='utf-8')+'\n')
    probe=once(probe,'    __atomic_store_n(&cdx15_enabled,1,__ATOMIC_RELEASE);',
        '    cdx16_epoch=mach_absolute_time();\n    __atomic_store_n(&cdx15_enabled,1,__ATOMIC_RELEASE);')
    old='static unsigned cdx15_ms(uint64_t ticks,bool &clipped){uint64_t ns=0;absolutetime_to_nanoseconds(ticks,&ns);return cdx15_cap(ns/1000000,999999,clipped);}'
    new='''static unsigned cdx15_ms(uint64_t ticks,bool &clipped){
    if(!ticks)return 0;
    if(ticks<cdx16_epoch){clipped=true;return 0;}
    uint64_t ns=0;absolutetime_to_nanoseconds(ticks-cdx16_epoch,&ns);return cdx15_cap(ns/1000000,999999,clipped);
}'''
    probe=once(probe,old,new)
    probe=once(probe,'    cdx15::State &state=cdx15_snapshot_state;Cdx14Samples last;bool targetValid;uint64_t seq;',
        '    cdx15::State &state=cdx15_snapshot_state;Cdx16VsyncState pacing;Cdx14Samples last;bool targetValid;uint64_t seq;')
    probe=once(probe,'    state=cdx15_state;last=cdx15_target;targetValid=cdx15_target_valid;seq=cdx15_target_sequence;',
        '    state=cdx15_state;pacing=cdx16_vsync;last=cdx15_target;targetValid=cdx15_target_valid;seq=cdx15_target_sequence;')
    probe=once(probe,'    text.line("CDX15 quiet=%u gate=%x\\n",(unsigned)quiet,state.gate);',
        '    text.line("CDX16 quiet=%u gate=%x age=%u\\n",(unsigned)quiet,state.gate,cdx15_ms(mach_absolute_time(),clipped));')
    anchor='    char tail[640]={};Cdx15Text rest(tail,sizeof(tail));'
    probe=once(probe,anchor,'''    text.line("vst=%u sa=%u ar=%u aa=%u sf=%x af=%x hz=%u\\n",pacing.startReason,
        cdx15_cap(pacing.startAttempts,65535,clipped),pacing.armReason,cdx15_cap(pacing.armAttempts,65535,clipped),
        pacing.startFlags,pacing.armFlags,pacing.hz);
    if(activeLegacyDisplay){OSData *data=OSData::withBytes(&pacing,sizeof(pacing));
        if(data){activeLegacyDisplay->setProperty("CDX16VsyncState",data);data->release();}}
'''+anchor)
    backend=before['stage10/stage10-runtime/NativeLegacyDisplay.cpp'].decode()
    anchor='class NativeLegacyDisplay : public IOMobileFramebufferLegacy {'
    backend=once(backend,anchor,'extern "C" void cdx16_vsync_observed(unsigned,unsigned,unsigned,unsigned);\n'+anchor)
    start=backend.index('    void armVsync() {');end=backend.index('    static void vsyncFired',start)
    backend=backend[:start]+'''    void armVsync() {
        unsigned flags=(vsyncTimer?1U:0U)|(primary?2U:0U)|(bootMapping?4U:0U);
        if(!vsyncTimer || vsyncArmed){cdx16_vsync_observed(1,!vsyncTimer?1U:2U,flags,vsyncHz);return;}
        bool wanted=vsyncWanted();flags|=32U|(wanted?16U:0U);
        if(!wanted){cdx16_vsync_observed(1,3,flags,vsyncHz);return;}
        vsyncArmed=true;vsyncNext=mach_absolute_time()+vsyncInterval;
        vsyncTimer->wakeAtTime(vsyncNext);native_legacy_vsync_observed(0,vsyncHz);
        cdx16_vsync_observed(1,4,flags,vsyncHz);
    }
'''+backend[end:]
    start=backend.index('    void startVsync() {');end=backend.index('    void stopVsync()',start)
    backend=backend[:start]+'''    void startVsync() {
        unsigned hz=0;PE_parse_boot_argn("sheng-vsync",&hz,sizeof(hz));
        unsigned flags=(vsyncTimer?1U:0U)|(primary?2U:0U)|(bootMapping?4U:0U);
        if(!hz || hz>240 || !primary || !bootMapping || vsyncTimer){
            unsigned reason=!hz?1U:hz>240?2U:!primary?3U:!bootMapping?4U:5U;
            cdx16_vsync_observed(0,reason,flags,hz);return;
        }
        IOWorkLoop *loop=getWorkLoop();
        if(!loop){cdx16_vsync_observed(0,6,flags,hz);return;}
        flags|=8U;
        IOTimerEventSource *timer=IOTimerEventSource::timerEventSource(this,&NativeLegacyDisplay::vsyncFired);
        if(!timer){cdx16_vsync_observed(0,7,flags,hz);return;}
        if(loop->addEventSource(timer)!=kIOReturnSuccess){timer->release();cdx16_vsync_observed(0,8,flags,hz);return;}
        nanoseconds_to_absolutetime(1000000000ull/hz,&vsyncInterval);
        vsyncHz=hz;vsyncTimer=timer;native_legacy_vsync_observed(4,hz);
        cdx16_vsync_observed(0,9,flags|1U,hz);
        loop->runAction([](OSObject *owner,void *,void *,void *,void *)->IOReturn {
            static_cast<NativeLegacyDisplay *>(owner)->armVsync();return kIOReturnSuccess;
        },this);
    }
'''+backend[end:]
    changes={'stage10/stage10-runtime/LegacyDisplayProbe.cpp':probe.encode(),
        'stage10/stage10-runtime/NativeLegacyDisplay.cpp':backend.encode()}
    report=dict(stage=16,before={p:sha(b) for p,b in before.items()},after={p:sha(b) for p,b in changes.items()},
        applied=apply,core_patch_unchanged=True,scheduling_policy_changed=False,full_kernel_compiled=False,runtime_verified=False)
    if apply:
        for p,b in changes.items():(device/p).write_bytes(b)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--device',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.device.resolve(),a.apply),indent=2))
