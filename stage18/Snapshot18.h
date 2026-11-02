    if(option("luming-display-wait-probe")==1){
        cdx18::State &s=cdx18_snapshot_state;
        irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);s=cdx18_state;
        IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
        if(activeLegacyDisplay){OSData *data=OSData::withBytes(&s,sizeof(s));
            if(data){activeLegacyDisplay->setProperty("CDX18WaitState",data);data->release();}}
        text.line("CDX18 quiet=%u cp=%u ret=%u waits=%u done=%u\n",(unsigned)quiet,state.copy,state.ret,s.nw,s.nc);
        text.line("lost=%u unmatched=%u seq=%llx boundary-samples\n",s.lost,s.unmatched,(unsigned long long)s.next);
        unsigned shown=0,total=2*s.nw+s.nc;
        // Completion rows first: values came from a live request before the
        // original completion; post contains only the provider object's words.
        for(unsigned i=0;i<s.nc;++i){const auto &r=s.completions[i];
            if(text.line("D%llx i=%x x=%x d=%u v=%u/%u c=%x/%x\n",
                (unsigned long long)r.token,r.id,r.raw32c,r.done,r.pre.valid,r.post.valid,r.pre.completed,r.post.completed))++shown;
        }
        for(unsigned i=0;i<s.nw;++i){const auto &r=s.waits[i];
            if(text.line("W%llx p%u i=%x f=%x t=%x r=%x d=%u\n",
                (unsigned long long)r.token,r.pid,r.id,r.flags,r.timeout,r.status,r.done))++shown;
            if(text.line("W%llx v=%u/%u c=%x/%x h=%u/%u q=%u/%u\n",(unsigned long long)r.token,r.pre.valid,r.post.valid,
                r.pre.completed,r.post.completed,r.pre.current,r.post.current,r.pre.queued,r.post.queued))++shown;
        }
        text.footer(total-shown,clipped||s.saturated||state.saturated);return;
    }
