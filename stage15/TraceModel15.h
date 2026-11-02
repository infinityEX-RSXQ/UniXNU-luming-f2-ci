// SPDX-License-Identifier: BSD-2-Clause-Patent
// Caller holds the diagnostic spin lock. No kernel pointers are dereferenced.
namespace cdx15 {
struct Client {uint64_t id,serial,opened;uint32_t pid,type,status,ipc,validated;char name[17];};
struct Call {uint64_t token,thread,client;uint32_t selector;};
struct Request {uint64_t key,generation,client;uint32_t pid;bool head,retiring;};
struct Event {uint64_t time,request,client;uint32_t phase,value;};
struct State {
    Client clients[16];Call calls[16];Request requests[16];Event events[64];
    uint64_t serial,token,generation,eventCount,first[5],last[5],lastVsync;
    uint32_t ipc,ipcEnd,ipcError,val,head,copy,ret,reject,unknown,linked,drop;
    uint32_t gate,gateCount,vsync,arm,late,idle,hz;
    bool armed,wanted,saturated;
};
inline void inc(State &s,uint32_t &v){if(v!=UINT32_MAX)++v;else s.saturated=true;}
inline void name(char (&dst)[17],const char *src){unsigned i=0;if(src)for(;i<16 && src[i];++i)dst[i]=src[i];for(;i<17;++i)dst[i]=0;}
inline Client *client(State &s,uint64_t id){for(auto &x:s.clients)if(id && x.id==id)return &x;return nullptr;}
inline Request *request(State &s,uint64_t key){for(auto &x:s.requests)if(key && x.key==key)return &x;return nullptr;}
inline void event(State &s,uint32_t phase,uint64_t now,uint64_t req,uint64_t cli,uint32_t value){
    s.events[s.eventCount%64]={now,req,cli,phase,value};++s.eventCount;
}
inline void stamp(State &s,unsigned stage,uint64_t now){if(!s.first[stage])s.first[stage]=now;s.last[stage]=now;}
inline void open(State &s,uint64_t id,uint32_t pid,const char *comm,uint32_t type,uint32_t status,uint64_t now){
    Client *at=client(s,id);
    if(!at){at=&s.clients[0];for(auto &x:s.clients){if(!x.serial){at=&x;break;}if(x.serial<at->serial)at=&x;}}
    if(at->serial && (!id || at->id!=id))inc(s,s.drop);
    *at={};at->id=id;at->serial=++s.serial;at->opened=now;at->pid=pid;at->type=type;at->status=status;name(at->name,comm);
    event(s,0,now,0,id,status);
}
inline uint64_t begin(State &s,uint64_t id,uint64_t thread,uint32_t selector,uint64_t now){
    if(!id || !thread)return 0;
    for(auto &x:s.calls)if(!x.token){
        x={++s.token,thread,id,selector};inc(s,s.ipc);if(auto *c=client(s,id))inc(s,c->ipc);
        event(s,1,now,0,id,selector);return x.token;
    }
    inc(s,s.drop);return 0;
}
inline void end(State &s,uint64_t token,uint32_t status,uint64_t now){
    if(!token)return;
    for(auto &x:s.calls)if(x.token==token){inc(s,s.ipcEnd);if(status)inc(s,s.ipcError);
        event(s,2,now,0,x.client,status);x={};return;}
    inc(s,s.drop);
}
inline void validate(State &s,uint64_t key,uint64_t thread,bool accepted,uint32_t why,uint64_t now){
    inc(s,s.val);stamp(s,1,now);
    uint64_t id=0,latest=0;
    for(auto &c:s.calls)if(c.token && c.thread==thread && c.token>latest){latest=c.token;id=c.client;}
    auto *owner=client(s,id);if(owner){inc(s,s.linked);inc(s,owner->validated);}else inc(s,s.unknown);
    event(s,3,now,key,id,why);
    if(!accepted){inc(s,s.reject);if(auto *r=request(s,key))*r={};return;}
    if(!key){inc(s,s.drop);return;}
    if(auto *r=request(s,key)){
        if(r->retiring)*r={key,++s.generation,id,owner?owner->pid:0,false,false};
        return;
    }
    for(auto &r:s.requests)if(!r.key){r={key,++s.generation,id,owner?owner->pid:0,false,false};return;}
    inc(s,s.drop);
}
inline void head(State &s,uint64_t key,uint64_t now){
    auto *r=request(s,key);if(!r){inc(s,s.drop);return;}
    if(!r->head){r->head=true;inc(s,s.head);stamp(s,2,now);event(s,4,now,key,r->client,0);}
}
inline void copied(State &s,uint64_t key,uint32_t status,uint64_t now){
    if(!status){inc(s,s.copy);stamp(s,3,now);}
    auto *r=request(s,key);event(s,5,now,key,r?r->client:0,status);
}
inline uint64_t retireBegin(State &s,uint64_t key){auto *r=request(s,key);if(r)r->retiring=true;return r?r->generation:0;}
inline void retireEnd(State &s,uint64_t key,uint64_t generation,uint64_t now){
    inc(s,s.ret);stamp(s,4,now);auto *r=request(s,key);
    event(s,6,now,key,(r && r->generation==generation)?r->client:0,0);
    if(r && generation && r->generation==generation)*r={};
}
inline void gate(State &s,uint32_t bits){s.gate=bits;inc(s,s.gateCount);}
inline void vsync(State &s,unsigned ev,unsigned hz,uint64_t now){
    s.hz=hz;
    if(ev==0){inc(s,s.arm);s.armed=true;s.wanted=true;}
    if(ev==1){inc(s,s.vsync);s.lastVsync=now;s.wanted=true;}
    if(ev==2){inc(s,s.idle);s.armed=false;s.wanted=false;}
    if(ev==3)inc(s,s.late);
    if(ev==6)s.armed=false;
    if(ev==7)s.armed=true;
    if(ev==8)s.armed=false;
}
}
