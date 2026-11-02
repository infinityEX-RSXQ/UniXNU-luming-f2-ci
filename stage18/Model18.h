// SPDX-License-Identifier: BSD-2-Clause-Patent
// Value-only, bounded records. The adapter owns serialization.
struct Cdx18View {uint32_t valid,completed,current,queued;};
namespace cdx18 {
struct Wait {uint64_t token,client;uint32_t pid,id,flags,timeout,status,done;
    Cdx18View pre,post;};
struct Completion {uint64_t token;uint32_t id,raw32c,done;Cdx18View pre,post;};
struct State {Wait waits[16];Completion completions[8];uint64_t next;
    uint32_t nw,nc,lost,unmatched;bool saturated;};
inline void inc(State &s,uint32_t &v){if(v==UINT32_MAX)s.saturated=true;else ++v;}
inline uint64_t next(State &s){if(s.next==UINT64_MAX){s.saturated=true;inc(s,s.lost);return 0;}return ++s.next;}
inline uint64_t waitBegin(State &s,uint64_t client,uint32_t pid,uint32_t id,
    uint32_t flags,uint32_t timeout,const Cdx18View &pre){
    if(s.nw==16){inc(s,s.lost);return 0;}uint64_t token=next(s);if(!token)return 0;
    auto &r=s.waits[s.nw++];r={};r.token=token;r.client=client;r.pid=pid;
    r.id=id;r.flags=flags;r.timeout=timeout;r.pre=pre;return token;
}
inline void waitEnd(State &s,uint64_t token,uint32_t status,const Cdx18View &post){
    if(!token)return;for(auto &r:s.waits)if(r.token==token && !r.done){r.status=status;r.post=post;r.done=1;return;}
    inc(s,s.unmatched);
}
inline uint64_t doneBegin(State &s,uint32_t id,uint32_t raw32c,const Cdx18View &pre){
    if(s.nc==8){inc(s,s.lost);return 0;}uint64_t token=next(s);if(!token)return 0;
    auto &r=s.completions[s.nc++];r={};r.token=token;r.id=id;r.raw32c=raw32c;r.pre=pre;return token;
}
inline void doneEnd(State &s,uint64_t token,const Cdx18View &post){
    if(!token)return;for(auto &r:s.completions)if(r.token==token && !r.done){r.post=post;r.done=1;return;}
    inc(s,s.unmatched);
}
}
