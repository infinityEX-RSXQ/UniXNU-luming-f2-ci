// The production headers compile against a minimal IOKit interface fixture.
#include <stdint.h>
#include <stddef.h>
#ifndef CDX15_ABI_ONLY
#include <stdio.h>
#include <string.h>
#include <assert.h>
#else
extern "C" int vsnprintf(char *,size_t,const char *,__builtin_va_list);
extern "C" int snprintf(char *,size_t,const char *,...);
extern "C" void *memcpy(void *,const void *,size_t);
extern "C" int strcmp(const char *,const char *);
#endif
static unsigned depth;static uint64_t ticks=1000000,threadID=7;
static void unlocked(){
    (void)depth;
#ifndef CDX15_ABI_ONLY
    assert(!depth);
#endif
}
struct IOSimpleLock {};static IOSimpleLock lockObject;
typedef unsigned IOInterruptState;
static IOSimpleLock *IOSimpleLockAlloc(){unlocked();return &lockObject;}
static IOInterruptState IOSimpleLockLockDisableInterrupt(IOSimpleLock *){
#ifndef CDX15_ABI_ONLY
    assert(!depth);
#endif
    ++depth;return 0;
}
static void IOSimpleLockUnlockEnableInterrupt(IOSimpleLock *,IOInterruptState){--depth;}
typedef int IOReturn;
struct MockProc {int pid;const char *name;};typedef MockProc *proc_t;typedef MockProc *task_t;
static void *get_bsdtask_info(task_t t){unlocked();return t;}
static int proc_pid(proc_t p){unlocked();return p->pid;}
static const char *processName="backboardd";
static int proc_name(int,char *p,int n){unlocked();return snprintf(p,(size_t)n,"%s",processName);}
static uint64_t mach_absolute_time(){return ++ticks;}
static void *current_thread(){return reinterpret_cast<void *>(threadID);}
static void absolutetime_to_nanoseconds(uint64_t t,uint64_t *ns){*ns=t*1000000;}
static unsigned traceOverride=1;
static unsigned wait18=0;static unsigned page17=2;static unsigned option(const char *s){return !strcmp(s,"luming-display-wait-probe")?wait18:!strcmp(s,"luming-display-ipc-page")?page17:1;}
static void PE_parse_boot_argn(const char *,void *p,size_t){*(unsigned *)p=traceOverride;}
struct IOUserClient {uint64_t id;uint64_t getRegistryEntryID(){unlocked();return id;}};
struct IOMemoryMap {
    void *data;uint64_t length;unsigned refs;
    void retain(){unlocked();++refs;}
    uintptr_t getVirtualAddress(){unlocked();return reinterpret_cast<uintptr_t>(data);}
    uint64_t getLength(){unlocked();return length;}
};
struct OSDictionary {const char *name;void release(){unlocked();}};
struct MockMeta {const char *name;const char *getClassName(){return name;}};
static unsigned presentMask=3;static bool dictionaryFailure;
struct IOService {
    MockMeta meta;
    static OSDictionary *serviceMatching(const char *s){unlocked();static OSDictionary d;
        if(dictionaryFailure)return nullptr;d.name=s;return &d;}
    static IOService *copyMatchingService(OSDictionary *d){unlocked();static IOService s;
        unsigned bit=!strcmp(d->name,"IOWatchdog")?1:!strcmp(d->name,"AppleKeyStore")?2:4;
        if(!(bit&presentMask))return nullptr;s.meta.name=d->name;return &s;}
    MockMeta *getMetaClass(){return &meta;}void release(){unlocked();}
};
struct OSData {static OSData *withBytes(const void *,size_t){unlocked();static OSData d;return &d;}
    void release(){unlocked();}};
struct Active {void setProperty(const char *,OSData *){unlocked();}};static Active activeObject;
static Active *activeLegacyDisplay=&activeObject;
#include "TraceModel15.h"
#include "Text15.h"
#include "FrameSamples14.fixture.h"
struct Daemon {unsigned count,pid,ns;uint64_t code;};static Daemon cdx14_daemons[4];
struct Exception {unsigned count,type;uint64_t c0,c1;};static Exception cdx14_exceptions[4];
extern "C" {
#include "daemon15.fixture.h"
}
struct IOExternalMethodArguments {const uint64_t *scalarInput;uint32_t scalarInputCount,scalarOutputCount;};
#include "Adapter18.fixture.h"

