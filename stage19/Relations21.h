// SPDX-License-Identifier: BSD-2-Clause-Patent
// Bounded joins over validated COPIED kcdata; no live pointers or kernel locks.
namespace cdx21 {
using cdx19::u32;using cdx19::u64;using cdx19::Thread;
struct Identity {uint64_t tid,unique;uint32_t pid,state;char comm[32];};
struct Owner {uint64_t tid,firstWaiter;Identity id;Thread thread;uint32_t matches,found,source;};
struct Turn {uint64_t waiter,context,flags;int32_t label;uint32_t version;};
struct Label {int32_t id;uint32_t flags,domain;char name[64];};
struct Relations {
    Identity index[1024];Owner owners[24];
    uint32_t count,overflow,n,omitted,passes,valid,error,depthLimited;
    Turn turns[256];Label labels[64];uint32_t nt,nl,turnOverflow,labelOverflow;
};
// The same integer means a TID for an unfair lock, a local name for receive,
// and sometimes a PID for send. Never join an untyped owner.
inline const char *kind(const Thread &t){
    if(!t.waitinfo)return "absent";
    if(t.owner>=~uint64_t(0)-7)return "sentinel";
    if(!t.owner)return "unknown";
    if(t.kind==1 || t.kind==10 || t.kind==18)return "tid";
    if(t.kind==2)return "portname";
    if(t.kind==4)return "pid";
    return "opaque";
}
inline bool request(Relations &r,const Thread &t,uint32_t source=1){
    if(strcmp(kind(t),"tid"))return false;
    for(unsigned i=0;i<r.n;++i)if(r.owners[i].tid==t.owner){r.owners[i].source|=source;return false;}
    if(r.n==24){++r.omitted;return false;}
    auto &o=r.owners[r.n++];o.tid=t.owner;o.firstWaiter=t.tid;o.source=source;return true;
}
inline Owner *find(Relations &r,uint64_t tid){
    for(unsigned i=0;i<r.n;++i)if(r.owners[i].tid==tid)return &r.owners[i];return nullptr;
}
// Structural validation is supplied by cdx19::parse before this decoder runs.
// Still check every length/count read here, including skipped array elements.
inline bool scan(const void *buffer,size_t length,Relations &r,bool indexing){
    const auto *b=static_cast<const unsigned char *>(buffer);size_t at=0;
    Identity id={};Thread thread={};bool task=false,have=false,inside=false;int label=-1;bool labelScope=false;
    while(at<length){
        if(length-at<16)return false;
        uint32_t type=u32(b+at),size=u32(b+at+4);uint64_t flags=u64(b+at+8);
        if(size>length-at-16)return false;
        const auto *d=b+at+16;at+=16+size;
        if(type==0x13){if(size<4)return false;auto c=u32(d);
            if(c==0x903){task=false;id={};}if(c==0x904){have=false;inside=true;thread={};}
            if(c==0x934){label=-1;labelScope=true;}continue;}
        if(type==0x14){
            if(inside && have){
                id.tid=thread.tid;id.state=thread.state;
                if(indexing){if(r.count<1024)r.index[r.count++]=id;else ++r.overflow;}
                else if(auto *o=find(r,thread.tid)){
                    ++o->matches;if(o->matches==1){o->id=id;o->thread=thread;o->found=1;}
                    else o->found=0; // never pick one of duplicate TIDs
                }
            }
            inside=false;have=false;labelScope=false;label=-1;continue;
        }
        if(type==0x905){if(size<120)return false;id={};id.unique=u64(d);id.pid=u32(d+84);
            memcpy(id.comm,d+88,31);id.comm[31]=0;task=true;continue;}
        if(type==0x906){if(size<104 || !task || !inside)return false;
            thread.tid=u64(d);thread.wait=u64(d+8);thread.continuation=u64(d+16);
            thread.flags=u64(d+64);thread.state=u32(d+88);have=true;continue;}
        if(indexing && type==0x935 && labelScope){
            if(size<5)return false;
            if(r.nl==64){++r.labelOverflow;continue;}
            label=int(r.nl++);auto &l=r.labels[label];int16_t v;uint16_t f;
            memcpy(&v,d,2);memcpy(&f,d+2,2);l.id=v;l.flags=f;l.domain=d[4];continue;
        }
        if(indexing && type==0x936 && labelScope && label>=0){
            unsigned j=0;for(;j<size && j<63 && d[j];++j)r.labels[label].name[j]=char(d[j]);
            r.labels[label].name[j]=0;continue;
        }
        if(type!=0x11 && !(type>=0x20 && type<=0x2f))continue;
        uint32_t elem=uint32_t(flags>>32),count=uint32_t(flags);size_t step=0,bytes=0;
        if(type==0x11){
            if(elem==0x90b || elem==0x90d)step=16;else if(elem==0x914 || elem==0x916)step=8;else continue;
            if(count>size/step || size-size_t(count)*step>=16)return false;
        }else{
            unsigned pad=type&15;if(pad>size)return false;bytes=size-pad;
            if(!count){if(bytes)return false;continue;}
            if(bytes%count)return false;step=bytes/count;if(!step)return false;
        }
        if(!indexing && inside && have && find(r,thread.tid) &&
           (elem==0x90b || elem==0x90d || elem==0x914 || elem==0x916)){
            size_t need=(elem==0x90b || elem==0x90d)?16:8;if(step!=need)return false;
            bool k=elem==0x90b || elem==0x914;unsigned limit=k?4:32,n=count<limit?count:limit;
            for(unsigned j=0;j<n;++j)(k?thread.k:thread.u)[j]=u64(d+size_t(j)*step);
            if(k)thread.nk=count;else thread.nu=count;
        }
        if(!indexing && elem==0x91d){
            if(step!=25 && step!=31)return false;
            for(unsigned j=0;j<count;++j){const auto *w=d+size_t(j)*step;
                if(auto *o=find(r,u64(w+8))){auto &t=o->thread;
                    t.waitinfo=1;t.owner=u64(w);t.context=u64(w+16);t.kind=w[24];t.waitbytes=uint32_t(step);
                    if(step==31){int16_t label;memcpy(&label,w+25,2);t.portlabel=label;t.waitflags=u32(w+27);}
                }
            }
        }
        if(indexing && elem==0x929){
            if(step!=26 && step!=28)return false;
            for(unsigned j=0;j<count;++j){const auto *w=d+size_t(j)*step;
                if(r.nt==256){++r.turnOverflow;continue;}
                auto &t=r.turns[r.nt++];t.waiter=u64(w);t.context=u64(w+8);t.flags=u64(w+18);
                t.version=uint32_t(step);t.label=0;
                if(step==28){int16_t l;memcpy(&l,w+26,2);t.label=l;}
            }
        }
    }
    return at==length;
}
inline bool turnRequest(Relations &r,uint64_t waiter){
    for(unsigned i=0;i<r.nt;++i){const auto &t=r.turns[i];
        if(t.waiter==waiter && (t.flags&8) && !(t.flags&(1|2|4|16|32))){
            Thread synthetic={};synthetic.tid=waiter;synthetic.waitinfo=1;synthetic.kind=10;synthetic.owner=t.context;return request(r,synthetic,2);
        }
    }return false;
}
inline bool collect(const void *b,size_t n,const cdx19::Sample &s,Relations &r){
    // These stores target static storage. Aggregate assignment at -O0 can
    // materialize an 82KiB temporary on the small kernel thread stack.
    memset(&r,0,sizeof(r));if(!s.parsed){r.error=1;return false;}
    if(!scan(b,n,r,true)){r.error=2;return false;}
    // lsd waits first, followed by the other targets; capacity omissions explicit.
    const unsigned order[]={3,4,1,0,2};
    for(unsigned p:order){const auto &proc=s.processes[p];if(proc.matches!=1 || (p>=3 && s.lsdInstances>2))continue;
        for(unsigned i=0;i<proc.n;++i){request(r,proc.threads[i]);turnRequest(r,proc.threads[i].tid);}}
    for(unsigned depth=0;depth<3;++depth){
        unsigned before=r.n;
        for(unsigned i=0;i<r.n;++i){r.owners[i].matches=0;r.owners[i].found=0;r.owners[i].thread={};}
        if(!scan(b,n,r,false)){r.error=3;return false;}++r.passes;
        // Append only after completing this scan, so task order cannot affect it.
        for(unsigned i=0;i<before;++i)if(r.owners[i].found){request(r,r.owners[i].thread);turnRequest(r,r.owners[i].tid);}
        if(r.n==before){r.valid=1;return true;}
    }
    r.depthLimited=1;r.valid=1;return true;
}
}
