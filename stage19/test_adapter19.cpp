// SPDX-License-Identifier: BSD-2-Clause-Patent
#define CDX19_LIBRARY_ONLY
#include "test_model19.cpp"
#include <map>
#include <string>
#include <cstdlib>
#include <cstdarg>
using kern_return_t=int;
static unsigned enabled19=0,page19=0,calls19=0,fail19=0,frame19=0;
static unsigned option(const char *s){return !strcmp(s,"luming-display-stackshot")?enabled19:!strcmp(s,"luming-display-stack-page")?page19:!strcmp(s,"luming-display-stack-frame")?frame19:0;}
static unsigned outstanding;
static void *IOMalloc(size_t n){++outstanding;return malloc(n);}
static void IOFree(void *p,size_t){--outstanding;free(p);}
static void bzero(void *p,size_t n){memset(p,0,n);}
static bool ml_at_interrupt_context(){return false;}
static bool ml_get_interrupts_enabled(){return true;}
static uint64_t mach_absolute_time(){return 15000000000ULL+(uint64_t)calls19*15000000000ULL;}
static void absolutetime_to_nanoseconds(uint64_t t,uint64_t *n){*n=t;}
static uint64_t cdx16_epoch=0;
struct OSData {
    Bytes data;
    static OSData *withBytes(const void *p,size_t n){auto *d=new OSData;d->data.resize(n);memcpy(d->data.data(),p,n);return d;}
    void release(){delete this;}
};
struct MockService {
    std::map<std::string,Bytes> props;
    bool setProperty(const char *s,OSData *d){props[s]=d->data;return true;}
};
static MockService display;
static MockService *activeLegacyDisplay=&display;
#include "Text15.fixture.h"
#include "Adapter19.h"
extern "C" kern_return_t stack_snapshot_from_kernel(int pid,void *p,uint32_t n,uint64_t flags,uint64_t delta,uint32_t pages,unsigned *used){
    assert(pid==-1 && flags==cdx19_flags && !delta && !pages && n==cdx19_capacity);
    assert(cdx19_busy==1);++calls19;if(fail19){*used=0;return 6;}
    auto b=fixture();assert(b.size()<n);memcpy(p,b.data(),b.size());*used=(unsigned)b.size();return 0;
}
static void bounded(const char *out,size_t n){assert(strlen(out)<n && strstr(out,"omit="));
    const char *p=out;while(*p){const char *e=strchr(p,'\n');assert(e && e-p+1<=88);p=e+1;}}
int main(){
    assert(!cdx19_capture_next() && !calls19);enabled19=1;
    assert(cdx19_capture_next());assert(cdx19_taken==1 && calls19==1 && !outstanding);
    assert(!cdx19_capture_next());assert(cdx19_taken==2 && calls19==2 && !outstanding);
    assert(!cdx19_capture_next() && calls19==2);
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];assert(!s.rc && s.parsed && s.stored && s.bytes);
        const char *name=i?"CDX19Raw1":"CDX19Raw0";assert(display.props[name]==fixture());}
    char out[820];Cdx15Text text(out,sizeof(out));cdx19_format(text,true,2,2);bounded(out,sizeof(out));
    assert(strstr(out,"P0 p=583") && strstr(out,"U0 n=2 f=0 19f3d0009") && strstr(out,"wt=1/7"));
    assert(strstr(out,"cache=1 sl=1000 uuid=ab000000") && strstr(out,"sc=unavailable"));
    puts(out);
    // More than two user LRs must fit and must reach the photographed text.
    for(auto &sample:cdx19_samples){auto &t=sample.processes[0].threads[0];
        t.nu=37;t.u[0]=0x1cb780b58;t.u[1]=0x1cb7841b0;t.u[2]=0x19f123456;t.u[3]=0x100012340;
        t.waitbytes=31;t.waitflags=1;t.portlabel=-1;t.kind=2;}
    Cdx15Text expanded(out,sizeof(out));cdx19_format(expanded,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"1cb780b58/1cb7841b0/19f123456/100012340"));
    assert(strstr(out,"W0 t=2 f=1 l=-1 owner="));assert(!expanded.dropped);
    for(auto &sample:cdx19_samples){auto &t=sample.processes[0].threads[0];
        for(unsigned j=4;j<8;++j)t.u[j]=0x100030000+j;}
    frame19=4;Cdx15Text upper(out,sizeof(out));cdx19_format(upper,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"f=4 100030004/100030005/100030006/100030007"));frame19=0;
    cdx19_samples[0].processes[0].matches=2;cdx19_samples[0].processes[0].otherpid=777;
    Cdx15Text ambiguous(out,sizeof(out));cdx19_format(ambiguous,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"P0 ambiguous names=2 pid=583/777") && !strstr(out,"T0 id="));
    page19=1;Cdx15Text missing(out,sizeof(out));cdx19_format(missing,true,2,2);bounded(out,sizeof(out));
    assert(strstr(out,"process=not-found"));
    cdx19_taken=0;calls19=0;fail19=1;cdx19_samples[0]={};cdx19_samples[1]={};
    assert(cdx19_capture_next());assert(!cdx19_capture_next());assert(!cdx19_samples[0].parsed);
    Cdx15Text failed(out,sizeof(out));cdx19_format(failed,false,2,2);bounded(out,sizeof(out));assert(strstr(out,"stack=unavailable"));
    assert(!outstanding && !cdx19_busy);
    puts("PASS: default off, two calls only, real API return, raw ownership, bounded output, unavailable");
}
