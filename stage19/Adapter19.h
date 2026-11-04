// SPDX-License-Identifier: BSD-2-Clause-Patent
// Exactly the kernel-consumer declaration in the pinned osfmk/kern/debug.h.
// Linked to the source-built kernel, never an address in the IPSW graphics kext.
extern "C" kern_return_t stack_snapshot_from_kernel(int,void *,uint32_t,uint64_t,uint64_t,uint32_t,unsigned *);
static cdx19::Sample cdx19_samples[2]={};
static cdx21::Relations cdx21_samples[2]={};
static uint32_t cdx21_saved[2]={};
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
    auto &s=cdx19_samples[index];memset(&s,0,sizeof(s));s.begin=mach_absolute_time();s.flags=cdx19_flags;
    // This runs only in the independent thread_call, BEFORE quiesce or any
    // diagnostic lock. Stackshot itself owns debugger rendezvous/serialization.
    if(ml_at_interrupt_context() || !ml_get_interrupts_enabled()){s.rc=0xffff0001U;}
    else if(void *buffer=IOMalloc(cdx19_capacity)){
        bzero(buffer,cdx19_capacity);unsigned used=0;
        s.rc=(uint32_t)stack_snapshot_from_kernel(-1,buffer,cdx19_capacity,cdx19_flags,0,0,&used);
        s.bytes=used;
        if(!s.rc && used && used<=cdx19_capacity){
            (void)cdx19::parse(buffer,used,s);
            (void)cdx21::collect(buffer,used,s,cdx21_samples[index]);
            if(activeLegacyDisplay){OSData *rel=OSData::withBytes(&cdx21_samples[index],sizeof(cdx21::Relations));
                if(rel){cdx21_saved[index]=activeLegacyDisplay->setProperty(index?"CDX21State1":"CDX21State0",rel)?1U:0U;rel->release();}}
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
// SPDX-License-Identifier: BSD-2-Clause-Patent
// One compact report for both copied samples. Full owners/labels stay in State.
static void cdx21_format(Cdx15Text &text,bool quiet,uint32_t copies,uint32_t retired){
    text.line("CDX21 q=%u cp=%u ret=%u export=0 jobs=?\n",unsigned(quiet),copies,retired);
    const char *names[]={"BB","SB","LD","L1","L2"};
    for(unsigned p=0;p<5;++p){const auto &a=cdx19_samples[0];const auto &b=cdx19_samples[1];
        const auto &x=a.processes[p];const auto &y=b.processes[p];
        if(!a.parsed || !b.parsed || !x.n || !y.n || x.matches!=1 || y.matches!=1 ||
           (p>=3 && (a.lsdInstances>2 || b.lsdInstances>2))){text.line("%s unavailable/ambiguous\n",names[p]);continue;}
        text.line("%s p=%u/%u w=%u/%u o=%llx/%llx\n",names[p],x.pid,y.pid,x.threads[0].kind,y.threads[0].kind,
            (unsigned long long)x.threads[0].owner,(unsigned long long)y.threads[0].owner);
    }
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];const auto &r=cdx21_samples[i];
        uint64_t nanos=0;if(s.begin>=cdx16_epoch)absolutetime_to_nanoseconds(s.begin-cdx16_epoch,&nanos);
        text.line("S%u ms=%llu ok=%u rel=%u save=%u ov=%u dep=%u\n",i,(unsigned long long)(nanos/1000000),s.parsed,r.valid,cdx21_saved[i],r.overflow,r.depthLimited);
        if(!s.parsed || !r.valid)continue;
        if(!r.n){text.line("O%u unavailable\n",i);continue;}
        unsigned focus=option("luming-display-stack-owner");if(focus>=r.n){text.line("O%u slot=unavailable\n",i);continue;}
        const auto &o=r.owners[focus];
        if(!o.found){text.line("O%u tid=%llx unavailable matches=%u\n",i,(unsigned long long)o.tid,o.matches);continue;}
        text.line("O%u p=%u t=%llx w=%u src=%u\n",i,o.id.pid,(unsigned long long)o.tid,o.thread.kind,o.source);
        unsigned f=option("luming-display-stack-frame");if(f>28)f=28;
        if(o.thread.nu<=f)text.line("U%u n=%u f=%u unavailable\n",i,o.thread.nu,f);
        else if(o.thread.nu==f+1)text.line("U%u n=%u f=%u %llx/end\n",i,o.thread.nu,f,(unsigned long long)o.thread.u[f]);
        else text.line("U%u n=%u f=%u %llx/%llx\n",i,o.thread.nu,f,(unsigned long long)o.thread.u[f],(unsigned long long)o.thread.u[f+1]);
    }
    unsigned omitted=0;
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];const auto &r=cdx21_samples[i];
        omitted+=r.omitted+r.overflow+r.turnOverflow+r.labelOverflow+(r.n?r.n-1:0);
        for(const auto &p:s.processes)if(p.total)omitted+=p.total-1;
    }
    text.footer(omitted,false);
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Root selection follows a typed lsd wait; an owner slot is not an identity.
static const cdx19::Thread *cdx22_root(const cdx19::Process &p,unsigned ordinal){
    const unsigned kinds[]={18,10,1};
    for(unsigned k:kinds)for(unsigned j=0;j<p.n;++j){const auto &t=p.threads[j];
        if(t.kind!=k || strcmp(cdx21::kind(t),"tid"))continue;
        if(!ordinal)return &t;--ordinal;
    }
    return nullptr;
}
static const cdx21::Owner *cdx22_follow(cdx21::Relations &r,const cdx19::Thread &root,
                                    unsigned hop,const char **why){
    uint64_t seen[24]={};unsigned n=0;const cdx19::Thread *waiter=&root;
    for(unsigned depth=0;depth<=hop;++depth){
        if(strcmp(cdx21::kind(*waiter),"tid")){*why="next-not-tid";return nullptr;}
        for(unsigned j=0;j<n;++j)if(seen[j]==waiter->owner){*why="cycle";return nullptr;}
        if(n==24){*why="limit";return nullptr;}seen[n++]=waiter->owner;
        const auto *o=cdx21::find(r,waiter->owner);
        if(!o){*why="not-retained";return nullptr;}
        if(!o->found || o->matches!=1){*why=o->matches>1?"ambiguous":"not-found";return nullptr;}
        if(depth==hop)return o;
        waiter=&o->thread;
    }*why="unavailable";return nullptr;
}
static void cdx22_frames(Cdx15Text &text,unsigned i,const cdx19::Thread &t,unsigned frame){
    // Retain original raw counts, print only initialized copied entries.
    if(!t.nk)text.line("K%u n=0 c=%llx unavailable\n",i,(unsigned long long)t.continuation);
    else if(t.nk==1)text.line("K%u keep=1 c=%llx %llx/end\n",i,(unsigned long long)t.continuation,(unsigned long long)t.k[0]);
    else text.line("K%u keep=2 c=%llx %llx/%llx\n",i,(unsigned long long)t.continuation,(unsigned long long)t.k[0],(unsigned long long)t.k[1]);
    if(t.nu<=frame)text.line("U%u n=%u f=%u unavailable\n",i,t.nu,frame);
    else if(t.nu==frame+1)text.line("U%u n=%u f=%u %llx/end\n",i,t.nu,frame,(unsigned long long)t.u[frame]);
    else text.line("U%u n=%u f=%u %llx/%llx\n",i,t.nu,frame,(unsigned long long)t.u[frame],(unsigned long long)t.u[frame+1]);
}
static void cdx22_format(Cdx15Text &text,bool quiet,uint32_t copies,uint32_t retired){
    unsigned instance=option("luming-display-stack-step");if(instance>1)instance=0;
    unsigned ordinal=option("luming-display-stack-thread");if(ordinal>7)ordinal=0;
    unsigned hop=option("luming-display-stack-owner");if(hop>23)hop=23;
    unsigned frame=option("luming-display-stack-frame");if(frame>28)frame=28;
    text.line("CDX22 q=%u cp=%u ret=%u ls=%u r=%u h=%u\n",unsigned(quiet),copies,retired,instance+1,ordinal,hop);
    unsigned omitted=0;
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];auto &r=cdx21_samples[i];
        uint64_t ns=0;if(s.begin>=cdx16_epoch)absolutetime_to_nanoseconds(s.begin-cdx16_epoch,&ns);
        text.line("S%u ms=%llu v=%u/%u x=%u d=%u\n",i,(unsigned long long)(ns/1000000),s.parsed,r.valid,r.overflow,r.depthLimited);
        if(!s.parsed || !r.valid){text.line("R%u snapshot-unavailable\n",i);continue;}
        const auto &p=s.processes[3+instance];
        if(s.lsdInstances>2 || p.matches!=1 || !p.n){text.line("R%u lsd-unavailable/ambiguous\n",i);continue;}
        const auto *root=cdx22_root(p,ordinal);
        if(!root){text.line("R%u no-typed-root kept=%u total=%u\n",i,p.n,p.total);continue;}
        text.line("R%u p=%u t=%llx w=%u o=%llx\n",i,p.pid,(unsigned long long)root->tid,root->kind,(unsigned long long)root->owner);
        const char *why="unavailable";const auto *o=cdx22_follow(r,*root,hop,&why);
        if(!o){text.line("O%u %s\n",i,why);continue;}
        text.line("O%u p=%u t=%llx w=%u o=%llx\n",i,o->id.pid,(unsigned long long)o->tid,o->thread.kind,(unsigned long long)o->thread.owner);
        char comm[9]={};for(unsigned j=0;j<8 && o->id.comm[j];++j)comm[j]=o->id.comm[j];
        text.line("N%u %s u=%llx s=%u\n",i,comm,(unsigned long long)o->id.unique,o->source);
        cdx22_frames(text,i,o->thread,frame);
        omitted+=r.n?r.n-1:0;if(p.total)omitted+=p.total-1;
    }
    text.footer(omitted,false);
}

