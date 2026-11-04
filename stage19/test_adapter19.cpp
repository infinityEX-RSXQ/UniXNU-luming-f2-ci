// SPDX-License-Identifier: BSD-2-Clause-Patent
#define CDX19_LIBRARY_ONLY
#include "test_model19.cpp"
#include <map>
#include <string>
#include <cstdlib>
#include <cstdarg>
using kern_return_t=int;
static unsigned enabled19=0,page19=0,calls19=0,fail19=0,frame19=0,step19=0,owner21=0,thread22=0;
static unsigned option(const char *s){return !strcmp(s,"luming-display-stackshot")?enabled19:!strcmp(s,"luming-display-stack-page")?page19:!strcmp(s,"luming-display-stack-frame")?frame19:!strcmp(s,"luming-display-stack-step")?step19:!strcmp(s,"luming-display-stack-owner")?owner21:!strcmp(s,"luming-display-stack-thread")?thread22:0;}
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
#include "Relations21.h"
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
        const char *name=i?"CDX19Raw1":"CDX19Raw0";assert(display.props[name]==fixture());
        assert(cdx21_saved[i] && display.props[i?"CDX21State1":"CDX21State0"].size()==sizeof(cdx21::Relations));}
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
        for(unsigned j=4;j<32;++j)t.u[j]=0x100030000+j;}
    frame19=4;Cdx15Text upper(out,sizeof(out));cdx19_format(upper,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"f=4 100030004/100030005/100030006/100030007"));
    frame19=8;step19=4;Cdx15Text pair(out,sizeof(out));cdx19_format(pair,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"U0 n=37 f=8 100030008/100030009/10003000a/10003000b"));
    assert(strstr(out,"U1 n=37 f=12 10003000c/10003000d/10003000e/10003000f") && !pair.dropped);
    frame19=999;step19=999;Cdx15Text clamp(out,sizeof(out));cdx19_format(clamp,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"f=28 10003001c/10003001d/10003001e/10003001f"));
    frame19=0;step19=0;
    cdx19_samples[0].processes[0].matches=2;cdx19_samples[0].processes[0].otherpid=777;
    Cdx15Text ambiguous(out,sizeof(out));cdx19_format(ambiguous,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"P0 ambiguous names=2 pid=583/777") && !strstr(out,"T0 id="));
    // Explicit lsd instance selection and overflow suppression.
    for(auto &sample:cdx19_samples){sample.lsdInstances=2;sample.processes[3]=sample.processes[0];sample.processes[3].matches=1;}
    page19=3;Cdx15Text lsd(out,sizeof(out));cdx19_format(lsd,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"target=lsd instance=1 domain=unknown") && !lsd.dropped);
    cdx19_samples[0].lsdInstances=3;Cdx15Text over(out,sizeof(out));cdx19_format(over,true,3,3);bounded(out,sizeof(out));
    assert(strstr(out,"lsd-overflow=1 unavailable") && !strstr(out,"T0 id="));
    page19=1;Cdx15Text missing(out,sizeof(out));cdx19_format(missing,true,2,2);bounded(out,sizeof(out));
    assert(strstr(out,"process=not-found"));
    // Both samples and all five target slots must fit in the actual 820B page.
    // Use maximum-width IDs, kinds and PCs; real IDs may be much shorter.
    for(unsigned i=0;i<2;++i){auto &s=cdx19_samples[i];s={};s.parsed=1;s.lsdInstances=2;s.begin=~uint64_t(0);
        for(auto &p:s.processes){p.n=1;p.total=32;p.matches=1;p.pid=~uint32_t(0);p.threads[0].kind=255;p.threads[0].owner=~uint64_t(0);}
        auto &r=cdx21_samples[i];r={};r.valid=1;r.n=2;r.overflow=262144;r.depthLimited=1;
        auto &o=r.owners[0];o.found=1;o.matches=1;o.tid=~uint64_t(0);o.id.pid=~uint32_t(0);o.source=3;o.thread.kind=255;o.thread.nu=~uint32_t(0);
        for(auto &pc:o.thread.u)pc=~uint64_t(0);}
    page19=5;Cdx15Text batch(out,sizeof(out));cdx19_format(batch,true,~uint32_t(0),~uint32_t(0));bounded(out,sizeof(out));
    assert(!batch.dropped && strstr(out,"L2 p=") && strstr(out,"S1 ms=") && strstr(out,"O1 p=") && strstr(out,"U1 n=") && strstr(out,"export=0 jobs=?"));
    puts(out);
    cdx21_samples[0].owners[0].thread.nu=0;cdx21_samples[1].owners[0].thread.nu=1;
    Cdx15Text noframes(out,sizeof(out));cdx19_format(noframes,true,3,3);bounded(out,sizeof(out));
    assert(!noframes.dropped && strstr(out,"U0 n=0 f=0 unavailable") && strstr(out,"U1 n=1 f=0 ffffffffffffffff/end"));
    owner21=99;Cdx15Text noslot(out,sizeof(out));cdx19_format(noslot,true,3,3);bounded(out,sizeof(out));assert(strstr(out,"slot=unavailable"));owner21=0,thread22=0;
    cdx19_samples[0].processes[0].matches=2;
    Cdx15Text batchamb(out,sizeof(out));cdx19_format(batchamb,true,3,3);assert(strstr(out,"BB unavailable/ambiguous"));

    // Stage22 follows typed roots, independent of owner array slot order.
    for(unsigned i=0;i<2;++i){auto &s=cdx19_samples[i];s={};s.parsed=1;s.lsdInstances=1;s.begin=~uint64_t(0);
      auto &p=s.processes[3];p.matches=1;p.pid=96;p.n=1;p.total=9;
      auto &t=p.threads[0];t.waitinfo=1;t.kind=18;t.tid=0x600;t.owner=0x2fc;
      auto &r=cdx21_samples[i];r={};r.valid=1;r.n=2;r.overflow=262144;r.depthLimited=1;
      auto &a=r.owners[1];a.found=a.matches=1;a.tid=0x2fc;a.source=1;a.id.pid=26;a.id.unique=~uint64_t(0);memcpy(a.id.comm,"SpringBoard",12);
      a.thread.waitinfo=1;a.thread.kind=1;a.thread.owner=0x888;a.thread.nk=4;a.thread.nu=37;
      a.thread.continuation=~uint64_t(0);for(auto &x:a.thread.k)x=~uint64_t(0);for(auto &x:a.thread.u)x=~uint64_t(0);
      auto &b=r.owners[0];b=a;b.tid=0x888;b.id.pid=200;b.thread.kind=2;b.thread.owner=0x903;}
    page19=6;Cdx15Text chain22(out,sizeof(out));cdx19_format(chain22,true,~uint32_t(0),~uint32_t(0));bounded(out,sizeof(out));
    assert(!chain22.dropped && strstr(out,"R0 p=96 t=600 w=18 o=2fc") && strstr(out,"O0 p=26 t=2fc w=1 o=888") && strstr(out,"K1 keep=2") && strstr(out,"U1 n=37"));puts(out);
    owner21=1;Cdx15Text hop22(out,sizeof(out));cdx19_format(hop22,true,3,3);assert(strstr(out,"O0 p=200 t=888 w=2 o=903"));
    owner21=2;Cdx15Text port22(out,sizeof(out));cdx19_format(port22,true,3,3);assert(strstr(out,"O0 next-not-tid"));
    owner21=0;cdx21_samples[0].owners[1].matches=2;Cdx15Text dup22(out,sizeof(out));cdx19_format(dup22,true,3,3);assert(strstr(out,"O0 ambiguous"));
    cdx21_samples[0].owners[1].matches=1;cdx21_samples[0].owners[1].thread.owner=0x2fc;owner21=1;
    Cdx15Text cycle22(out,sizeof(out));cdx19_format(cycle22,true,3,3);assert(strstr(out,"O0 cycle"));
    owner21=0;cdx19_samples[0].processes[3].threads[0].kind=2;
    Cdx15Text root22(out,sizeof(out));cdx19_format(root22,true,3,3);assert(strstr(out,"R0 no-typed-root"));
    cdx19_samples[0].lsdInstances=3;Cdx15Text amb22(out,sizeof(out));cdx19_format(amb22,true,3,3);assert(strstr(out,"R0 lsd-unavailable/ambiguous"));
    for(unsigned i=0;i<2;++i){auto &s=cdx19_samples[i];s.lsdInstances=1;auto &p=s.processes[3];p.pid=~uint32_t(0);p.total=~uint32_t(0);
      p.threads[0].kind=18;p.threads[0].tid=~uint64_t(0)-100;p.threads[0].owner=~uint64_t(0)-101;
      auto &o=cdx21_samples[i].owners[1];o.matches=1;o.tid=p.threads[0].owner;o.id.pid=~uint32_t(0);o.thread.owner=~uint64_t(0)-102;o.thread.nu=~uint32_t(0);}
    Cdx15Text max22(out,sizeof(out));cdx19_format(max22,true,~uint32_t(0),~uint32_t(0));bounded(out,sizeof(out));assert(!max22.dropped && strstr(out,"U1 n=4294967295"));
    page19=1;
    cdx19_taken=0;calls19=0;fail19=1;cdx19_samples[0]={};cdx19_samples[1]={};
    assert(cdx19_capture_next());assert(!cdx19_capture_next());assert(!cdx19_samples[0].parsed);
    Cdx15Text failed(out,sizeof(out));cdx19_format(failed,false,2,2);bounded(out,sizeof(out));assert(strstr(out,"stack=unavailable"));
    assert(!outstanding && !cdx19_busy);
    puts("PASS: default off, two calls only, real API return, raw ownership, bounded output, unavailable");
}
