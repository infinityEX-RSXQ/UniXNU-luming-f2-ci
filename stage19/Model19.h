// SPDX-License-Identifier: BSD-2-Clause-Patent
// Parses copied kcdata, never a live task/thread or a pointer from the snapshot.
// Layout/type values are checked against this build's pinned kern/kcdata.h.
namespace cdx19 {
struct Thread {
    uint64_t tid,wait,continuation,flags,k[4],u[32],owner,context;
    uint32_t state,nk,nu,kind,waitinfo,waitbytes,waitflags;int32_t portlabel;
};
struct Process {
    uint64_t unique,cacheSlide;uint32_t pid,seen,total,run,wait,unint,n,omitted,cacheValid;
    unsigned char uuid[16];Thread threads[8];uint32_t matches,otherpid;
};
struct Sample {
    uint64_t begin,end,flags,cacheSlide;uint32_t rc,bytes,parsed,error,stored,cacheValid;
    unsigned char uuid[16];Process processes[5];uint32_t lsdInstances;
};
inline uint32_t u32(const unsigned char *p){uint32_t v;memcpy(&v,p,4);return v;}
inline uint64_t u64(const unsigned char *p){uint64_t v;memcpy(&v,p,8);return v;}
inline int nameIndex(const unsigned char *p,size_t n){
    const char *names[]={"backboardd","SpringBoard","launchd","lsd"};
    for(unsigned i=0;i<4;++i){size_t j=0;while(j<n && names[i][j] && p[j]==(unsigned char)names[i][j])++j;
        if(j<n && !names[i][j] && !p[j])return (int)i;}
    return -1;
}
inline unsigned rank(const Thread &t){
    // Main thread first, then non-idle waiting threads. A rank is selection,
    // never a conclusion that the thread is hung or causing a display failure.
    return ((t.flags&0x2000)?16U:0U)+((t.state&1)?4U:0U)+((t.state&8)?2U:0U)+((t.flags&0x1000)?0U:1U);
}
inline void insert(Process &p,const Thread &t){
    ++p.total;if(t.state&4)++p.run;if(t.state&1)++p.wait;if(t.state&8)++p.unint;
    unsigned at=p.n;
    if(at==8){++p.omitted;at=7;if(rank(t)<=rank(p.threads[at]))return;}
    else ++p.n;
    while(at && rank(t)>rank(p.threads[at-1])){p.threads[at]=p.threads[at-1];--at;}
    p.threads[at]=t;
}
struct Scope {uint64_t id;uint32_t type;};
inline bool parse(const void *buffer,size_t length,Sample &s){
    const auto *b=static_cast<const unsigned char *>(buffer);size_t at=0;
    Scope scopes[8]={};unsigned depth=0;int proc=-1;bool inTask=false,inThread=false,haveThread=false,taskSnapshot=false;
    Thread thread={};
    auto bad=[&](unsigned why){s.error=why;return false;};
    if(!b || length<32 || u32(b)!=0x59a25807U)return bad(1);
    while(at<length){
        if(length-at<16)return bad(2);
        uint32_t type=u32(b+at),size=u32(b+at+4);uint64_t flags=u64(b+at+8);
        if(size>length-at-16)return bad(3);
        const auto *data=b+at+16;at+=16+(size_t)size;
        size_t useful=size;
        if(!(type>=0x20 && type<=0x2f) && (flags&0x80) && type!=0x13 && type!=0x14){
            unsigned pad=(unsigned)(flags&15);if(pad>size)return bad(4);useful-=pad;
        }
        if(type==0xf19158edU){if(depth || inThread || size || at!=length)return bad(5);
            s.parsed=1;return true;}
        if(type==0x13){
            if(useful<4 || depth==8)return bad(6);
            uint32_t container=u32(data);scopes[depth++]={flags,container};
            if(container==0x903){if(inTask || inThread)return bad(7);inTask=true;proc=-1;taskSnapshot=false;}
            if(container==0x904){if(inThread)return bad(8);inThread=true;haveThread=false;thread={};}
            continue;
        }
        if(type==0x14){
            if(!depth || scopes[depth-1].id!=flags)return bad(9);
            uint32_t container=scopes[--depth].type;
            if(container==0x904){
                if(!inThread)return bad(10);
                if(proc>=0 && haveThread)insert(s.processes[proc],thread);
                inThread=false;haveThread=false;
            }
            if(container==0x903){proc=-1;inTask=false;}
            continue;
        }
        if(type==0x905){
            if(useful<120 || !depth || scopes[depth-1].type!=0x903)return bad(11);
            // A second snapshot record inside one task scope is malformed.
            // Separate tasks may legitimately share comm; mark ambiguity and
            // never merge their threads or silently select a process by name.
            if(taskSnapshot)return bad(24);taskSnapshot=true;
            proc=nameIndex(data+88,32);
            if(proc==3){
                // Preserve two independent lsd task containers. Never merge
                // threads from same-comm tasks or infer a launchd domain.
                unsigned instance=s.lsdInstances++;
                if(instance<2)proc=3+(int)instance;
                else {proc=-1;continue;}
            }
            if(proc>=0){auto &p=s.processes[proc];++p.matches;
                if(p.seen){if(p.matches==2)p.otherpid=u32(data+84);proc=-1;continue;}
                p.seen=1;p.unique=u64(data);p.pid=u32(data+84);}
            continue;
        }
        if(type==0x906 && proc>=0){
            if(!inThread || useful<104 || haveThread)return bad(13);
            thread.tid=u64(data);thread.wait=u64(data+8);thread.continuation=u64(data+16);
            thread.flags=u64(data+64);thread.state=u32(data+88);haveThread=true;continue;
        }
        if(type==0x908 || type==0x943){
            if(useful<24)return bad(14);
            if(proc>=0){auto &p=s.processes[proc];p.cacheValid=1;p.cacheSlide=u64(data);memcpy(p.uuid,data+8,16);}
            else if(!inTask){s.cacheValid=1;s.cacheSlide=u64(data);memcpy(s.uuid,data+8,16);}
            continue;
        }
        if(type==0x11 || (type>=0x20 && type<=0x2f)){
            uint32_t element=(uint32_t)(flags>>32),count=(uint32_t)flags;size_t step=0,bytes=0;
            if(type==0x11){
                if(element==0x90b || element==0x90d)step=16;
                else if(element==0x914 || element==0x916)step=8;
                else continue; // obsolete unknown array types cannot be decoded
                if(count>size/step || size-(size_t)count*step>=16)return bad(15);bytes=(size_t)count*step;
            }else{
                unsigned pad=type&15;if(pad>size)return bad(16);bytes=size-pad;
                if(!count){if(bytes)return bad(17);continue;}
                if(bytes%count)return bad(18);step=bytes/count;if(!step)return bad(19);
            }
            if(proc>=0 && inThread && haveThread && (element==0x90b || element==0x90d || element==0x914 || element==0x916)){
                bool kernel=element==0x90b || element==0x914;
                size_t need=(element==0x90b || element==0x90d)?16:8;if(step!=need)return bad(20);
                unsigned limit=kernel?4:32,n=count<limit?count:limit;auto *out=kernel?thread.k:thread.u;
                for(unsigned j=0;j<n;++j)out[j]=u64(data+(size_t)j*step);
                if(kernel)thread.nk=count;else thread.nu=count;
            }
            if(proc>=0 && element==0x91d){
                if(step!=25 && step!=31)return bad(21);
                auto &p=s.processes[proc];
                for(unsigned j=0;j<count;++j){const auto *r=data+(size_t)j*step;uint64_t tid=u64(r+8);
                    for(unsigned n=0;n<p.n;++n)if(p.threads[n].tid==tid){auto &t=p.threads[n];
                        t.waitinfo=1;t.owner=u64(r);t.context=u64(r+16);t.kind=r[24];t.waitbytes=(uint32_t)step;
                        if(step==31){int16_t label;memcpy(&label,r+25,2);t.portlabel=label;t.waitflags=u32(r+27);}}}
            }
        }
    }
    return bad(22); // missing end marker; partial buffers are never success
}
}