extern "C" void ipc_mqueue_receive_continue(void);
static void cdx23_port(Cdx15Text &text,unsigned i,const cdx19::Sample &s,const cdx19::Thread &t){
    if(t.kind!=2 || !t.wait)return;
    text.line("R%u w=%llx c=%llx n=%u\n",i,(unsigned long long)t.wait,(unsigned long long)t.continuation,s.ntasks);
    if(t.continuation!=(uint64_t)(uintptr_t)&ipc_mqueue_receive_continue)return;
    for(unsigned base=8;base<=16;base+=8){
        uint64_t port=t.wait-base;
        for(unsigned off=0x30;off<=0x88;off+=8){
            uint64_t v=*(const volatile uint64_t *)(uintptr_t)(port+off);
            constexpr uint64_t mask=0x0000FFFFFFFFFFFFULL;
            for(unsigned k=0;k<s.ntasks;++k){
                if(s.tasks[k].task==v || (s.tasks[k].task&mask)==(v&mask)){
                    char comm[9]={};
                    for(unsigned j=0;j<8 && s.tasks[k].comm[j];++j)comm[j]=s.tasks[k].comm[j];
                    text.line("R%u rx=%u %s\n",i,s.tasks[k].pid,comm);
                    return;
                }
            }
        }
    }
    text.line("R%u none n=%u w=%llx\n",i,s.ntasks,(unsigned long long)t.wait);
}
static void cdx19_format(Cdx15Text &text,bool quiet,uint32_t copies,uint32_t retired){
    unsigned page=option("luming-display-stack-page");if(page==6){cdx22_format(text,quiet,copies,retired);return;}if(page==5){cdx21_format(text,quiet,copies,retired);return;}if(page>4)page=0;
    unsigned selected=option("luming-display-stack-thread");if(selected>7)selected=0;
    unsigned first=option("luming-display-stack-frame");if(first>28)first=28;
    unsigned step=option("luming-display-stack-step");if(step>28)step=28;
    text.line("CDX19 rev=22 pg=%u th=%u quiet=%u cp=%u ret=%u\n",page,selected,(unsigned)quiet,copies,retired);
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
        cdx23_port(text,i,s,t);
    }
    const auto &s=cdx19_samples[cdx19_taken==2?1:0];const auto &p=s.processes[page];
    const unsigned char *uuid=p.cacheValid?p.uuid:s.uuid;uint64_t slide=p.cacheValid?p.cacheSlide:s.cacheSlide;
    bool valid=s.parsed && (p.cacheValid || s.cacheValid);char hex[33]={};
    for(unsigned i=0;i<16;++i){const char digits[]="0123456789abcdef";hex[2*i]=digits[uuid[i]>>4];hex[2*i+1]=digits[uuid[i]&15];}
    text.line("cache=%u sl=%llx uuid=%s\n",(unsigned)valid,(unsigned long long)slide,hex);
    text.footer(missing,false);
}
