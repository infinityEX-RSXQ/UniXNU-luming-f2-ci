// SPDX-License-Identifier: BSD-2-Clause-Patent
// Appended after Stage14.1 definitions. No fake services or user-client vptr edits.
static IOSimpleLock *cdx15_lock;
static cdx15::State cdx15_state={};
// A serialized snapshot avoids putting the bounded event ring on the kernel stack.
static cdx15::State cdx15_snapshot_state={};static unsigned cdx15_snapshot_busy;
static unsigned cdx15_enabled;
static IOMemoryMap *cdx15_mapping; // one deliberate retained reference until reboot
static uint32_t cdx15_width,cdx15_height;static uint64_t cdx15_stride;
static unsigned cdx15_map_changed;static bool cdx15_target_valid;
static Cdx14Samples cdx15_target={};static uint64_t cdx15_target_sequence;
extern "C" size_t cdx15_daemon_summary(char *,size_t);
static uint64_t cdx15_now(){return mach_absolute_time();}
static bool cdx15_on(){return __atomic_load_n(&cdx15_enabled,__ATOMIC_ACQUIRE)!=0;}
extern "C" void cdx15_mapping_observed(IOMemoryMap *mapping,uint32_t w,uint32_t h,uint64_t stride) {
    unsigned enabled=(option("luming-display-frame-probe")==1 || option("luming-display-snapshot")==1)?1U:0U;
    PE_parse_boot_argn("luming-display-trace",&enabled,sizeof(enabled));if(enabled!=1)return;
    if(cdx15_mapping){if(cdx15_mapping!=mapping)__atomic_store_n(&cdx15_map_changed,1,__ATOMIC_RELEASE);return;}
    IOSimpleLock *lock=IOSimpleLockAlloc();if(!lock)return;
    mapping->retain();cdx15_mapping=mapping;cdx15_width=w;cdx15_height=h;cdx15_stride=stride;cdx15_lock=lock;
    __atomic_store_n(&cdx15_enabled,1,__ATOMIC_RELEASE);
}
extern "C" void cdx15_client_open(task_t task,uint32_t type,IOUserClient *client,IOReturn status) {
    if(!cdx15_on())return;
    proc_t proc=task?(proc_t)get_bsdtask_info(task):nullptr;uint32_t pid=proc?(uint32_t)proc_pid(proc):0;
    char comm[17]={};if(pid)proc_name((int)pid,comm,sizeof(comm));
    uint64_t id=client?client->getRegistryEntryID():0,now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::open(cdx15_state,id,pid,comm,type,(uint32_t)status,now);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" uint64_t cdx15_ipc_begin(void *object,uint32_t selector) {
    if(!cdx15_on() || !object)return 0;
    IOUserClient *client=static_cast<IOUserClient *>(object);
    uint64_t id=client->getRegistryEntryID(),now=cdx15_now(),thread=(uintptr_t)current_thread(),token=0;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    if(cdx15::client(cdx15_state,id))token=cdx15::begin(cdx15_state,id,thread,selector,now);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return token;
}
extern "C" void cdx15_ipc_end(uint64_t token,uint32_t status) {
    if(!cdx15_on() || !token)return;uint64_t now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::end(cdx15_state,token,status,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_validation(const void *request,bool accepted,uint32_t reason) {
    if(!cdx15_on())return;uint64_t now=cdx15_now(),thread=(uintptr_t)current_thread();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::validate(cdx15_state,(uintptr_t)request,thread,accepted,reason,now);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_head(const void *request) {
    if(!cdx15_on())return;uint64_t now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::head(cdx15_state,(uintptr_t)request,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_copy(const void *request,uint32_t status) {
    if(!cdx15_on())return;uint64_t now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::copied(cdx15_state,(uintptr_t)request,status,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" uint64_t cdx15_retire_begin(const void *request) {
    if(!cdx15_on())return 0;IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    uint64_t generation=cdx15::retireBegin(cdx15_state,(uintptr_t)request);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return generation;
}
extern "C" void cdx15_retire_end(const void *request,uint64_t generation) {
    if(!cdx15_on())return;uint64_t now=cdx15_now();IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::retireEnd(cdx15_state,(uintptr_t)request,generation,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_gate(uint32_t bits) {
    if(!cdx15_on())return;IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::gate(cdx15_state,bits);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_vsync(unsigned event,unsigned hz) {
    if(!cdx15_on())return;uint64_t now=cdx15_now();IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::vsync(cdx15_state,event,hz,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_target_observed(void) {
    if(!cdx15_on() || __atomic_load_n(&cdx15_map_changed,__ATOMIC_ACQUIRE))return;
    Cdx14Samples sample={};
    bool valid=cdx14_samples(reinterpret_cast<const volatile void *>(cdx15_mapping->getVirtualAddress()),
        cdx15_mapping->getLength(),cdx15_stride,cdx15_width,cdx15_height,&sample);
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15_target_valid=valid;if(valid){cdx15_target=sample;++cdx15_target_sequence;}
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
static unsigned cdx15_cap(uint64_t value,unsigned limit,bool &clipped){if(value>limit){clipped=true;return limit;}return (unsigned)value;}
static unsigned cdx15_ms(uint64_t ticks,bool &clipped){uint64_t ns=0;absolutetime_to_nanoseconds(ticks,&ns);return cdx15_cap(ns/1000000,999999,clipped);}
static int cdx15_service(const char *name,char (&cls)[17]) {
    cls[0]=0;OSDictionary *matching=IOService::serviceMatching(name);if(!matching)return -1;
    IOService *service=IOService::copyMatchingService(matching);matching->release();
    if(!service)return 0;
    cdx15::name(cls,service->getMetaClass()->getClassName());service->release();return 1;
}
extern "C" void cdx15_snapshot(char *out,size_t capacity,bool quiet) {
    Cdx15Text text(out,capacity);bool clipped=false;
    if(!cdx15_on()){text.line("CDX15 trace=unavailable\n");text.footer(0,false);return;}
    unsigned expected=0;
    if(!__atomic_compare_exchange_n(&cdx15_snapshot_busy,&expected,1,false,__ATOMIC_ACQUIRE,__ATOMIC_RELAXED)){
        text.line("CDX15 snapshot=busy\n");text.footer(0,false);return;
    }
    struct Lease {~Lease(){__atomic_store_n(&cdx15_snapshot_busy,0,__ATOMIC_RELEASE);}} lease;
    cdx15::State &state=cdx15_snapshot_state;Cdx14Samples last;bool targetValid;uint64_t seq;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    state=cdx15_state;last=cdx15_target;targetValid=cdx15_target_valid;seq=cdx15_target_sequence;
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
    bool mapValid=!__atomic_load_n(&cdx15_map_changed,__ATOMIC_ACQUIRE);
    Cdx14Samples late={};bool lateValid=quiet && targetValid && mapValid && cdx15_mapping &&
        cdx14_samples(reinterpret_cast<const volatile void *>(cdx15_mapping->getVirtualAddress()),cdx15_mapping->getLength(),
            cdx15_stride,cdx15_width,cdx15_height,&late);
    char wd[17]={},aks[17]={},alt[17]={};int watchdog=cdx15_service("IOWatchdog",wd);
    int keyStore=cdx15_service("AppleKeyStore",aks),alternate=cdx15_service("AppleARMWatchdogTimer",alt);
    char daemon[352]={};cdx15_daemon_summary(daemon,sizeof(daemon));
    // All full counters, timestamps, clients and bounded events remain available as data.
    if(activeLegacyDisplay){OSData *data=OSData::withBytes(&state,sizeof(state));
        if(data){activeLegacyDisplay->setProperty("CDX15TraceState",data);data->release();}}
    text.line("CDX15 quiet=%u gate=%x\n",(unsigned)quiet,state.gate);
    text.line("sub=? ipc=%u val=%u q=%u cp=%u ret=%u rej=%u\n",cdx15_cap(state.ipc,65535,clipped),
        cdx15_cap(state.val,65535,clipped),cdx15_cap(state.head,65535,clipped),cdx15_cap(state.copy,65535,clipped),
        cdx15_cap(state.ret,65535,clipped),cdx15_cap(state.reject,65535,clipped));
    text.line("F=?/%u/%u/%u/%u\n",cdx15_ms(state.first[1],clipped),cdx15_ms(state.first[2],clipped),
        cdx15_ms(state.first[3],clipped),cdx15_ms(state.first[4],clipped));
    text.line("L=?/%u/%u/%u/%u\n",cdx15_ms(state.last[1],clipped),cdx15_ms(state.last[2],clipped),
        cdx15_ms(state.last[3],clipped),cdx15_ms(state.last[4],clipped));
    text.line("vs=%u last=%u sub=? arm=%u late=%u\n",cdx15_cap(state.vsync,65535,clipped),
        cdx15_ms(state.lastVsync,clipped),(unsigned)state.armed,cdx15_cap(state.late,65535,clipped));
    char tail[640]={};Cdx15Text rest(tail,sizeof(tail));
    if(lateValid){rest.line("late=%llx last=%llx eq=%u\n",(unsigned long long)late.hash,
        (unsigned long long)last.hash,(unsigned)!cdx14_sample_diff(late,last));
        rest.line("latepx=%08x lastpx=%08x f=%u\n",late.pixels[0],last.pixels[0],cdx15_cap(seq,65535,clipped));}
    else rest.line("late=skip quiet=%u valid=%u map=%u\n",(unsigned)quiet,(unsigned)targetValid,(unsigned)mapValid);
    rest.line("wd=%d:%.16s aks=%d:%.16s\n",watchdog,wd,keyStore,aks);
    rest.line("wdAlt=%d:%.16s\n",alternate,alt);rest.lines(daemon);
    unsigned shown=0,total=0;
    for(const auto &c:state.clients)if(c.serial)++total;
    for(const auto &c:state.clients)if(c.serial && shown<4){
        char row[88]={};int n=snprintf(row,sizeof(row),"cli p=%u t=%x rc=%x n=%u %.16s\n",c.pid,c.type,c.status,
            cdx15_cap(c.validated,65535,clipped),c.name);
        if(n>0 && n<88 && text.used+(size_t)n+rest.used+90<capacity){text.line("%s",row);++shown;}
    }
    text.line("unk=%u linked=%u lost=%u\n",cdx15_cap(state.unknown,65535,clipped),cdx15_cap(state.linked,65535,clipped),
        cdx15_cap(state.drop,65535,clipped));text.lines(tail);
    text.dropped+=rest.dropped;text.footer(total-shown,clipped||state.saturated);
}
