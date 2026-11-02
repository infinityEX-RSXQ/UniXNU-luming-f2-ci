#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <assert.h>
typedef int IOReturn;
static constexpr int kIOReturnSuccess=0;
static bool diagnostic;static unsigned locks,reads,beginCount,endCount,baseCount;
static uint32_t inputId,inputFlags,inputTimeout;static IOReturn response=(int)0xe00002d5;
struct IOUserClient {};
struct OSObject {};
struct IOWorkLoop {
    bool inGate(){return locks!=0;}
    IOReturn runAction(IOReturn(*f)(OSObject *,void *,void *,void *,void *),OSObject *o,void *a){
        ++locks;++reads;auto r=f(o,a,nullptr,nullptr,nullptr);--locks;return r;
    }
};
static IOWorkLoop loop;
static void PE_parse_boot_argn(const char *,void *p,size_t){*(unsigned *)p=diagnostic;}
struct Cdx18View {uint32_t valid,completed,current,queued;};
static Cdx18View preSeen,postSeen;
extern "C" uint64_t cdx18_wait_begin(IOUserClient *,uint32_t id,uint32_t flags,uint32_t timeout,const Cdx18View *p){
    assert(!locks);++beginCount;assert(id==inputId && flags==inputFlags && timeout==inputTimeout);preSeen=*p;return 42;
}
extern "C" void cdx18_wait_end(uint64_t t,uint32_t rc,const Cdx18View *p){assert(!locks && t==42 && rc==(uint32_t)response);++endCount;postSeen=*p;}
struct IOMobileFramebufferLegacy: OSObject {
    unsigned char storage[0x1900]={};
    virtual IOReturn waitForSwap(IOUserClient *,uint32_t id,uint32_t flags,uint32_t timeout){
        assert(!locks);++baseCount;inputId=id;inputFlags=flags;inputTimeout=timeout;
        uint32_t completed=2;memcpy(reinterpret_cast<char *>(this)+0x16bc,&completed,4);return response;
    }
};
struct NativeLegacyDisplay: IOMobileFramebufferLegacy {
    bool hasLoop=true;
    IOWorkLoop *getWorkLoop(){return hasLoop?&loop:nullptr;}
#include "Backend18.h"
};
int main(){
    NativeLegacyDisplay n;IOUserClient client;inputId=1;inputFlags=0x80000000;inputTimeout=0;
    diagnostic=false;assert(n.waitForSwap(&client,inputId,inputFlags,inputTimeout)==response);
    assert(baseCount==1 && !reads && !beginCount && !endCount);
    uint32_t completed=1;memcpy(reinterpret_cast<char *>(&n)+0x16bc,&completed,4);
    diagnostic=true;assert(n.waitForSwap(&client,inputId,inputFlags,inputTimeout)==response);
    assert(baseCount==2 && beginCount==1 && endCount==1 && reads==2 && !locks);
    assert(preSeen.valid && preSeen.completed==1 && postSeen.valid && postSeen.completed==2);
    n.hasLoop=false;response=0;assert(n.waitForSwap(&client,inputId,inputFlags,inputTimeout)==response);
    assert(baseCount==3 && beginCount==2 && endCount==2 && !preSeen.valid && !postSeen.valid);
}