#ifndef CDX15_ABI_ONLY
static void linesBounded(const char *p){const char *at=p;while(*at){const char *end=strchr(at,'\n');assert(end);assert(end-at<88);at=end+1;}}
static void textTests(){
    for(size_t n=0;n<700;++n){char b[704];memset(b,'X',sizeof b);Cdx15Text t(b,n);
        for(unsigned j=0;j<30;++j)t.line("sample=%u\n",j);t.line("missing-newline");
        t.footer(UINT32_MAX,true);assert(b[n]=='X');if(n)assert(memchr(b,0,n));}
    char b[160];Cdx15Text t(b,sizeof b);char longLine[100];memset(longLine,'a',99);longLine[99]=0;
    assert(!t.line("%s\n",longLine));assert(!t.line("no newline"));assert(t.line("ok\n"));
    t.footer(2,false);assert(strstr(b,"omit=2 drop=2 clip=0"));linesBounded(b);
}
static void modelTests(){
    cdx15::State s={};cdx15::open(s,1,26,"SpringBoard",0,0,1);cdx15::open(s,2,58,"backboardd",0,0,2);
    auto a=cdx15::begin(s,1,7,4,3);auto b=cdx15::begin(s,2,7,5,4);
    cdx15::validate(s,100,7,true,0,5);assert(cdx15::request(s,100)->pid==58);
    cdx15::end(s,b,0,6);cdx15::validate(s,101,7,true,0,7);assert(cdx15::request(s,101)->pid==26);
    cdx15::validate(s,102,8,true,0,8);assert(cdx15::request(s,102)->pid==0 && s.unknown==1);
    cdx15::end(s,a,7,9);assert(s.ipcError==1 && s.linked==2);
    cdx15::head(s,100,10);cdx15::head(s,100,11);assert(s.head==1 && s.first[2]==10);
    cdx15::copied(s,100,5,12);assert(!s.copy);cdx15::copied(s,100,0,13);assert(s.copy==1);
    auto gen=cdx15::retireBegin(s,100);cdx15::retireEnd(s,100,gen,14);assert(!cdx15::request(s,100));
    cdx15::validate(s,100,99,true,0,15);auto next=cdx15::request(s,100)->generation;assert(next!=gen);
    cdx15::retireEnd(s,100,gen,16);assert(cdx15::request(s,100)->generation==next);
    cdx15::validate(s,100,99,false,4,17);assert(!cdx15::request(s,100) && s.reject==1);
    // Completion may validate a reused address before the old completion returns.
    cdx15::validate(s,100,99,true,0,18);auto before=cdx15::retireBegin(s,100);
    cdx15::validate(s,100,99,true,0,19);auto during=cdx15::request(s,100)->generation;
    assert(before!=during);cdx15::retireEnd(s,100,before,20);assert(cdx15::request(s,100)->generation==during);
    cdx15::vsync(s,0,60,18);assert(s.armed && s.wanted);
    cdx15::vsync(s,8,60,19);assert(!s.armed);cdx15::vsync(s,1,60,20);assert(s.vsync==1 && s.lastVsync==20);
    cdx15::vsync(s,7,60,21);assert(s.armed);cdx15::vsync(s,2,60,22);assert(!s.armed && !s.wanted);
    cdx15::vsync(s,3,60,23);assert(s.late==1);
    for(unsigned i=0;i<20;++i)cdx15::open(s,1000+i,i,"verylongprocessnametruncated",0,0,24+i);
    assert(s.drop==6 && !cdx15::client(s,1) && cdx15::client(s,1019));
    assert(strlen(cdx15::client(s,1019)->name)==16);
    cdx15::open(s,0,99,"failed",0,5,50);assert(!cdx15::client(s,0));
    cdx15::State full={};for(unsigned i=0;i<16;++i)assert(cdx15::begin(full,1,i+1,0,1));
    assert(!cdx15::begin(full,1,99,0,1) && full.drop==1);
    for(unsigned i=0;i<17;++i)cdx15::validate(full,i+1,99,true,0,1);assert(full.drop==2);
    for(unsigned i=0;i<100;++i)cdx15::event(full,9,i,0,0,i);assert(full.events[(full.eventCount-1)%64].value==99);
    full.copy=UINT32_MAX;cdx15::copied(full,1,0,3);assert(full.copy==UINT32_MAX && full.saturated);
}
static void adapterTests(){
    alignas(4) uint32_t pixels[8*12]={};for(auto &x:pixels)x=0xff123456;
    IOMemoryMap map={pixels,sizeof pixels,1};traceOverride=0;cdx15_mapping_observed(&map,8,8,48);assert(!cdx15_on());
    traceOverride=1;cdx15_mapping_observed(&map,8,8,48);assert(cdx15_on() && map.refs==2);
    MockProc p={58,"backboardd"};IOUserClient client={42},other={99};
    cdx15_client_open(&p,0,&client,0);assert(!cdx15_ipc_begin(&other,0));
    auto token=cdx15_ipc_begin(&client,5);assert(token);cdx15_validation((void *)100,true,0);
    cdx15_head((void *)100);cdx15_copy((void *)100,0);cdx15_target_observed();
    cdx15_retire_end((void *)100,cdx15_retire_begin((void *)100));cdx15_ipc_end(token,0);
    char out[660];cdx15_snapshot(out,sizeof out,true);assert(strstr(out,"eq=1"));
    cdx15_snapshot_busy=1;cdx15_snapshot(out,sizeof out,true);assert(strstr(out,"snapshot=busy"));cdx15_snapshot_busy=0;
    cdx15_snapshot(out,sizeof out,true);
    assert(strstr(out,"wd=1:IOWatchdog aks=1:AppleKeyStore"));assert(strstr(out,"cli p=58"));linesBounded(out);
    // Change a visible sampled pixel AFTER last copy; fresh late sampling must detect it.
    pixels[0]^=255;cdx15_snapshot(out,sizeof out,true);assert(strstr(out,"eq=0"));
    cdx15_snapshot(out,sizeof out,false);assert(strstr(out,"late=skip quiet=0"));
    presentMask=0;cdx15_snapshot(out,sizeof out,true);assert(strstr(out,"wd=0: aks=0:"));
    dictionaryFailure=true;cdx15_snapshot(out,sizeof out,true);assert(strstr(out,"wd=-1: aks=-1:"));dictionaryFailure=false;
    IOMemoryMap changed={pixels,sizeof pixels,1};cdx15_mapping_observed(&changed,8,8,48);
    cdx15_snapshot(out,sizeof out,true);assert(strstr(out,"map=0"));assert(changed.refs==1);
    for(auto &d:cdx14_daemons){d.count=UINT32_MAX;d.ns=UINT32_MAX;d.code=UINT64_MAX;}
    for(auto &e:cdx14_exceptions){e.type=UINT32_MAX;e.c1=UINT64_MAX;}
    for(unsigned i=0;i<20;++i)cdx15::open(cdx15_state,1000+i,UINT32_MAX,"longclientnamemax",UINT32_MAX,UINT32_MAX,1);
    cdx15_state.ipc=UINT32_MAX;cdx15_state.val=UINT32_MAX;cdx15_state.last[1]=9999999;
    cdx15_snapshot(out,sizeof out,true);linesBounded(out);assert(strlen(out)+39<700);
    assert(strstr(out,"clip=1") && strstr(out,"omit="));assert(map.refs==2 && !depth);
    for(size_t n=1;n<352;++n){char b[354];memset(b,'X',sizeof b);auto size=cdx15_daemon_summary(b,n);
        assert(size<n && b[size]==0 && b[n]=='X');}
}

