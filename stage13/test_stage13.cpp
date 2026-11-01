#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <string>
#include <vector>
struct OSObject {unsigned refs=1;virtual ~OSObject(){};void retain(){++refs;}void release(){if(!--refs)delete this;}};
struct OSData:OSObject {
    std::vector<uint8_t> bytes;
    static bool failAllocate;
    static OSData *withBytes(const void *data,unsigned size){if(failAllocate)return nullptr;auto *p=new OSData;p->bytes.assign((const uint8_t *)data,(const uint8_t *)data+size);return p;}
    unsigned getLength(){return (unsigned)bytes.size();}const void *getBytesNoCopy(){return bytes.data();}
};bool OSData::failAllocate=false;
#define OSDynamicCast(T,x) dynamic_cast<T *>(x)
static const void *gIODTPlane=nullptr;
struct IORegistryEntry:OSObject {
    std::map<std::string,OSObject *> props;
    static IORegistryEntry *node;static unsigned calls,failOn;
    ~IORegistryEntry(){for(auto &entry:props)entry.second->release();}
    static IORegistryEntry *fromPath(const char *path,const void *){assert(!strcmp(path,"/chosen"));if(node)node->retain();return node;}
    OSObject *getProperty(const char *key){auto i=props.find(key);return i==props.end()?nullptr:i->second;}
    bool setProperty(const char *key,OSObject *value){if(++calls==failOn)return false;value->retain();removeProperty(key);props[key]=value;return true;}
    void removeProperty(const char *key){auto i=props.find(key);if(i!=props.end()){i->second->release();props.erase(i);}}
};IORegistryEntry *IORegistryEntry::node=nullptr;unsigned IORegistryEntry::calls=0,IORegistryEntry::failOn=0;
static unsigned selected=0;
static unsigned option(const char *name){assert(!strcmp(name,"luming-display-ui-scale"));return selected;}
static void IOLog(const char *,...){}
#include "UiScalePolicy.h"
static int copyError=0;
extern "C" int copyin(uint64_t address,void *out,size_t size){if(copyError)return copyError;memcpy(out,(const void *)(uintptr_t)address,size);return 0;}
#include "ModeSnapshot.h"
#include "ModeSummary13.h"
static uint32_t word(const char *key){auto *d=dynamic_cast<OSData *>(IORegistryEntry::node->getProperty(key));assert(d && d->getLength()==4);uint32_t v;memcpy(&v,d->getBytesNoCopy(),4);return v;}
static void put(const char *key,uint32_t value){auto *d=OSData::withBytes(&value,4);assert(IORegistryEntry::node->setProperty(key,d));d->release();}
static void reset(){if(IORegistryEntry::node)IORegistryEntry::node->release();IORegistryEntry::node=new IORegistryEntry;IORegistryEntry::calls=0;IORegistryEntry::failOn=0;OSData::failAllocate=false;selected=2;cdx13_ui_writes=0;cdx13_ui_readback=0;}
int main(){
    reset();assert(cdx13_publish_ui_scale(1236,2750));assert(word("display-scale")==2 && word("display-rotation")==0);assert(cdx13_ui_writes==2);
    assert(cdx13_publish_ui_scale(1236,2750) && cdx13_ui_writes==2); // matched values are not rewritten
    reset();put("display-scale",0);assert(cdx13_publish_ui_scale(1236,2750) && word("display-scale")==2);
    reset();put("display-scale",1);assert(!cdx13_publish_ui_scale(1236,2750) && word("display-scale")==1 && cdx13_ui_status==4);
    reset();put("display-rotation",1);assert(!cdx13_publish_ui_scale(1236,2750) && !IORegistryEntry::node->getProperty("display-scale"));
    reset();auto *bad=new OSObject;assert(IORegistryEntry::node->setProperty("display-scale",bad));bad->release();assert(!cdx13_publish_ui_scale(1236,2750) && cdx13_ui_status==3);
    reset();IORegistryEntry::failOn=2;assert(!cdx13_publish_ui_scale(1236,2750));assert(IORegistryEntry::node->props.empty()); // second write failure rolls back first
    reset();put("display-scale",0);IORegistryEntry::calls=0;IORegistryEntry::failOn=2;assert(!cdx13_publish_ui_scale(1236,2750) && word("display-scale")==0); // restore exact existing value
    reset();OSData::failAllocate=true;assert(!cdx13_publish_ui_scale(1236,2750) && IORegistryEntry::node->props.empty());OSData::failAllocate=false;
    reset();selected=0;assert(cdx13_publish_ui_scale(0,0) && IORegistryEntry::node->props.empty());selected=3;assert(!cdx13_publish_ui_scale(1236,2750));selected=2;assert(!cdx13_publish_ui_scale(1236,2748));
    reset();IORegistryEntry::node->release();IORegistryEntry::node=nullptr;assert(!cdx13_publish_ui_scale(1236,2750) && cdx13_ui_status==2);reset();
    // Actual Stage12 photo: only the zero pref + zero override fails these checks.
    assert(cdx13_publish_ui_scale(1236,2750));
    uint64_t object[9]={0,1236,2750,0,0,0x404e000000000000ULL,1,0,0};
    cdx12_capture_mode(26,(uintptr_t)object);cdx13_capture_validity(26,0);
    assert(cdx13_scalar_issues(object+1)==4);object[3]=2;assert(cdx13_scalar_issues(object+1)==0);object[3]=0;object[4]=0x4000000000000000ULL;assert(cdx13_scalar_issues(object+1)==0);
    object[4]=0;cdx12_capture_mode(26,(uintptr_t)object);char out[1024]={0};cdx13_append_mode_summary(26,out,sizeof(out));assert(strstr(out,"rb=404e000000000000") && strstr(out,"vcGot=1 vc=0 issues=4"));puts(out);
    char wrong[1024]={0};cdx13_append_mode_summary(99,wrong,sizeof(wrong));assert(strstr(wrong,"got=0") && strstr(wrong,"issues=ffffffff"));
    copyError=14;cdx12_capture_mode(26,(uintptr_t)object);char failed[1024]={0};cdx13_append_mode_summary(26,failed,sizeof(failed));assert(strstr(failed,"got=0 err=14"));copyError=0;
    __atomic_store_n(&cdx12_lock,1,__ATOMIC_RELEASE);char busy[256]={0};cdx13_append_mode_summary(26,busy,sizeof(busy));assert(strstr(busy,"busy=1"));__atomic_store_n(&cdx12_lock,0,__ATOMIC_RELEASE);
    struct {char out[16];char guard[8];} small;memset(&small,'Z',sizeof(small));small.out[0]=0;cdx13_append_mode_summary(26,small.out,sizeof(small.out));assert(strlen(small.out)<sizeof(small.out));for(char c:small.guard)assert(c=='Z');
    IORegistryEntry::node->release();IORegistryEntry::node=nullptr;puts("Stage13 policy, rollback, captured fields, and bounds: PASS");
}
