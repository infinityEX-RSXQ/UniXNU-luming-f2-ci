// SPDX-License-Identifier: BSD-2-Clause-Patent
// Same diagnostic lock as Stage15. No new private object fields or queue reads.
struct Cdx16VsyncState {
    uint32_t startAttempts,armAttempts,startReason,armReason,startFlags,armFlags,hz;
};
static Cdx16VsyncState cdx16_vsync={};
static uint64_t cdx16_epoch;
extern "C" void cdx16_vsync_observed(unsigned phase,unsigned reason,unsigned flags,unsigned hz) {
    if(!cdx15_on())return;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    if(phase==0){cdx15::inc(cdx15_state,cdx16_vsync.startAttempts);cdx16_vsync.startReason=reason;cdx16_vsync.startFlags=flags;}
    else {cdx15::inc(cdx15_state,cdx16_vsync.armAttempts);cdx16_vsync.armReason=reason;cdx16_vsync.armFlags=flags;}
    cdx16_vsync.hz=hz;IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