static void time16Tests(){
    bool clipped=false;cdx16_epoch=1234000000;
    assert(cdx15_ms(0,clipped)==0 && !clipped);
    assert(cdx15_ms(cdx16_epoch+1234,clipped)==1234 && !clipped);
    assert(cdx15_ms(cdx16_epoch-1,clipped)==0 && clipped);cdx16_epoch=0;
}
static void pacing16Tests(){
    cdx16_vsync_observed(0,6,6,60);cdx16_vsync_observed(1,3,39,60);
    assert(cdx16_vsync.startReason==6 && cdx16_vsync.armReason==3);
    assert(cdx16_vsync.startAttempts==1 && cdx16_vsync.armAttempts==1);
    char out[660];cdx15_snapshot(out,sizeof out,true);linesBounded(out);assert(strstr(out,"vst=6 sa=1 ar=3 aa=1"));
}

static void test17(){
    cdx15_state={};cdx17_state={};cdx16_epoch=0;cdx15_map_changed=0;
    static uint32_t pixels[96]={};static IOMemoryMap map={pixels,sizeof pixels,1};
    cdx15_mapping=&map;cdx15_width=cdx15_height=8;cdx15_stride=48;
    MockProc proc={58,"backboardd"};IOUserClient client={91},other={123};
    cdx15_client_open(&proc,0,&client,0);
    uint64_t values[3]={1,2,3};IOExternalMethodArguments args={values,3,1};
    cdx17_ipc_arguments(0,reinterpret_cast<IOExternalMethodArguments *>(1));
    auto a=cdx15_ipc_begin(&client,6);auto b=cdx15_ipc_begin(&client,72);
    cdx17_ipc_arguments(a,&args);args.scalarInputCount=2;cdx17_ipc_arguments(b,&args);
    assert(cdx17_state.rows[0].captured==3 && cdx17_state.rows[1].captured==2);
    assert(cdx17_state.rows[0].scalar[2]==3);
    cdx15_ipc_end(a,0x123);assert(cdx17_state.rows[0].errors==1 && cdx17_state.rows[0].status==0x123);
    auto port=cdx17_port_begin(&client,5,1,1);assert(port);
    assert(!cdx17_port_begin(&other,5,0,1));cdx17_port_end(port,1,0);
    assert(cdx17_state.rows[2].kind==2 && cdx17_state.rows[2].hasPort);
    // Notifications and method tokens are independently correlated, including same numeric token.
    assert(!cdx17::find(cdx17_state,a,0) && cdx17::find(cdx17_state,b,0));
    char out[660];page17=0;cdx15_snapshot(out,sizeof out,true);linesBounded(out);
    assert(strstr(out,"p58 s6 n1 d1 f1 r123") && strstr(out,"p58 Q5 n1 d1 f0 r0 b1"));
    assert(strstr(out,"pending=1 portRPC=1") && strlen(out)+39<700);
    page17=1;cdx15_snapshot(out,sizeof out,true);assert(strstr(out,"a=1/2/3") && strstr(out,"pending p58 k0 s72"));
    cdx15_ipc_end(b,0);
    // No borrowed argument pointer survives the call. Short/null buffers are bounded.
    auto c=cdx15_ipc_begin(&client,6);args={values,0,0};cdx17_ipc_arguments(c,&args);
    assert(!cdx17_state.rows[0].captured);args={nullptr,UINT32_MAX,0};cdx17_ipc_arguments(c,&args);
    assert(!cdx17_state.rows[0].captured);cdx15_ipc_end(c,0);
    cdx17::State full={};for(unsigned i=0;i<32;++i)assert(cdx17::begin(full,i+1,91,58,i,0,false,1));
    assert(!cdx17::begin(full,100,91,58,100,0,false,1) && full.drop==1);
    for(unsigned i=0;i<32;++i)cdx17::end(full,i+1,0,0,2);
    for(unsigned i=32;i<64;++i){assert(cdx17::begin(full,i+1,91,58,i,0,false,1));cdx17::end(full,i+1,0,0,2);}
    assert(!cdx17::begin(full,101,91,58,101,0,false,1) && full.used==64);
    full.rows[0].begun=UINT32_MAX;assert(cdx17::begin(full,200,91,58,0,0,false,1));assert(full.saturated);
    cdx17_state=full;page17=0;cdx15_snapshot(out,sizeof out,true);linesBounded(out);
    assert(strlen(out)+39<700 && strstr(out,"omit=") && strstr(out,"clip=1"));
    assert(!depth);page17=2;
}

