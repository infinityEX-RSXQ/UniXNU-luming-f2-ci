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
