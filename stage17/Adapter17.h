// SPDX-License-Identifier: BSD-2-Clause-Patent
static cdx17::State cdx17_state={},cdx17_snapshot_state={};
extern "C" void cdx17_ipc_arguments(uint64_t token,const IOExternalMethodArguments *args){
    if(!cdx15_on() || !token || !args)return;
    // Only 0..3 scalar values of these kernel-marshalled arguments are read.
    // Lookup first, so unrelated clients never cause argument reads.
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    auto *a=cdx17::find(cdx17_state,token,0);
    if(a){unsigned key=cdx17_state.rows[a->row].key;
        unsigned n=((key==6 || key==72) && args->scalarInput)?args->scalarInputCount:0;
        if(n>3)n=3;
        cdx17::arguments(cdx17_state,token,args->scalarInputCount,args->scalarOutputCount,args->scalarInput,n);}
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" uint64_t cdx17_port_begin(void *object,uint32_t type,unsigned wide,unsigned hasPort){
    if(!cdx15_on() || !object)return 0;
    uint64_t id=static_cast<IOUserClient *>(object)->getRegistryEntryID(),now=cdx15_now(),token=0;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    if(auto *c=cdx15::client(cdx15_state,id)){
        if(cdx17_state.next==UINT64_MAX)cdx17_state.saturated=true;
        else token=cdx17::begin(cdx17_state,++cdx17_state.next,id,c->pid,type,wide?2U:1U,hasPort!=0,now);}
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return token;
}
extern "C" void cdx17_port_end(uint64_t token,unsigned wide,uint32_t status){
    if(!cdx15_on() || !token)return;uint64_t now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx17::end(cdx17_state,token,wide?2U:1U,status,now);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
