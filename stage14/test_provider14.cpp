#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <assert.h>
#include <string>
#include <vector>
#include <stdexcept>
#include "FrameSamples14.h"
static unsigned probe=1,latch=1,snapshot=0,commits=0,scheduled=0,published=0;
static unsigned option(const char *name) {
    if(!strcmp(name,"luming-display-frame-probe"))return probe;
    if(!strcmp(name,"luming-display-vt-latch"))return latch;
    if(!strcmp(name,"luming-display-snapshot"))return snapshot;
    return 0;
}
struct OSData {static OSData *withBytes(const void *,size_t){return new OSData;}void release(){delete this;}};
struct Service {bool setProperty(const char *,OSData *){++published;return true;}};
static Service service,*activeLegacyDisplay=&service;
static std::string logs;
static void IOLog(const char *fmt,...) {char b[512];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);logs+=b;}
[[noreturn]] static void panic(const char *fmt,...) {char b[2048];va_list a;va_start(a,fmt);vsnprintf(b,sizeof b,fmt,a);va_end(a);throw std::runtime_error(b);}
extern "C" void cdx14_console_commit(void){++commits;}
extern "C" void cdx14_console_snapshot(unsigned *o){o[0]=commits?1:0;o[1]=0;o[2]=1;o[3]=2;o[4]=0;}
extern "C" size_t cdx14_daemon_summary(char *b,size_t n){return snprintf(b,n,"watchdogd n=2 ns=2 code=5\n");}
extern "C" size_t cdx14_exception_summary(char *b,size_t n){return snprintf(b,n,"watchdogd e=6 c0=1 c1=1234\n");}
typedef void *thread_call_param_t;
typedef void (*thread_call_func_t)(thread_call_param_t,thread_call_param_t);
static thread_call_func_t saved_callback;
typedef void *thread_call_t;
static thread_call_t thread_call_allocate(thread_call_func_t f,void *){saved_callback=f;return &saved_callback;}
static void thread_call_enter_delayed(thread_call_t,uint64_t){++scheduled;}
static void clock_interval_to_deadline(unsigned n,unsigned units,uint64_t *d){*d=(uint64_t)n*units;}
#define NSEC_PER_SEC 1000000000U
static unsigned native_legacy_swap_validation_calls=2,native_legacy_swap_validation_result=1,
    native_legacy_transfer_calls=2,native_legacy_retirement_calls=2,native_legacy_vsync_count=900;
static int native_legacy_transfer_status=0;
static uint64_t native_legacy_transfer_bytes=13596000;
#include "ProviderProbe14.h"
int main() {
    alignas(4) uint32_t src[8*10]={},dst[8*11]={};
    for(unsigned y=0;y<8;++y)for(unsigned x=0;x<8;++x)src[y*10+x]=0xff000000U+y*8+x;
    auto begin=[&](){cdx14_frame_begin(dst,sizeof dst,44,src,sizeof src,40,8,8);};
    auto copy=[&](){for(unsigned y=0;y<8;++y)memcpy(dst+y*11,src+y*10,32);};
    Cdx14Samples a={},b={};assert(cdx14_samples(src,sizeof src,40,8,8,&a));
    assert(!cdx14_samples(src,40,40,8,8,&b));assert(!cdx14_samples(src,sizeof src,31,8,8,&b));
    assert(!cdx14_samples(src,sizeof src,40,0,8,&b));
    begin();copy();cdx14_frame_end(true);
    assert(cdx14_frame.valid && !cdx14_frame.copyMismatch && !cdx14_frame.sourceChanged);
    assert(cdx14_frame.srcHash==cdx14_frame.dstAfter && published==1);
    // Corrupt a visible destination sample between our frames.
    dst[0]^=1;begin();assert(cdx14_frame.betweenMismatch==1);copy();cdx14_frame_end(true);
    assert(!cdx14_frame.copyMismatch);
    // Source changes while a CPU frame is being copied: do not blame VT.
    begin();copy();src[0]^=8;cdx14_frame_end(true);
    assert(cdx14_frame.sourceChanged==1 && !cdx14_frame.copyMismatch);
    begin();copy();dst[7]^=2;cdx14_frame_end(true);assert(cdx14_frame.copyMismatch==1);
    // Blank swap/gap invalidates any intervening writer inference.
    cdx14_frame_gap();dst[0]^=4;begin();assert(!cdx14_frame.betweenMismatch);
    copy();cdx14_frame_end(false);assert(!cdx14_frame.valid && !cdx14_has_previous);
    probe=0;uint64_t seq=cdx14_frame.sequence;begin();assert(cdx14_frame.sequence==seq);probe=1;
    unsigned due=0;for(unsigned i=1;i<=1000;++i)due+=cdx14_sample_due(i);assert(due==13);
    latch=0;cdx14_after_release();assert(!commits && !scheduled);
    latch=1;snapshot=1;cdx14_after_release();cdx14_after_release();assert(commits==2 && scheduled==1);
    try{saved_callback(nullptr,nullptr);assert(false);}catch(const std::runtime_error &e){
        assert(strstr(e.what(),"intentional") && strstr(e.what(),"watchdogd e=6") && strstr(e.what(),"bytes=13596000"));
    }
    puts("Stage14 provider: padded rows, mismatch/mutation/gap, bounded sampling, opt-in snapshot PASS");
}
