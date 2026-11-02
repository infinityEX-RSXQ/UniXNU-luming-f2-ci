// SPDX-License-Identifier: BSD-2-Clause-Patent
// Bounded observations only. Caller serializes access; no borrowed pointers retained.
namespace cdx17 {
struct Row {
    uint64_t client,first,last;
    uint32_t pid,key,kind,begun,ended,errors,status,inputs,outputs,hasPort;
    uint64_t scalar[3];uint32_t captured;
};
struct Active {uint64_t token,time;uint32_t row,kind;};
struct State {Row rows[64];Active active[32];uint64_t next;uint32_t used,drop;bool saturated;};
inline void inc(State &s,uint32_t &v){if(v==UINT32_MAX)s.saturated=true;else ++v;}
inline Active *find(State &s,uint64_t token,unsigned kind){
    if(token)for(auto &a:s.active)if(a.token==token && a.kind==kind)return &a;return nullptr;
}
inline uint64_t begin(State &s,uint64_t token,uint64_t client,uint32_t pid,
    uint32_t key,unsigned kind,bool port,uint64_t now){
    if(!client || !token)return 0;
    if(find(s,token,kind)){inc(s,s.drop);return 0;}
    Active *slot=nullptr;for(auto &a:s.active)if(!a.token){slot=&a;break;}
    if(!slot){inc(s,s.drop);return 0;}
    unsigned i=0;for(;i<s.used;++i)if(s.rows[i].client==client && s.rows[i].key==key && s.rows[i].kind==kind)break;
    if(i==s.used){if(s.used==64){inc(s,s.drop);return 0;}++s.used;
        s.rows[i]={};s.rows[i].client=client;s.rows[i].pid=pid;s.rows[i].key=key;s.rows[i].kind=kind;s.rows[i].first=now;}
    auto &r=s.rows[i];inc(s,r.begun);r.last=now;r.hasPort=port?1U:0U;
    *slot={token,now,i,kind};return token;
}
inline void arguments(State &s,uint64_t token,uint32_t inputs,uint32_t outputs,
    const uint64_t *values,unsigned count){
    auto *a=find(s,token,0);if(!a)return;auto &r=s.rows[a->row];
    r.inputs=inputs;r.outputs=outputs;r.captured=0;
    if(r.key!=6 && r.key!=72)return;
    if(values)for(unsigned i=0;i<count && i<3;++i){r.scalar[i]=values[i];++r.captured;}
}
inline void end(State &s,uint64_t token,unsigned kind,uint32_t status,uint64_t now){
    if(!token)return;auto *a=find(s,token,kind);if(!a){inc(s,s.drop);return;}
    auto &r=s.rows[a->row];inc(s,r.ended);if(status)inc(s,r.errors);r.status=status;r.last=now;*a={};
}
}
