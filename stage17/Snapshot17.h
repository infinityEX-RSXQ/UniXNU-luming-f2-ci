// SPDX-License-Identifier: BSD-2-Clause-Patent
// Same quiesce/late-sample boundary as Stage16. Dedicated IPC page, <=660B.
    cdx17::State &calls=cdx17_snapshot_state;
    irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);calls=cdx17_state;
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
    if(activeLegacyDisplay){OSData *data=OSData::withBytes(&calls,sizeof(calls));
        if(data){activeLegacyDisplay->setProperty("CDX17IPCState",data);data->release();}}
    unsigned page=option("luming-display-ipc-page");
    text.line("CDX17 pg=%u quiet=%u cp=%u ret=%u\n",page,(unsigned)quiet,state.copy,state.ret);
    text.line("ipc=%u end=%u err=%u loss=%u vst=%u ar=%u vs=%u\n",state.ipc,state.ipcEnd,state.ipcError,
        calls.drop,pacing.startReason,pacing.armReason,state.vsync);
    unsigned pending=0,ports=0;for(const auto &a:calls.active)if(a.token)++pending;
    for(unsigned i=0;i<calls.used;++i)if(calls.rows[i].kind)ports+=calls.rows[i].begun;
    text.line("pending=%u portRPC=%u rows=%u\n",pending,ports,calls.used);
    // n=entered,d=returned,f=nonzero returns,r=last return; P/Q=32/64-bit port RPC.
    unsigned shown=0,total=0;
    if(!page){
        for(unsigned i=0;i<calls.used;++i){const auto &r=calls.rows[i];++total;
            if(text.line("p%u %c%u n%u d%u f%u r%x b%u\n",r.pid,r.kind==1?'P':r.kind==2?'Q':'s',
                r.key,r.begun,r.ended,r.errors,r.status,r.hasPort))++shown;}
    }else{
        for(unsigned i=0;i<calls.used;++i){const auto &r=calls.rows[i];
            if(!r.kind && (r.key==6 || r.key==72)){++total;
                if(text.line("p%u s%u in%u out%u got%u\n",r.pid,r.key,r.inputs,r.outputs,r.captured))++shown;
                text.line("a=%llx/%llx/%llx\n",(unsigned long long)r.scalar[0],
                    (unsigned long long)r.scalar[1],(unsigned long long)r.scalar[2]);}}
        for(const auto &a:calls.active)if(a.token){const auto &r=calls.rows[a.row];++total;
            unsigned age=cdx15_ms(mach_absolute_time(),clipped)-cdx15_ms(a.time,clipped);
            if(text.line("pending p%u k%u s%u ms%u\n",r.pid,r.kind,r.key,age))++shown;}
    }
    text.footer(total-shown,clipped||calls.saturated||state.saturated);
    return;
