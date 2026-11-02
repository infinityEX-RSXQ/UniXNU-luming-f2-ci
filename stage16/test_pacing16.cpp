
#include <stdint.h>
#ifndef CDX15_ABI_ONLY
#include <assert.h>
#define CHECK(x) assert(x)
#else
#define CHECK(x) ((void)(x))
#endif
typedef int IOReturn;static const int kIOReturnSuccess=0;
struct OSObject {};
static unsigned hzArg=60,fail,reason[2],flagsSeen[2],attempt[2],allocs,releases,wakes,wantReads;
static bool wants;
static void PE_parse_boot_argn(const char *,void *out,unsigned){*(unsigned *)out=hzArg;}
static uint64_t mach_absolute_time(){return 1000;}
static void nanoseconds_to_absolutetime(uint64_t n,uint64_t *out){*out=n;}
static void native_legacy_vsync_observed(unsigned,unsigned){}
static void cdx16_vsync_observed(unsigned phase,unsigned why,unsigned flags,unsigned){reason[phase]=why;flagsSeen[phase]=flags;++attempt[phase];}
struct IOTimerEventSource {
    static IOTimerEventSource *timerEventSource(OSObject *,void (*)(OSObject *,IOTimerEventSource *)){
        ++allocs;static IOTimerEventSource t;return fail==7?nullptr:&t;}
    void wakeAtTime(uint64_t){++wakes;}void release(){++releases;}
};
struct IOWorkLoop {
    int addEventSource(IOTimerEventSource *){return fail==8?-1:0;}
    int runAction(IOReturn (*f)(OSObject *,void *,void *,void *,void *),OSObject *o){return f(o,nullptr,nullptr,nullptr,nullptr);}
};
class NativeLegacyDisplay:public OSObject {public:
    IOTimerEventSource *vsyncTimer=nullptr;bool primary=true,bootMapping=true,vsyncArmed=false;
    uint64_t vsyncNext=0,vsyncInterval=0;unsigned vsyncHz=0;
    bool vsyncWanted(){++wantReads;return wants;}
    IOWorkLoop *getWorkLoop(){static IOWorkLoop loop;return fail==6?nullptr:&loop;}
    static void vsyncFired(OSObject *,IOTimerEventSource *){}
    void armVsync() {
        unsigned flags=(vsyncTimer?1U:0U)|(primary?2U:0U)|(bootMapping?4U:0U);
        if(!vsyncTimer || vsyncArmed){cdx16_vsync_observed(1,!vsyncTimer?1U:2U,flags,vsyncHz);return;}
        bool wanted=vsyncWanted();flags|=32U|(wanted?16U:0U);
        if(!wanted){cdx16_vsync_observed(1,3,flags,vsyncHz);return;}
        vsyncArmed=true;vsyncNext=mach_absolute_time()+vsyncInterval;
        vsyncTimer->wakeAtTime(vsyncNext);native_legacy_vsync_observed(0,vsyncHz);
        cdx16_vsync_observed(1,4,flags,vsyncHz);
    }
    void startVsync() {
        unsigned hz=0;PE_parse_boot_argn("sheng-vsync",&hz,sizeof(hz));
        unsigned flags=(vsyncTimer?1U:0U)|(primary?2U:0U)|(bootMapping?4U:0U);
        if(!hz || hz>240 || !primary || !bootMapping || vsyncTimer){
            unsigned reason=!hz?1U:hz>240?2U:!primary?3U:!bootMapping?4U:5U;
            cdx16_vsync_observed(0,reason,flags,hz);return;
        }
        IOWorkLoop *loop=getWorkLoop();
        if(!loop){cdx16_vsync_observed(0,6,flags,hz);return;}
        flags|=8U;
        IOTimerEventSource *timer=IOTimerEventSource::timerEventSource(this,&NativeLegacyDisplay::vsyncFired);
        if(!timer){cdx16_vsync_observed(0,7,flags,hz);return;}
        if(loop->addEventSource(timer)!=kIOReturnSuccess){timer->release();cdx16_vsync_observed(0,8,flags,hz);return;}
        nanoseconds_to_absolutetime(1000000000ull/hz,&vsyncInterval);
        vsyncHz=hz;vsyncTimer=timer;native_legacy_vsync_observed(4,hz);
        cdx16_vsync_observed(0,9,flags|1U,hz);
        loop->runAction([](OSObject *owner,void *,void *,void *,void *)->IOReturn {
            static_cast<NativeLegacyDisplay *>(owner)->armVsync();return kIOReturnSuccess;
        },this);
    }

};
#ifndef CDX15_ABI_ONLY
static void reset(){hzArg=60;fail=0;reason[0]=reason[1]=flagsSeen[0]=flagsSeen[1]=attempt[0]=attempt[1]=allocs=releases=wakes=wantReads=0;wants=false;}
int main(){
    for(unsigned i=1;i<=9;++i){reset();NativeLegacyDisplay d;IOTimerEventSource existing;
        if(i==1)hzArg=0;if(i==2)hzArg=241;if(i==3)d.primary=false;if(i==4)d.bootMapping=false;
        if(i==5)d.vsyncTimer=&existing;if(i>=6 && i<=8)fail=i;
        d.startVsync();CHECK(reason[0]==i && attempt[0]==1);
        if(i<=6)CHECK(!allocs);if(i==7)CHECK(allocs==1 && !releases);if(i==8)CHECK(releases==1);
        if(i==9){CHECK(d.vsyncTimer && d.vsyncHz==60 && d.vsyncInterval==16666666 && !wakes);
            CHECK(reason[1]==3 && wantReads==1 && (flagsSeen[1]&32));
            wants=true;d.armVsync();CHECK(reason[1]==4 && wakes==1 && d.vsyncArmed && wantReads==2);
            d.armVsync();CHECK(reason[1]==2 && wakes==1 && wantReads==2);}
    }
    reset();NativeLegacyDisplay absent;absent.armVsync();CHECK(reason[1]==1 && !wantReads && !wakes);
}
#else
extern "C" unsigned pacing_fixture(NativeLegacyDisplay *d){d->startVsync();d->armVsync();return allocs+releases+wakes+wantReads+reason[0]+flagsSeen[0]+attempt[0];}
#endif
