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
    assert(p.threads[0].nk==2 && p.threads[0].nu==2 && p.threads[0].u[0]==0x19f3d0009ULL);
    assert(p.wait==10 && p.unint==1 && !s.processes[1].seen);
    // Every truncated prefix must fail, not masquerade as an empty snapshot.
    for(size_t n=0;n<b.size();++n){cdx19::Sample x={};assert(!cdx19::parse(b.data(),n,x) && !x.parsed);}
    auto bad=b;w32(bad,4,0xfffffff0);s={};assert(!cdx19::parse(bad.data(),bad.size(),s));
    bad=b;bad.back()=1;s={};assert(!cdx19::parse(bad.data(),bad.size()-1,s));
    // Full-width malformed headers and deliberately invalid array divisors.
    for(unsigned i=0;i<500;++i){Bytes a(64);w32(a,0,0x59a25807);w32(a,16,0x20+(i&15));
        w32(a,20,32);w64(a,24,((uint64_t)0x91d<<32)|(i+1));s={};assert(!cdx19::parse(a.data(),a.size(),s));}
    // Missing matching container end and wrong root magic.
    bad=b;w32(bad,0,0x434f4d50);s={};assert(!cdx19::parse(bad.data(),bad.size(),s));
    assert(cdx19::rank(cdx19::Thread{})>cdx19::rank(cdx19::Thread{0,0,0,0x1000,{},{},0,0,0,0,0,0,0}));
    puts("PASS: kcdata bounds, padding, process names, priority, owners, stack arrays, cache identity, truncation");
}
#endif
