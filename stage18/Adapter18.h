// SPDX-License-Identifier: BSD-2-Clause-Patent
static cdx18::State cdx18_state={},cdx18_snapshot_state={};
extern "C" uint64_t cdx18_wait_begin(IOUserClient *client,uint32_t id,uint32_t flags,
    uint32_t timeout,const Cdx18View *pre){
    if(!cdx15_on() || !pre)return 0;
    uint64_t entry=client?client->getRegistryEntryID():0,token=0;uint32_t pid=0;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    if(auto *c=cdx15::client(cdx15_state,entry))pid=c->pid;
    token=cdx18::waitBegin(cdx18_state,entry,pid,id,flags,timeout,*pre);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return token;
}
extern "C" void cdx18_wait_end(uint64_t token,uint32_t status,const Cdx18View *post){
    if(!cdx15_on() || !token || !post)return;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx18::waitEnd(cdx18_state,token,status,*post);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" uint64_t cdx18_done_begin(uint32_t id,uint32_t raw32c,const Cdx18View *pre){
    if(!cdx15_on() || !pre)return 0;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    uint64_t token=cdx18::doneBegin(cdx18_state,id,raw32c,*pre);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return token;
}
extern "C" void cdx18_done_end(uint64_t token,const Cdx18View *post){
    if(!cdx15_on() || !token || !post)return;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx18::doneEnd(cdx18_state,token,*post);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
