// SPDX-License-Identifier: BSD-2-Clause-Patent
#include <cstdint>
#include <cstring>
#include <cassert>
#include <vector>
#include <cstdio>
#include "Model19.h"
using Bytes=std::vector<unsigned char>;
static void w32(Bytes &b,size_t at,uint32_t v){assert(at+4<=b.size());memcpy(b.data()+at,&v,4);}
static void w64(Bytes &b,size_t at,uint64_t v){assert(at+8<=b.size());memcpy(b.data()+at,&v,8);}
static void item(Bytes &b,uint32_t type,const Bytes &payload={},uint64_t flags=0){
    size_t at=b.size();size_t size=(payload.size()+15)&~size_t(15);b.resize(at+16+size);
    w32(b,at,type);w32(b,at+4,(uint32_t)size);w64(b,at+8,flags);if(!payload.empty())memcpy(b.data()+at+16,payload.data(),payload.size());
}
static void begin(Bytes &b,uint32_t type,uint64_t id){Bytes p(4);w32(p,0,type);item(b,0x13,p,id);}
static void end(Bytes &b,uint64_t id){item(b,0x14,{},id);}
static void array(Bytes &b,uint32_t type,const Bytes &p,uint32_t count){
    unsigned pad=(unsigned)((16-p.size()%16)%16);item(b,0x20+pad,p,((uint64_t)type<<32)|count);
}
static Bytes fixture(){
    Bytes b;item(b,0x59a25807);Bytes cache(40);w64(cache,0,0x1000);cache[8]=0xab;item(b,0x908,cache);
    begin(b,0x903,10);Bytes p(120);w64(p,0,10);w32(p,84,583);memcpy(p.data()+88,"backboardd",11);item(b,0x905,p);
    for(unsigned i=0;i<10;++i){begin(b,0x904,100+i);Bytes t(104);
        w64(t,0,100+i);w64(t,8,0x1234567812345678ULL+i);w64(t,16,0xfffffff007123000ULL+i);
        w64(t,64,i==9?0x2000:(i<3?0x1000:0));w32(t,88,i==8?9:1);item(b,0x906,t);
        Bytes k(32);w64(k,0,0xfffffff007140000ULL+i);w64(k,16,0xfffffff007150000ULL+i);array(b,0x90b,k,2);
        Bytes u(16);w64(u,0,0x19f3d0000ULL+i);w64(u,8,0x19f3e0000ULL+i);array(b,0x916,u,2);end(b,100+i);
    }
    Bytes wi(31);w64(wi,0,200);w64(wi,8,109);w64(wi,16,0x5678);wi[24]=7;array(b,0x91d,wi,1);
    end(b,10);
    // A non-target process's cache must not overwrite global identity.
    begin(b,0x903,20);memset(p.data(),0,p.size());w32(p,84,99);memcpy(p.data()+88,"other",6);item(b,0x905,p);
    w64(cache,0,0x9000);cache[8]=0xff;item(b,0x908,cache);end(b,20);item(b,0xf19158ed);return b;
}
#ifndef CDX19_LIBRARY_ONLY
int main(){
    auto b=fixture(),copy=b;cdx19::Sample s={};assert(cdx19::parse(b.data(),b.size(),s));assert(b==copy);
    auto &p=s.processes[0];assert(s.parsed && !s.error && s.cacheSlide==0x1000 && s.uuid[0]==0xab);
    assert(p.seen && p.pid==583 && p.unique==10 && p.total==10 && p.n==8 && p.omitted==2);
    assert(p.threads[0].tid==109 && p.threads[0].waitinfo && p.threads[0].kind==7);
    assert(p.threads[0].owner==200 && p.threads[0].context==0x5678 && p.threads[0].state==1);
    assert(p.matches==1 && p.threads[0].waitbytes==31 && !p.threads[0].waitflags);
    assert(p.threads[0].nk==2 && p.threads[0].nu==2 && p.threads[0].u[0]==0x19f3d0009ULL);
    assert(p.wait==10 && p.unint==1 && !s.processes[1].seen);
    // Preserve 32 upper user LRs without changing the four-frame kernel bound.
    Bytes deep;item(deep,0x59a25807);begin(deep,0x903,5);Bytes dp(120);
    w64(dp,0,5);w32(dp,84,26);memcpy(dp.data()+88,"SpringBoard",12);item(deep,0x905,dp);
    begin(deep,0x904,99);Bytes dt(104);w64(dt,0,99);item(deep,0x906,dt);
    Bytes frames(40*8);for(unsigned j=0;j<40;++j)w64(frames,j*8,0x190000000+j*4);
    array(deep,0x916,frames,40);array(deep,0x914,frames,40);end(deep,99);end(deep,5);item(deep,0xf19158ed);
    cdx19::Sample ds={};assert(cdx19::parse(deep.data(),deep.size(),ds));auto &d=ds.processes[1].threads[0];
    assert(d.nu==40 && d.nk==40 && d.u[31]==0x19000007c && d.k[3]==0x19000000c);
    // Valid same-comm tasks: do not merge them, do not reject other processes.
    auto duplicates=b;duplicates.resize(duplicates.size()-16);begin(duplicates,0x903,30);
    Bytes task(120);w64(task,0,30);w32(task,84,777);memcpy(task.data()+88,"backboardd",11);
    item(duplicates,0x905,task);end(duplicates,30);begin(duplicates,0x903,31);
    w64(task,0,31);w32(task,84,26);memset(task.data()+88,0,32);memcpy(task.data()+88,"SpringBoard",12);
    item(duplicates,0x905,task);end(duplicates,31);item(duplicates,0xf19158ed);
    cdx19::Sample multi={};assert(cdx19::parse(duplicates.data(),duplicates.size(),multi));
    assert(multi.processes[0].matches==2 && multi.processes[0].otherpid==777);
    assert(multi.processes[0].total==10 && multi.processes[1].pid==26 && multi.processes[1].matches==1);
    // Two task snapshot records within one scope remain structurally invalid.
    Bytes invalid;item(invalid,0x59a25807);begin(invalid,0x903,31);
    item(invalid,0x905,task);item(invalid,0x905,task);end(invalid,31);item(invalid,0xf19158ed);
    cdx19::Sample twice={};assert(!cdx19::parse(invalid.data(),invalid.size(),twice) && twice.error==24);
    // Capture actual v2 special-reply flag and signed port-label ID.
    auto flagged=b;bool changed=false;
    for(size_t a=0;a<flagged.size();a+=16+cdx19::u32(flagged.data()+a+4)){
        if(cdx19::u32(flagged.data()+a)==0x21 && cdx19::u64(flagged.data()+a+8)>>32==0x91d){
            int16_t label=-1;memcpy(flagged.data()+a+16+25,&label,2);w32(flagged,a+16+27,1);changed=true;break;}}
    assert(changed);cdx19::Sample reply={};assert(cdx19::parse(flagged.data(),flagged.size(),reply));
    assert(reply.processes[0].threads[0].waitflags==1 && reply.processes[0].threads[0].portlabel==-1);
    // A v1 record never invents availability of v2-only fields.
    auto v1=b;
    for(size_t a=0;a<v1.size();a+=16+cdx19::u32(v1.data()+a+4)){
        if(cdx19::u32(v1.data()+a)==0x21 && cdx19::u64(v1.data()+a+8)>>32==0x91d){w32(v1,a,0x27);break;}}
    cdx19::Sample legacy={};assert(cdx19::parse(v1.data(),v1.size(),legacy));
    assert(legacy.processes[0].threads[0].waitbytes==25 && !legacy.processes[0].threads[0].waitflags);
    // Every truncated prefix must fail, not masquerade as an empty snapshot.
    for(size_t n=0;n<b.size();++n){cdx19::Sample x={};assert(!cdx19::parse(b.data(),n,x) && !x.parsed);}
    auto bad=b;w32(bad,4,0xfffffff0);s={};assert(!cdx19::parse(bad.data(),bad.size(),s));
    bad=b;bad.back()=1;s={};assert(!cdx19::parse(bad.data(),bad.size()-1,s));
    // Full-width malformed headers and deliberately invalid array divisors.
    for(unsigned i=0;i<500;++i){Bytes a(64);w32(a,0,0x59a25807);w32(a,16,0x20+(i&15));
        w32(a,20,32);w64(a,24,((uint64_t)0x91d<<32)|(i+1));s={};assert(!cdx19::parse(a.data(),a.size(),s));}
    // Missing matching container end and wrong root magic.
    bad=b;w32(bad,0,0x434f4d50);s={};assert(!cdx19::parse(bad.data(),bad.size(),s));
    assert(cdx19::rank(cdx19::Thread{})>cdx19::rank(cdx19::Thread{0,0,0,0x1000,{},{},0,0,0,0,0,0,0,0,0,0}));
    puts("PASS: kcdata bounds, padding, process names, priority, owners, stack arrays, cache identity, truncation");
}
#endif