static void test18(){
    cdx18::State s={};Cdx18View a={1,1,1,0},b={1,2,0,1};
    auto x=cdx18::waitBegin(s,100,58,1,0x80000000,0,a);
    auto y=cdx18::waitBegin(s,100,58,2,0,50,a);
    auto d=cdx18::doneBegin(s,2,0xf,a);
    cdx18::waitEnd(s,y,0,b);cdx18::doneEnd(s,d,b);cdx18::waitEnd(s,x,0xe00002d5,b);
    assert(s.waits[0].id==1 && s.waits[0].status==0xe00002d5 && s.waits[1].status==0);
    assert(s.completions[0].raw32c==15 && s.completions[0].post.completed==2);
    cdx18::waitEnd(s,x,9,a);assert(s.unmatched==1 && s.waits[0].status==0xe00002d5);
    for(unsigned i=2;i<16;++i)assert(cdx18::waitBegin(s,0,0,i,0,0,a));
    assert(!cdx18::waitBegin(s,0,0,18,0,0,a) && s.lost==1);
    for(unsigned i=1;i<8;++i)assert(cdx18::doneBegin(s,i,0,a));
    assert(!cdx18::doneBegin(s,20,0,a) && s.lost==2);
    cdx18::State max={};max.next=UINT64_MAX;assert(!cdx18::waitBegin(max,0,0,0,0,0,a) && max.saturated);
    cdx18_state={};cdx15_state={};cdx15_enabled=1;
    MockProc proc={58,"backboardd"};IOUserClient client={91};cdx15_client_open(&proc,0,&client,0);
    auto t=cdx18_wait_begin(&client,1,0x80000000,0,&a);assert(t && cdx18_state.waits[0].pid==58);
    cdx18_wait_end(t,0xe00002d5,&b);assert(cdx18_state.waits[0].done);
    auto z=cdx18_done_begin(2,15,&a);cdx18_done_end(z,&b);
    auto u=cdx18_wait_begin(nullptr,2,0,0,&a);assert(u && !cdx18_state.waits[1].pid);
    char out[660];wait18=1;cdx15_snapshot(out,sizeof out,true);linesBounded(out);
    assert(strstr(out,"CDX18") && strstr(out,"i=1 f=80000000 t=0 r=e00002d5") && strstr(out,"c=1/2"));
    // Worst-width untrusted integers never overrun rows/buffer; omissions explicit.
    cdx18_state={};for(unsigned i=0;i<16;++i){cdx18_state.next=UINT64_MAX-40+i;
        auto t=cdx18::waitBegin(cdx18_state,UINT64_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,a);
        cdx18::waitEnd(cdx18_state,t,UINT32_MAX,b);}
    cdx15_snapshot(out,sizeof out,true);linesBounded(out);assert(strlen(out)<660 && strstr(out,"omit="));
    // Each individual worst-width line fits <=88 including newline.
    char row[700];Cdx15Text text(row,sizeof row);
    assert(text.line("W%llx p%u i=%x f=%x t=%x r=%x d=%u\n",(unsigned long long)UINT64_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,UINT32_MAX,1U));
    assert(text.line("W%llx v=%u/%u c=%x/%x h=%u/%u q=%u/%u\n",(unsigned long long)UINT64_MAX,1U,1U,UINT32_MAX,UINT32_MAX,1U,1U,1U,1U));
    assert(text.line("D%llx i=%x x=%x d=%u v=%u/%u c=%x/%x\n",(unsigned long long)UINT64_MAX,UINT32_MAX,UINT32_MAX,1U,1U,1U,UINT32_MAX,UINT32_MAX));
    wait18=0;assert(!depth);
}
int main(){time16Tests();textTests();modelTests();adapterTests();pacing16Tests();test17();test18();puts("Stage15 model, attribution, generation reuse, late sampling, locks, registry and text bounds PASS");}
#else
// Force code generation for the kernel adapter and all snapshot paths.
extern "C" void cdx15_fixture(IOMemoryMap *map,task_t task,IOUserClient *client){
    cdx15_mapping_observed(map,8,8,48);cdx15_client_open(task,0,client,0);
    auto token=cdx15_ipc_begin(client,5);cdx15_validation((void *)100,true,0);cdx15_head((void *)100);
    cdx15_copy((void *)100,0);cdx15_target_observed();cdx15_retire_end((void *)100,cdx15_retire_begin((void *)100));
    cdx15_ipc_end(token,0);cdx15_gate(127);cdx15_vsync(1,60);char out[660];cdx15_snapshot(out,sizeof out,true);
}
#endif
