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
