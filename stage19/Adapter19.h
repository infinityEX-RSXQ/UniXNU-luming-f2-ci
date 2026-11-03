// SPDX-License-Identifier: BSD-2-Clause-Patent
// Exactly the kernel-consumer declaration in the pinned osfmk/kern/debug.h.
// Linked to the source-built kernel, never an address in the IPSW graphics kext.
extern "C" kern_return_t stack_snapshot_from_kernel(int,void *,uint32_t,uint64_t,uint64_t,uint32_t,unsigned *);
static cdx19::Sample cdx19_samples[2]={};
static unsigned cdx19_busy,cdx19_taken;
static constexpr uint32_t cdx19_capacity=4U*1024U*1024U;
// KCData + UUID load info + trylock + no I/O stats + wait owners + no latency
// + skip Exclaves. No faulting, no compression, no task/thread suspension API.
static constexpr uint64_t cdx19_flags=0x10000ULL|0x2ULL|0x8ULL|0x100000ULL|
    0x800000ULL|0x1000000ULL|0x40000000ULL|0x400000000ULL;
extern "C" bool cdx19_capture_next(void){
    if(option("luming-display-stackshot")!=1)return false;
    unsigned expected=0;
    if(!__atomic_compare_exchange_n(&cdx19_busy,&expected,1,false,__ATOMIC_ACQUIRE,__ATOMIC_RELAXED))return false;
    unsigned index=cdx19_taken;
    if(index>=2){__atomic_store_n(&cdx19_busy,0,__ATOMIC_RELEASE);return false;}
    auto &s=cdx19_samples[index];s={};s.begin=mach_absolute_time();s.flags=cdx19_flags;
    // This runs only in the independent thread_call, BEFORE quiesce or any
    // diagnostic lock. Stackshot itself owns debugger rendezvous/serialization.
    if(ml_at_interrupt_context() || !ml_get_interrupts_enabled()){s.rc=0xffff0001U;}
    else if(void *buffer=IOMalloc(cdx19_capacity)){
        bzero(buffer,cdx19_capacity);unsigned used=0;
        s.rc=(uint32_t)stack_snapshot_from_kernel(-1,buffer,cdx19_capacity,cdx19_flags,0,0,&used);
        s.bytes=used;
        if(!s.rc && used && used<=cdx19_capacity){
            (void)cdx19::parse(buffer,used,s);
            // Preserve original uncompressed kcdata even if our decoder fails.
            // Property failure is visible; it does not invalidate parsed rows.
            if(activeLegacyDisplay){OSData *data=OSData::withBytes(buffer,used);
                if(data){s.stored=activeLegacyDisplay->setProperty(index?"CDX19Raw1":"CDX19Raw0",data)?1U:0U;data->release();}}
        }else if(!s.rc){s.error=23;}
        IOFree(buffer,cdx19_capacity);
    }else {s.rc=0xffff0002U;}
    s.end=mach_absolute_time();
    if(activeLegacyDisplay){OSData *data=OSData::withBytes(&s,sizeof(s));
        if(data){activeLegacyDisplay->setProperty(index?"CDX19State1":"CDX19State0",data);data->release();}}
    cdx19_taken=index+1;__atomic_store_n(&cdx19_busy,0,__ATOMIC_RELEASE);
    return index==0;
}
static void cdx19_format(Cdx15Text &text,bool quiet,uint32_t copies,uint32_t retired){
    unsigned page=option("luming-display-stack-page");if(page>4)page=0;
    unsigned selected=option("luming-display-stack-thread");if(selected>7)selected=0;
    unsigned first=option("luming-display-stack-frame");if(first>28)first=28;
    unsigned step=option("luming-display-stack-step");if(step>28)step=28;
    text.line("CDX19 rev=20 pg=%u th=%u quiet=%u cp=%u ret=%u\n",page,selected,(unsigned)quiet,copies,retired);
    text.line("k=unslid w=unslid-or-perm sc=unavailable nofault\n");
    if(page>=3)text.line("target=lsd instance=%u domain=unknown\n",page-2);
    unsigned missing=0;
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];
        unsigned frame=first+(i?step:0);if(frame>28)frame=28;
        uint64_t nanos=0;if(s.begin>=cdx16_epoch)absolutetime_to_nanoseconds(s.begin-cdx16_epoch,&nanos);
        text.line("S%u ms=%llu rc=%x b=%u ok=%u err=%u raw=%u\n",i,
            (unsigned long long)(nanos/1000000),s.rc,s.bytes,s.parsed,s.error,s.stored);
        if(i>=cdx19_taken || !s.parsed){text.line("P%u stack=unavailable\n",i);continue;}
        const auto &p=s.processes[page];
        if(page>=3 && s.lsdInstances>2){text.line("P%u lsd-overflow=%u unavailable\n",i,s.lsdInstances-2);continue;}
        if(!p.seen){text.line("P%u process=not-found\n",i);continue;}
        if(p.matches>1){text.line("P%u ambiguous names=%u pid=%u/%u\n",i,p.matches,p.pid,p.otherpid);continue;}
        text.line("P%u p=%u n=%u r=%u w=%u ui=%u\n",i,p.pid,p.total,p.run,p.wait,p.unint);
        if(selected>=p.n){text.line("T%u thread=unavailable\n",i);continue;}
        // One selected thread on screen per sample; all eight retained in State.
        // Preserve the distinction between wait-info absent and type zero.
        const auto &t=p.threads[selected];missing+=p.total-1;
        text.line("T%u id=%llx st=%x fl=%llx wt=%u/%u\n",i,(unsigned long long)t.tid,t.state,
            (unsigned long long)t.flags,t.waitinfo,t.kind);
        // Kernel frames remain in State; give screen space to four user LRs.
        text.line("K%u c=%llx n=%u\n",i,(unsigned long long)t.continuation,t.nk);
        if(t.nu>frame)text.line("U%u n=%u f=%u %llx/%llx/%llx/%llx\n",i,t.nu,frame,
            (unsigned long long)t.u[frame],(unsigned long long)t.u[frame+1],
            (unsigned long long)t.u[frame+2],(unsigned long long)t.u[frame+3]);
        else text.line("U%u stack=unavailable\n",i);
        if(!t.waitinfo)text.line("W%u unavailable w=%llx\n",i,(unsigned long long)t.wait);
        else if(t.waitbytes==31)text.line("W%u t=%u f=%x l=%d owner=%llx cx=%llx\n",i,t.kind,
            t.waitflags,(int)t.portlabel,(unsigned long long)t.owner,(unsigned long long)t.context);
        else text.line("W%u t=%u f=? l=? owner=%llx cx=%llx\n",i,t.kind,
            (unsigned long long)t.owner,(unsigned long long)t.context);
    }
    const auto &s=cdx19_samples[cdx19_taken==2?1:0];const auto &p=s.processes[page];
    const unsigned char *uuid=p.cacheValid?p.uuid:s.uuid;uint64_t slide=p.cacheValid?p.cacheSlide:s.cacheSlide;
    bool valid=s.parsed && (p.cacheValid || s.cacheValid);char hex[33]={};
    for(unsigned i=0;i<16;++i){const char digits[]="0123456789abcdef";hex[2*i]=digits[uuid[i]>>4];hex[2*i+1]=digits[uuid[i]&15];}
    text.line("cache=%u sl=%llx uuid=%s\n",(unsigned)valid,(unsigned long long)slide,hex);
    text.footer(missing,false);
}
