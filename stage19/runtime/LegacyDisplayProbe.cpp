// SPDX-License-Identifier: BSD-2-Clause-Patent
// Luming CPU GOP publication for the audited, unchanged 21H461 Legacy family.
// The original family supplies its IOService/user-client lifecycle. This file
// supplies only a real firmware memory resource and bounded observations.
#include <IOKit/IOPlatformExpert.h>
#include <IOKit/IODeviceMemory.h>
#include <IOKit/IODeviceTreeSupport.h>
#include <IOKit/IOLib.h>
#include <IOKit/IOUserClient.h>
#include <IOKit/IOMemoryDescriptor.h>
#include <libkern/c++/OSArray.h>
#include <libkern/c++/OSData.h>
#include <libkern/c++/OSMetaClass.h>
#include <kern/task.h>
#include <kern/thread.h>
#include <IOKit/IOLocks.h>
#include <kern/thread_call.h>
#include <kern/clock.h>
#include <sys/proc.h>
#include <pexpert/pexpert.h>
#include <mach/kmod.h>
#include <machine/machine_routines.h>

extern "C" kmod_info_t g_kernel_kmod_info;
extern "C" void native_legacy_display_static_init(void)
    __asm__("__GLOBAL__sub_I_NativeLegacyDisplay.cpp");
extern "C" IOService *native_legacy_display_allocate(void);

static IOService *pendingLegacyDisplay;
// These owned references deliberately survive until reboot. No driver unload
// is offered by this built-in experiment, and published clients may retain it.
static IOService *activeLegacyDisplay;
static IOPlatformDevice *activeGOPNub;
static unsigned consoleOwnership;
extern "C" void cdx15_mapping_observed(IOMemoryMap *,uint32_t,uint32_t,uint64_t);
extern "C" void cdx15_client_open(task_t,uint32_t,IOUserClient *,IOReturn);
extern "C" void cdx15_validation(const void *,bool,uint32_t);
extern "C" void cdx15_copy(const void *,uint32_t);
extern "C" void cdx15_vsync(unsigned,unsigned);
extern "C" void cdx15_snapshot(char *,size_t,bool);

extern "C" void cdx14_after_release(void);
extern "C" void cdx14p1_schedule_snapshot(void);

static bool validVideo(const PE_Video &v) {
    return v.v_baseAddr && !(v.v_baseAddr&3) && v.v_width && v.v_height &&
        v.v_depth==32 && !v.v_rotate && !v.v_offset && !(v.v_rowBytes&3) &&
        v.v_display<=1 && v.v_width<=16384 && v.v_height<=16384 &&
        v.v_rowBytes>=v.v_width*4 && v.v_rowBytes<=65536 &&
        v.v_rowBytes<=UINT64_MAX/v.v_height &&
        (!v.v_length || v.v_length>=v.v_rowBytes*v.v_height) &&
        v.v_baseAddr<=UINT64_MAX-v.v_rowBytes*v.v_height;
}
extern "C" bool cdx13_publish_ui_scale(uint32_t,uint32_t);
static unsigned option(const char *name) {
    unsigned value=0;PE_parse_boot_argn(name,&value,sizeof(value));return value;
}

extern "C" {
// Separate lifecycle results from user-client and real-transfer observations.
volatile uint32_t native_legacy_stage,native_legacy_failure;
volatile int native_legacy_meta_status=-1,native_legacy_surface_status=-1;
volatile uint32_t native_legacy_init_result,native_legacy_start_result;
volatile uint32_t native_legacy_parent_match,native_legacy_probe_match;
volatile uint32_t native_legacy_surface_found,native_legacy_dt_attached;
volatile uint32_t native_legacy_registration_calls,native_legacy_client_calls;
volatile uint32_t native_legacy_pm_calls;
volatile int native_legacy_client_pid,native_legacy_client_status=-1;
volatile uint32_t native_legacy_client_type;
volatile uint64_t native_legacy_object,native_legacy_nub;
volatile uint64_t native_legacy_gop_physical,native_legacy_gop_virtual,native_legacy_gop_bytes;
volatile uint32_t native_legacy_gop_width,native_legacy_gop_height;
volatile uint32_t native_legacy_swap_validation_calls,native_legacy_swap_validation_result;
volatile uint32_t native_legacy_swap_validation_reason,native_legacy_transfer_calls;
volatile int native_legacy_transfer_status=-1;
volatile uint64_t native_legacy_transfer_bytes,native_legacy_copy_ticks,native_legacy_copy_bytes;
volatile uint32_t native_legacy_retirement_calls,native_legacy_vsync_count;
volatile uint32_t native_legacy_guard_slot;
volatile uint64_t native_legacy_early_retires,native_legacy_early_failures;
extern kern_return_t OSKextLoadKextWithIdentifier(const char *);

__attribute__((noinline)) void native_legacy_display_checkpoint(void) {
    __asm__ volatile("" ::: "memory");
}
static void failed(unsigned reason) {
    native_legacy_failure=reason;native_legacy_stage=8;
    IOLog("CDX_DISP failed reason=%u\n",reason);
    native_legacy_display_checkpoint();
}

// The exact original backend vtable still has unknown leaves. They cannot
// return a made-up success or return value; report the slot and stop.
__attribute__((noreturn,noinline)) void native_legacy_backend_guard(
    unsigned slot,void *object,void *caller) {
    native_legacy_guard_slot=slot;
    panic("CDX_DISP guard slot=%u stage=%u obj=%p caller=%p",
        slot,native_legacy_stage,object,caller);
}

// Called only after NativeLegacyDisplay validates an actual destination and
// source (or a validated blank swap). Keep the boot console until that point.
bool native_legacy_prepare_scanout(void) {
    if(ml_at_interrupt_context() || !ml_get_interrupts_enabled())return false;
    if(option("luming-display-console-handoff")!=1) {cdx14p1_schedule_snapshot();return true;}
    if(__atomic_load_n(&consoleOwnership,__ATOMIC_ACQUIRE)==2)return true;
    unsigned empty=0;
    if(!__atomic_compare_exchange_n(&consoleOwnership,&empty,1,false,
        __ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE))return false;
    // Public platform console lifecycle; never write the console's private
    // state or video vtable. The panic path can still reacquire the screen.
    PE_initialize_console(nullptr,kPEReleaseScreen);
    cdx14_after_release();
    __atomic_store_n(&consoleOwnership,2,__ATOMIC_RELEASE);
    return true;
}

bool native_legacy_gop_mapping_observed(IOService *display,IOMemoryMap *mapping,
    uint32_t width,uint32_t height) {
    PE_Video v={};
    if((uintptr_t)display!=native_legacy_object || !mapping ||
       PE_current_console(&v) || !validVideo(v) || width!=v.v_width || height!=v.v_height ||
       mapping->getPhysicalAddress()!=v.v_baseAddr ||
       mapping->getLength()!=v.v_rowBytes*v.v_height || !mapping->getVirtualAddress())return false;
    native_legacy_gop_physical=mapping->getPhysicalAddress();
    native_legacy_gop_virtual=mapping->getVirtualAddress();
    native_legacy_gop_bytes=mapping->getLength();
    native_legacy_gop_width=width;native_legacy_gop_height=height;
    IOLog("CDX_DISP mapped w=%u h=%u\n",width,height);
    bool ok=cdx13_publish_ui_scale(width,height);
    if(ok)cdx15_mapping_observed(mapping,width,height,v.v_rowBytes);
    return ok;
}
void native_legacy_registration_observed(IOService *display) {
    native_legacy_registration_calls=native_legacy_registration_calls+1;
    IOLog("CDX_DISP registered class=%s\n",display->getMetaClass()->getClassName());
}
void native_legacy_client_enter(task_t task,uint32_t type) {
    native_legacy_client_calls=native_legacy_client_calls+1;native_legacy_client_type=type;
    native_legacy_client_pid=task?proc_pid((proc_t)get_bsdtask_info(task)):0;
}
void native_legacy_client_observed(IOReturn status,IOUserClient *) {
    native_legacy_client_status=status;
    if(native_legacy_client_calls<=8)
        IOLog("CDX_DISP client pid=%d status=%x\n",native_legacy_client_pid,(unsigned)status);
}
void native_legacy_pm_observed(unsigned stage,IOReturn status,unsigned long ordinal) {
    native_legacy_pm_calls=native_legacy_pm_calls+1;
    if(native_legacy_pm_calls<=8)
        IOLog("CDX_DISP pm stage=%u state=%u status=%x\n",stage,(unsigned)ordinal,(unsigned)status);
}
void native_legacy_swap_stage(unsigned) {}
void native_legacy_swap_validation_observed(bool accepted,unsigned reason,const void *request,const void *) {
    cdx15_validation(request,accepted,reason);
    native_legacy_swap_validation_calls=native_legacy_swap_validation_calls+1;
    native_legacy_swap_validation_result=accepted;native_legacy_swap_validation_reason=reason;
    if(native_legacy_swap_validation_calls<=8)
        IOLog("CDX_DISP validate accepted=%u reason=%u\n",(unsigned)accepted,reason);
}
void native_legacy_surface_rejected(uint64_t,uint64_t,uint32_t,uint32_t,uint64_t,uint64_t,uint64_t) {}
void native_legacy_frame_observed(unsigned,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t) {}
void native_legacy_frame_colors_observed(const uint32_t *,const uint64_t *,uint64_t) {}
void native_legacy_copy_timing_observed(uint64_t ticks,uint64_t bytes) {
    native_legacy_copy_ticks=ticks;native_legacy_copy_bytes=bytes;
}
void native_legacy_transfer_observed(IOReturn status,const void *request,uint64_t bytes) {
    cdx15_copy(request,(uint32_t)status);
    native_legacy_transfer_calls=native_legacy_transfer_calls+1;native_legacy_transfer_status=status;native_legacy_transfer_bytes=bytes;
    if(native_legacy_transfer_calls<=8)
        IOLog("CDX_DISP copy status=%x bytes=%llu\n",(unsigned)status,(unsigned long long)bytes);
}
void native_legacy_retirement_observed(IOService *) {native_legacy_retirement_calls=native_legacy_retirement_calls+1;}
void native_legacy_vsync_observed(unsigned event,unsigned hz) {
    cdx15_vsync(event,hz);
    if(event==1)native_legacy_vsync_count=native_legacy_vsync_count+1;
}
// CPU-only transport: never offer memory to any SM8550/Adreno service. The
// shared backend immediately uses its normal bounded CPU copy when false.
bool native_legacy_gpu_offer(void *,IOMemoryDescriptor *,uint64_t,uint32_t,uint32_t) {return false;}
void native_legacy_gpu_fallback_observed(int) {}

void native_legacy_display_probe(void) {
    if(native_legacy_stage)return;
    if(option("offline-legacy-register")!=1 || option("offline-legacy-phase")!=4)return;
    native_legacy_stage=1;
    IOLog("CDX_DISP ctor begin\n");
    void *handle=OSMetaClass::preModLoad(g_kernel_kmod_info.name);
    if(!handle){failed(1);return;}
    native_legacy_display_static_init();
    native_legacy_meta_status=OSMetaClass::postModLoad(handle);
    if(native_legacy_meta_status){failed(2);return;}
    native_legacy_stage=2;
    PE_Video v={};
    if(PE_current_console(&v) || !validVideo(v)) {
        IOLog("CDX_DISP bad console depth=%u mode=%u rotate=%u\n",
            (unsigned)v.v_depth,(unsigned)v.v_display,(unsigned)v.v_rotate);
        failed(3);return;
    }
    IOLog("CDX_DISP console w=%u h=%u stride=%u mode=%u\n",
        (unsigned)v.v_width,(unsigned)v.v_height,(unsigned)v.v_rowBytes,(unsigned)v.v_display);
    IOService *display=native_legacy_display_allocate();
    if(!display){failed(4);return;}
    native_legacy_object=(uintptr_t)display;
    native_legacy_parent_match=display->metaCast("IOMobileFramebufferLegacy") &&
        display->metaCast("IOMobileFramebuffer") && display->metaCast("IOService");
    if(!native_legacy_parent_match){display->release();native_legacy_object=0;failed(5);return;}
    native_legacy_init_result=display->init();
    if(!native_legacy_init_result){display->release();native_legacy_object=0;failed(6);return;}
    // IOSurface waits on IOBSD, so leave the object pending until the existing
    // core's post-IOKitBSDInit hook. No peripheral service is called here.
    pendingLegacyDisplay=display;native_legacy_stage=3;
    IOLog("CDX_DISP pending IOBSD\n");
}

void native_legacy_display_late_probe(void) {
    IOService *display=pendingLegacyDisplay;
    if(!display || activeLegacyDisplay)return;
    pendingLegacyDisplay=nullptr;native_legacy_stage=4;
    native_legacy_surface_status=OSKextLoadKextWithIdentifier("com.apple.iokit.IOSurface");
    IOLog("CDX_DISP IOSurface load=%x\n",(unsigned)native_legacy_surface_status);
    OSDictionary *matching=IOService::nameMatching("IOCoreSurfaceRoot");
    IOService *surface=matching?IOService::waitForMatchingService(matching,5000000000ULL):nullptr;
    native_legacy_surface_found=surface!=nullptr;
    OSSafeReleaseNULL(surface);OSSafeReleaseNULL(matching);
    PE_Video v={};
    if(native_legacy_surface_status || !native_legacy_surface_found ||
       PE_current_console(&v) || !validVideo(v)) {
        display->release();native_legacy_object=0;failed(7);return;
    }
    IOPlatformDevice *nub=new IOPlatformDevice;
    IODeviceMemory *memory=IODeviceMemory::withRange(v.v_baseAddr,v.v_rowBytes*v.v_height);
    OSArray *ranges=OSArray::withCapacity(1);
    IOService *parent=IOService::getResourceService();
    IORegistryEntry *tree=IORegistryEntry::fromPath("/arm-io",gIODTPlane);
    bool nubAttached=false,nubStarted=false,dtAttached=false,attached=false,started=false;
    unsigned reason=8;
    if(nub && memory && ranges && parent && tree && nub->init() && ranges->setObject(memory)) {
        nub->setDeviceMemory(ranges);nub->setName("NativeGOPFramebuffer");
        nubAttached=nub->attach(parent);
        if(nubAttached)nubStarted=nub->start(parent);
        reason=9;
        if(nubStarted) {
            // Real firmware scanout resource in its actual DT plane. No Apple
            // compatible, panel timing, physical density or GPU claim is made.
            const char type[]="display-subsystem";
            OSData *data=OSData::withBytes(type,sizeof(type));
            if(data && nub->setProperty("device_type",data)) {
                nub->setName("gop-display",gIODTPlane);
                dtAttached=nub->attachToParent(tree,gIODTPlane);
            }
            OSSafeReleaseNULL(data);native_legacy_dt_attached=dtAttached;
            IOLog("CDX_DISP DT attached=%u\n",(unsigned)dtAttached);
            SInt32 score=0;reason=10;
            native_legacy_probe_match=dtAttached && display->probe(nub,&score)==display;
            IOLog("CDX_DISP probe matched=%u\n",native_legacy_probe_match);
            if(native_legacy_probe_match)attached=display->attach(nub);
            if(attached) {
                native_legacy_stage=5;started=display->start(nub);
                native_legacy_start_result=started;reason=11;
            }
            IOLog("CDX_DISP start result=%u\n",(unsigned)started);
            if(started) {
                activeLegacyDisplay=display;activeGOPNub=nub;
                native_legacy_nub=(uintptr_t)nub;native_legacy_stage=10;
                OSSafeReleaseNULL(ranges);OSSafeReleaseNULL(memory);OSSafeReleaseNULL(tree);
                native_legacy_display_checkpoint();return;
            }
        }
    }
    if(started)display->stop(nub);
    if(attached)display->detach(nub);
    if(dtAttached)nub->detachFromParent(tree,gIODTPlane);
    if(nubStarted)nub->stop(parent);
    if(nubAttached)nub->detach(parent);
    OSSafeReleaseNULL(ranges);OSSafeReleaseNULL(memory);OSSafeReleaseNULL(tree);OSSafeReleaseNULL(nub);
    display->release();native_legacy_object=0;failed(reason);
}
} // extern "C"

// CDX11 owned diagnostics: source-only, no rendering changes.
#include <libkern/libkern.h>
// SPDX-License-Identifier: BSD-2-Clause-Patent
// Included once, at the end of the owned LegacyDisplayProbe.cpp.
// Bounded diagnostics only: no allocation, wait, object call or policy change.
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct {
    int pid, exception;
    unsigned slide, off;
    uint64_t c0, c1;
} Cdx11Exception;
static Cdx11Exception cdx11_first, cdx11_last;
static unsigned cdx11_lock, cdx11_count, cdx11_dropped;

void cdx11_capture_exception(int pid, const char *name, int exception,
    uint64_t c0, uint64_t c1, unsigned slide, unsigned off)
{
    // EXC_CRASH / EXC_CORPSE_NOTIFY are secondary notifications. They must not
    // overwrite the original breakpoint or bad-access codes being investigated.
    if (!name || strcmp(name, "SpringBoard") ||
        (exception != 1 && exception != 6)) return;
    if (__atomic_exchange_n(&cdx11_lock, 1, __ATOMIC_ACQUIRE)) {
        __atomic_fetch_add(&cdx11_dropped, 1, __ATOMIC_RELAXED);
        return;
    }
    Cdx11Exception value = {pid, exception, slide, off, c0, c1};
    if (cdx11_last.pid != pid) { cdx11_count = 0; cdx11_first = value; }
    if (!cdx11_count) cdx11_first = value;
    cdx11_last = value;
    ++cdx11_count;
    __atomic_store_n(&cdx11_lock, 0, __ATOMIC_RELEASE);
}

// Display counters belong to the existing probe. They are approximate samples,
// not a transaction or a proof of CADisplay enumeration / visible presentation.
extern volatile uint32_t native_legacy_stage, native_legacy_failure;
extern volatile uint32_t native_legacy_registration_calls, native_legacy_client_calls;
extern volatile int native_legacy_client_status;
extern volatile uint32_t native_legacy_swap_validation_calls, native_legacy_swap_validation_result;
extern volatile uint32_t native_legacy_swap_validation_reason, native_legacy_transfer_calls;
extern volatile int native_legacy_transfer_status;
extern volatile uint32_t native_legacy_retirement_calls, native_legacy_vsync_count;

int cdx11_crash_summary(int pid, const char *name, const char *prefix,
    char *output, size_t capacity)
{
    if (!name || strcmp(name, "SpringBoard") || !output || !capacity) return 0;
    Cdx11Exception first = {0,0,0,0,0,0}, last = {0,0,0,0,0,0};
    unsigned count = 0, matched = 0, busy = 0;
    if (__atomic_exchange_n(&cdx11_lock, 1, __ATOMIC_ACQUIRE)) {
        busy = 1;
    } else {
        if (cdx11_last.pid == pid && cdx11_count) {
            first = cdx11_first; last = cdx11_last;
            count = cdx11_count; matched = 1;
        }
        __atomic_store_n(&cdx11_lock, 0, __ATOMIC_RELEASE);
    }
    // Newlines deliberately survive into the existing panic reason. No IOLog
    // queue or pid<=N filter is needed to retain these final lines.
    (void)snprintf(output, capacity,
        "%s\nCDX11 pid=%d match=%u busy=%u n=%u drop=%u\n"
        "CDX11 first e=%d c0=%llx c1=%llx\n"
        "CDX11 last e=%d off=%u sl=%x c0=%llx c1=%llx\n"
        "CDX11 st=%u fail=%u reg=%u cl=%u rc=%x\n"
        "CDX11 val=%u ok=%u why=%u cp=%u rc=%x\n"
        "CDX11 ret=%u vs=%u",
        prefix ? prefix : "SpringBoard exited", pid, matched, busy, count,
        __atomic_load_n(&cdx11_dropped, __ATOMIC_RELAXED),
        first.exception, (unsigned long long)first.c0, (unsigned long long)first.c1,
        last.exception, last.off, last.slide,
        (unsigned long long)last.c0, (unsigned long long)last.c1,
        native_legacy_stage, native_legacy_failure, native_legacy_registration_calls,
        native_legacy_client_calls, (unsigned)native_legacy_client_status,
        native_legacy_swap_validation_calls, native_legacy_swap_validation_result,
        native_legacy_swap_validation_reason, native_legacy_transfer_calls,
        (unsigned)native_legacy_transfer_status,
        native_legacy_retirement_calls, native_legacy_vsync_count);
    output[capacity - 1] = 0;
    return 1;
}
#ifdef __cplusplus
}
#endif

#include <libkern/copyio.h>
// SPDX-License-Identifier: BSD-2-Clause-Patent
// Read the exact FBSDisplayMode instance at its qualified original fatal PC.
// Only raw integer words are copied: no floating-point instructions in kernel.
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
static unsigned cdx12_lock;
static int cdx12_pid, cdx12_error=-1;
static unsigned cdx12_valid;
static uint64_t cdx12_fields[8];
volatile unsigned cdx12_refresh_calls, cdx12_refresh_present;

void cdx12_capture_mode(int pid, uint64_t object)
{
    uint64_t words[8]={0,0,0,0,0,0,0,0};
    // Copy once from the current user's address space. Never dereference user
    // memory as kernel pointers, inspect another task, or allocate/retry.
    if (object < 4096 || (object&7) || object > UINT64_MAX-72) return;
    int error=copyin(object+8,words,sizeof(words));
    if (__atomic_exchange_n(&cdx12_lock,1,__ATOMIC_ACQUIRE)) return;
    cdx12_pid=pid; cdx12_error=error; cdx12_valid=error==0;
    if (!error) memcpy(cdx12_fields,words,sizeof(words));
    __atomic_store_n(&cdx12_lock,0,__ATOMIC_RELEASE);
}

void cdx12_append_mode_summary(int pid, char *output, size_t capacity)
{
    uint64_t w[8]={0,0,0,0,0,0,0,0};
    unsigned valid=0,busy=0; int error=-1;
    if (__atomic_exchange_n(&cdx12_lock,1,__ATOMIC_ACQUIRE)) busy=1;
    else {
        if (pid==cdx12_pid) {
            valid=cdx12_valid; error=cdx12_error;
            if (valid) memcpy(w,cdx12_fields,sizeof(w));
        }
        __atomic_store_n(&cdx12_lock,0,__ATOMIC_RELEASE);
    }
    if (!output || !capacity) return;
    size_t used=strnlen(output,capacity);
    if (used==capacity) {output[capacity-1]=0;return;}
    (void)snprintf(output+used,capacity-used,
        "\nCDX12 mode got=%u err=%d busy=%u\n"
        "CDX12 w=%llu h=%llu pref=%llu rot=%llu\n"
        "CDX12 scaleBits=%llx rateBits=%llx\n"
        "CDX12 gamut=%llu hdr=%llu pub=%u prop=%u",
        valid,error,busy,(unsigned long long)w[0],(unsigned long long)w[1],
        (unsigned long long)w[2],(unsigned long long)w[7],
        (unsigned long long)w[3],(unsigned long long)w[4],
        (unsigned long long)w[5],(unsigned long long)w[6],
        cdx12_refresh_calls,cdx12_refresh_present);
    output[capacity-1]=0;
}
#ifdef __cplusplus
}
#endif

extern "C" void cdx12_refresh_observed(void *object) {
    IOService *display=static_cast<IOService *>(object);
    cdx12_refresh_calls=cdx12_refresh_calls+1;
    cdx12_refresh_present=display && display->getProperty("IOMFBDisplayRefresh")!=nullptr;
    IOLog("CDX12 refresh publish=%u property=%u\n",cdx12_refresh_calls,cdx12_refresh_present);
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Explicit UI pixels-per-point policy. No physical DPI or panel timing claim.
// Same 4-byte native-endian /chosen contract consumed by stock MobileGestalt.
extern "C" {
volatile unsigned cdx13_ui_requested,cdx13_ui_readback,cdx13_ui_status=99;
volatile unsigned cdx13_ui_writes;

bool cdx13_publish_ui_scale(uint32_t width,uint32_t height)
{
    const unsigned scale=option("luming-display-ui-scale");
    cdx13_ui_requested=scale;
    if(!scale){cdx13_ui_status=0;return true;}
    // The enabled experiment is qualified only for this measured scanout.
    // 2 -> 618 x 1375 points. Scale 3 is not an integral division here.
    if(scale>3 || width!=1236 || height!=2750 || width%scale || height%scale) {
        cdx13_ui_status=1;return false;
    }
    IORegistryEntry *chosen=IORegistryEntry::fromPath("/chosen",gIODTPlane);
    if(!chosen){cdx13_ui_status=2;return false;}
    const char *keys[2]={"display-scale","display-rotation"};
    const uint32_t desired[2]={scale,0};
    OSObject *prior[2]={nullptr,nullptr};
    bool replace[2]={false,false},written[2]={false,false};
    unsigned failure=0;
    for(unsigned i=0;i<2;++i) {
        prior[i]=chosen->getProperty(keys[i]);
        if(prior[i]) {
            prior[i]->retain();
            OSData *data=OSDynamicCast(OSData,prior[i]);uint32_t value=0;
            if(!data || data->getLength()!=4){failure=3;break;}
            memcpy(&value,data->getBytesNoCopy(),4);
            if(value==desired[i])continue;
            // Permit repairing a zero scale; do not overwrite a conflicting
            // positive policy, a nonzero rotation, or an unknown property type.
            if(i!=0 || value!=0){failure=4;break;}
        }
        replace[i]=true;
    }
    if(!failure)for(unsigned i=0;i<2;++i)if(replace[i]) {
        OSData *data=OSData::withBytes(&desired[i],4);
        bool ok=data && chosen->setProperty(keys[i],data);
        if(data)data->release();
        if(!ok){failure=5;break;}
        written[i]=true;
    }
    if(!failure)for(unsigned i=0;i<2;++i) {
        OSData *data=OSDynamicCast(OSData,chosen->getProperty(keys[i]));
        uint32_t actual=0;
        if(!data || data->getLength()!=4){failure=6;break;}
        memcpy(&actual,data->getBytesNoCopy(),4);
        if(actual!=desired[i]){failure=7;break;}
        if(i==0)cdx13_ui_readback=actual;
    }
    if(failure) {
        // Roll back only properties written by this attempt.
        for(unsigned i=0;i<2;++i)if(written[i]) {
            if(prior[i]) {if(!chosen->setProperty(keys[i],prior[i]))failure=8;}
            else chosen->removeProperty(keys[i]);
        }
        cdx13_ui_readback=0;
    } else for(unsigned i=0;i<2;++i)if(written[i])cdx13_ui_writes=cdx13_ui_writes+1;
    for(unsigned i=0;i<2;++i)if(prior[i])prior[i]->release();
    chosen->release();cdx13_ui_status=failure;
    IOLog("CDX13 ui=%u read=%u rc=%u writes=%u\n",scale,
        cdx13_ui_readback,failure,cdx13_ui_writes);
    return failure==0;
}
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Short fatal summary of actual captured fields; no kernel FP arithmetic.
extern "C" {
static unsigned cdx13_vc_lock,cdx13_vc_valid;
static int cdx13_vc_pid;
static uint64_t cdx13_vc;
void cdx13_capture_validity(int pid,uint64_t vc) {
    if(__atomic_exchange_n(&cdx13_vc_lock,1,__ATOMIC_ACQUIRE))return;
    cdx13_vc_pid=pid;cdx13_vc=vc;cdx13_vc_valid=1;
    __atomic_store_n(&cdx13_vc_lock,0,__ATOMIC_RELEASE);
}
static bool cdx13_nonnegative_finite(uint64_t bits) {
    return (bits>>63)==0 && ((bits>>52)&0x7ff)!=0x7ff;
}
// These checks cover the captured scalar conditions, not runtime class identity.
static unsigned cdx13_scalar_issues(const uint64_t *w) {
    unsigned why=0;
    if(w[0]==0 || w[1]==0 || w[0]==UINT64_MAX || w[1]==UINT64_MAX || w[2]==UINT64_MAX)why|=1;
    if(!cdx13_nonnegative_finite(w[3]) || !cdx13_nonnegative_finite(w[4]) || !w[4])why|=2;
    // Original helper tests abs(scaleOverride) < 2^-52 when pref==0.
    if(!w[2] && (w[3]&0x7fffffffffffffffULL)<0x3cb0000000000000ULL)why|=4;
    if(w[5]>=2 || w[6]>=3 || w[7]>=4)why|=8;
    return why;
}
void cdx13_append_mode_summary(int pid,char *output,size_t capacity) {
    uint64_t w[8]={};unsigned got=0,busy=0;int error=-1;
    if(__atomic_exchange_n(&cdx12_lock,1,__ATOMIC_ACQUIRE))busy=1;
    else {
        if(pid==cdx12_pid){got=cdx12_valid;error=cdx12_error;if(got)memcpy(w,cdx12_fields,sizeof(w));}
        __atomic_store_n(&cdx12_lock,0,__ATOMIC_RELEASE);
    }
    unsigned vcGot=0;uint64_t vc=0;
    if(!__atomic_exchange_n(&cdx13_vc_lock,1,__ATOMIC_ACQUIRE)) {
        if(cdx13_vc_valid && cdx13_vc_pid==pid){vcGot=1;vc=cdx13_vc;}
        __atomic_store_n(&cdx13_vc_lock,0,__ATOMIC_RELEASE);
    }
    if(!output || !capacity)return;
    size_t used=strnlen(output,capacity);
    if(used==capacity){output[capacity-1]=0;return;}
    (void)snprintf(output+used,capacity-used,
        "\nCDX13 got=%u err=%d busy=%u\n"
        "CDX13 w=%llu h=%llu pref=%llu\n"
        "CDX13 sb=%llx rb=%llx\n"
        "CDX13 vcGot=%u vc=%llu issues=%x\n"
        "CDX13 gamut=%llu hdr=%llu rot=%llu\n"
        "CDX13 ui=%u read=%u rc=%u writes=%u",
        got,error,busy,(unsigned long long)w[0],(unsigned long long)w[1],(unsigned long long)w[2],
        (unsigned long long)w[3],(unsigned long long)w[4],vcGot,(unsigned long long)vc,
        got?cdx13_scalar_issues(w):0xffffffffU,
        (unsigned long long)w[5],(unsigned long long)w[6],(unsigned long long)w[7],
        cdx13_ui_requested,cdx13_ui_readback,cdx13_ui_status,cdx13_ui_writes);
    output[capacity-1]=0;
}
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Integer-only, bounded samples of visible pixels; NOT a full-frame CRC.
// Appended verbatim to LegacyDisplayProbe.cpp, so it must not carry "#pragma
// once": the pragma in the translation unit itself is -Werror on the XNU build.
struct Cdx14Samples {
    uint64_t hash;
    uint32_t pixels[64];
};
static bool cdx14_samples(const volatile void *base,uint64_t bytes,uint64_t stride,
    uint32_t width,uint32_t height,Cdx14Samples *out) {
    if(!base || !out || !width || !height || width>16384 || height>16384 ||
       ((uintptr_t)base&3) || (stride&3) || stride<(uint64_t)width*4 ||
       stride>65536 || stride>bytes/height)return false;
    out->hash=14695981039346656037ULL;
    for(unsigned i=0;i<64;++i) {
        uint64_t x=(uint64_t)(i%8)*(width-1)/7;
        uint64_t y=(uint64_t)(i/8)*(height-1)/7;
        const volatile uint32_t *pixel=reinterpret_cast<const volatile uint32_t *>(
            reinterpret_cast<const volatile unsigned char *>(base)+y*stride+x*4);
        uint32_t value=*pixel;out->pixels[i]=value;
        for(unsigned b=0;b<4;++b){out->hash^=(value>>(b*8))&255;out->hash*=1099511628211ULL;}
    }
    return true;
}
static unsigned cdx14_sample_diff(const Cdx14Samples &a,const Cdx14Samples &b) {
    unsigned n=0;for(unsigned i=0;i<64;++i)n+=(a.pixels[i]!=b.pixels[i]);return n;
}
static bool cdx14_sample_due(uint64_t sequence) {
    return sequence<=8 || (sequence<=256 && !(sequence&(sequence-1)));
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Appended inside LegacyDisplayProbe.cpp, after Stage13 definitions.
// Display command-gate serialization is inherited from the CPU swap path.
extern "C" void cdx14_console_commit(void);
extern "C" void cdx14_console_snapshot(unsigned *);
extern "C" size_t cdx14_daemon_summary(char *,size_t);
extern "C" size_t cdx14_exception_summary(char *,size_t);
struct Cdx14FrameState {
    uint64_t sequence,srcHash,dstBefore,dstAfter,previousAfter;
    uint32_t sampled,blankCount,valid,sourceChanged,copyMismatch,betweenMismatch;
    uint32_t width,height,srcFirst,dstFirst,srcGrid36,dstGrid36;
    uint32_t console[5];
};
static Cdx14FrameState cdx14_frame={};
static Cdx14Samples cdx14_source={},cdx14_before={},cdx14_previous={};
static bool cdx14_inflight=false,cdx14_has_previous=false;
static uint32_t cdx14_previous_width,cdx14_previous_height;
static void *cdx14_destination;
static const void *cdx14_source_address;
static uint64_t cdx14_dst_bytes,cdx14_src_bytes,cdx14_dst_stride,cdx14_src_stride;
extern "C" void cdx14_frame_gap(void) {
    cdx14_inflight=false;cdx14_has_previous=false;
    if(option("luming-display-frame-probe")==1) {
        ++cdx14_frame.blankCount;
        if(cdx14_frame.blankCount<=4)IOLog("CDX14 blank=%u\n",cdx14_frame.blankCount);
    }
}
static void cdx14_publish(void) {
    cdx14_console_snapshot(cdx14_frame.console);
    if(activeLegacyDisplay) {
        OSData *data=OSData::withBytes(&cdx14_frame,sizeof(cdx14_frame));
        if(data){activeLegacyDisplay->setProperty("CDX14FrameSamples",data);data->release();}
    }
}
extern "C" void cdx14_frame_begin(void *destination,uint64_t dstBytes,uint64_t dstStride,
    const void *source,uint64_t srcBytes,uint64_t srcStride,uint32_t width,uint32_t height) {
    cdx14_inflight=false;
    if(option("luming-display-frame-probe")!=1)return;
    ++cdx14_frame.sequence;
    if(!cdx14_sample_due(cdx14_frame.sequence))return;
    cdx14_frame.width=width;cdx14_frame.height=height;cdx14_frame.valid=0;
    cdx14_frame.sourceChanged=cdx14_frame.copyMismatch=cdx14_frame.betweenMismatch=0;
    if(!cdx14_samples(source,srcBytes,srcStride,width,height,&cdx14_source) ||
       !cdx14_samples(destination,dstBytes,dstStride,width,height,&cdx14_before)) {cdx14_has_previous=false;return;}
    bool comparable=cdx14_has_previous && width==cdx14_previous_width && height==cdx14_previous_height;
    cdx14_frame.betweenMismatch=comparable?cdx14_sample_diff(cdx14_previous,cdx14_before):0;
    cdx14_frame.previousAfter=cdx14_has_previous?cdx14_previous.hash:0;
    // Only consecutive sampled frames support an intervening-writer comparison.
    if(cdx14_frame.sequence>8)cdx14_frame.betweenMismatch=0;
    cdx14_frame.srcHash=cdx14_source.hash;cdx14_frame.dstBefore=cdx14_before.hash;
    cdx14_frame.srcFirst=cdx14_source.pixels[0];cdx14_frame.srcGrid36=cdx14_source.pixels[36];
    cdx14_destination=destination;cdx14_source_address=source;
    cdx14_dst_bytes=dstBytes;cdx14_src_bytes=srcBytes;
    cdx14_dst_stride=dstStride;cdx14_src_stride=srcStride;cdx14_inflight=true;
}
extern "C" void cdx14_frame_end(bool copied) {
    if(!cdx14_inflight)return;
    cdx14_inflight=false;
    Cdx14Samples after={},sourceAfter={};
    if(!copied || !cdx14_samples(cdx14_destination,cdx14_dst_bytes,cdx14_dst_stride,
        cdx14_frame.width,cdx14_frame.height,&after) ||
       !cdx14_samples(cdx14_source_address,cdx14_src_bytes,cdx14_src_stride,
        cdx14_frame.width,cdx14_frame.height,&sourceAfter)) {
        cdx14_has_previous=false;cdx14_publish();return;
    }
    cdx14_frame.valid=1;++cdx14_frame.sampled;
    cdx14_frame.sourceChanged=cdx14_sample_diff(cdx14_source,sourceAfter);
    cdx14_frame.copyMismatch=cdx14_sample_diff(cdx14_source,after);
    cdx14_frame.dstAfter=after.hash;cdx14_frame.dstFirst=after.pixels[0];cdx14_frame.dstGrid36=after.pixels[36];
    cdx14_previous=after;cdx14_has_previous=true;
    cdx14_previous_width=cdx14_frame.width;cdx14_previous_height=cdx14_frame.height;cdx14_publish();
    // Log AFTER sampling; nohandoff console output can itself alter the next sample.
    IOLog("CDX14 f=%llu src=%llx dst=%llx\n",(unsigned long long)cdx14_frame.sequence,
        (unsigned long long)cdx14_frame.srcHash,(unsigned long long)cdx14_frame.dstAfter);
    IOLog("CDX14 eq=%u mutate=%u between=%u own=%u block=%u\n",(unsigned)!cdx14_frame.copyMismatch,
        cdx14_frame.sourceChanged,cdx14_frame.betweenMismatch,cdx14_frame.console[0],cdx14_frame.console[3]);
}
// SPDX-License-Identifier: BSD-2-Clause-Patent
// Embedded into the provider translation unit; no object-layout change.
static unsigned cdx14p1_frozen,cdx14p1_writers;
extern "C" bool cdx14p1_scanout_enter(void) {
    if(__atomic_load_n(&cdx14p1_frozen,__ATOMIC_SEQ_CST))return false;
    __atomic_add_fetch(&cdx14p1_writers,1,__ATOMIC_SEQ_CST);
    if(__atomic_load_n(&cdx14p1_frozen,__ATOMIC_SEQ_CST)) {
        __atomic_sub_fetch(&cdx14p1_writers,1,__ATOMIC_SEQ_CST);return false;
    }
    return true;
}
extern "C" void cdx14p1_scanout_leave(void) {
    __atomic_sub_fetch(&cdx14p1_writers,1,__ATOMIC_SEQ_CST);
}
static bool cdx14p1_quiesce(void) {
    __atomic_store_n(&cdx14p1_frozen,1,__ATOMIC_SEQ_CST);
    for(unsigned retry=0;retry<100;++retry) {
        if(!__atomic_load_n(&cdx14p1_writers,__ATOMIC_SEQ_CST))return true;
        IOSleep(10);
    }
    return !__atomic_load_n(&cdx14p1_writers,__ATOMIC_SEQ_CST);
}

extern "C" unsigned cdx14p1_console_reclaim(void);
extern "C" bool cdx19_capture_next(void);
static thread_call_t cdx14_snapshot_call;
static void cdx14_snapshot_callback(thread_call_param_t,thread_call_param_t) {
    if(option("luming-display-stackshot")==1){
        if(cdx19_capture_next()){
            uint64_t deadline;clock_interval_to_deadline(15,NSEC_PER_SEC,&deadline);
            thread_call_enter_delayed(cdx14_snapshot_call,deadline);return;
        }
        bool quiet19=cdx14p1_quiesce();char stackReason[820]={};
        cdx15_snapshot(stackReason,sizeof(stackReason),quiet19);
        unsigned reclaimed19=quiet19?cdx14p1_console_reclaim():0;
        panic("CDX19 stackshot (intentional) r=%u\n%s",reclaimed19,stackReason);
    }
    bool quiet=cdx14p1_quiesce();
    char reason[660]={};
    // Last-destination sampling MUST precede console clear/reacquisition.
    cdx15_snapshot(reason,sizeof(reason),quiet);
    unsigned reclaimed=quiet?cdx14p1_console_reclaim():0;
    panic("CDX17 snapshot (intentional) r=%u\n%s",reclaimed,reason);
}
extern "C" void cdx14p1_schedule_snapshot(void) {
    // Opt-in, independent delayed snapshot survives a stalled display work loop.
    if(option("luming-display-snapshot")==1 && !cdx14_snapshot_call) {
        cdx14_snapshot_call=thread_call_allocate(cdx14_snapshot_callback,nullptr);
        if(cdx14_snapshot_call) {
            uint64_t deadline;clock_interval_to_deadline(15,NSEC_PER_SEC,&deadline);
            thread_call_enter_delayed(cdx14_snapshot_call,deadline);
        }
    }
}

extern "C" void cdx14_after_release(void) {
    if(option("luming-display-vt-latch")==1)cdx14_console_commit();
    cdx14p1_schedule_snapshot();
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Caller holds the diagnostic spin lock. No kernel pointers are dereferenced.
namespace cdx15 {
struct Client {uint64_t id,serial,opened;uint32_t pid,type,status,ipc,validated;char name[17];};
struct Call {uint64_t token,thread,client;uint32_t selector;};
struct Request {uint64_t key,generation,client;uint32_t pid;bool head,retiring;};
struct Event {uint64_t time,request,client;uint32_t phase,value;};
struct State {
    Client clients[16];Call calls[16];Request requests[16];Event events[64];
    uint64_t serial,token,generation,eventCount,first[5],last[5],lastVsync;
    uint32_t ipc,ipcEnd,ipcError,val,head,copy,ret,reject,unknown,linked,drop;
    uint32_t gate,gateCount,vsync,arm,late,idle,hz;
    bool armed,wanted,saturated;
};
inline void inc(State &s,uint32_t &v){if(v!=UINT32_MAX)++v;else s.saturated=true;}
inline void name(char (&dst)[17],const char *src){unsigned i=0;if(src)for(;i<16 && src[i];++i)dst[i]=src[i];for(;i<17;++i)dst[i]=0;}
inline Client *client(State &s,uint64_t id){for(auto &x:s.clients)if(id && x.id==id)return &x;return nullptr;}
inline Request *request(State &s,uint64_t key){for(auto &x:s.requests)if(key && x.key==key)return &x;return nullptr;}
inline void event(State &s,uint32_t phase,uint64_t now,uint64_t req,uint64_t cli,uint32_t value){
    s.events[s.eventCount%64]={now,req,cli,phase,value};++s.eventCount;
}
inline void stamp(State &s,unsigned stage,uint64_t now){if(!s.first[stage])s.first[stage]=now;s.last[stage]=now;}
inline void open(State &s,uint64_t id,uint32_t pid,const char *comm,uint32_t type,uint32_t status,uint64_t now){
    Client *at=client(s,id);
    if(!at){at=&s.clients[0];for(auto &x:s.clients){if(!x.serial){at=&x;break;}if(x.serial<at->serial)at=&x;}}
    if(at->serial && (!id || at->id!=id))inc(s,s.drop);
    *at={};at->id=id;at->serial=++s.serial;at->opened=now;at->pid=pid;at->type=type;at->status=status;name(at->name,comm);
    event(s,0,now,0,id,status);
}
inline uint64_t begin(State &s,uint64_t id,uint64_t thread,uint32_t selector,uint64_t now){
    if(!id || !thread)return 0;
    for(auto &x:s.calls)if(!x.token){
        x={++s.token,thread,id,selector};inc(s,s.ipc);if(auto *c=client(s,id))inc(s,c->ipc);
        event(s,1,now,0,id,selector);return x.token;
    }
    inc(s,s.drop);return 0;
}
inline void end(State &s,uint64_t token,uint32_t status,uint64_t now){
    if(!token)return;
    for(auto &x:s.calls)if(x.token==token){inc(s,s.ipcEnd);if(status)inc(s,s.ipcError);
        event(s,2,now,0,x.client,status);x={};return;}
    inc(s,s.drop);
}
inline void validate(State &s,uint64_t key,uint64_t thread,bool accepted,uint32_t why,uint64_t now){
    inc(s,s.val);stamp(s,1,now);
    uint64_t id=0,latest=0;
    for(auto &c:s.calls)if(c.token && c.thread==thread && c.token>latest){latest=c.token;id=c.client;}
    auto *owner=client(s,id);if(owner){inc(s,s.linked);inc(s,owner->validated);}else inc(s,s.unknown);
    event(s,3,now,key,id,why);
    if(!accepted){inc(s,s.reject);if(auto *r=request(s,key))*r={};return;}
    if(!key){inc(s,s.drop);return;}
    if(auto *r=request(s,key)){
        if(r->retiring)*r={key,++s.generation,id,owner?owner->pid:0,false,false};
        return;
    }
    for(auto &r:s.requests)if(!r.key){r={key,++s.generation,id,owner?owner->pid:0,false,false};return;}
    inc(s,s.drop);
}
inline void head(State &s,uint64_t key,uint64_t now){
    auto *r=request(s,key);if(!r){inc(s,s.drop);return;}
    if(!r->head){r->head=true;inc(s,s.head);stamp(s,2,now);event(s,4,now,key,r->client,0);}
}
inline void copied(State &s,uint64_t key,uint32_t status,uint64_t now){
    if(!status){inc(s,s.copy);stamp(s,3,now);}
    auto *r=request(s,key);event(s,5,now,key,r?r->client:0,status);
}
inline uint64_t retireBegin(State &s,uint64_t key){auto *r=request(s,key);if(r)r->retiring=true;return r?r->generation:0;}
inline void retireEnd(State &s,uint64_t key,uint64_t generation,uint64_t now){
    inc(s,s.ret);stamp(s,4,now);auto *r=request(s,key);
    event(s,6,now,key,(r && r->generation==generation)?r->client:0,0);
    if(r && generation && r->generation==generation)*r={};
}
inline void gate(State &s,uint32_t bits){s.gate=bits;inc(s,s.gateCount);}
inline void vsync(State &s,unsigned ev,unsigned hz,uint64_t now){
    s.hz=hz;
    if(ev==0){inc(s,s.arm);s.armed=true;s.wanted=true;}
    if(ev==1){inc(s,s.vsync);s.lastVsync=now;s.wanted=true;}
    if(ev==2){inc(s,s.idle);s.armed=false;s.wanted=false;}
    if(ev==3)inc(s,s.late);
    if(ev==6)s.armed=false;
    if(ev==7)s.armed=true;
    if(ev==8)s.armed=false;
}
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Whole lines only, <=88 columns. Leaves room for an explicit omission footer.
#include <stdarg.h>
struct Cdx15Text {
    char *out;size_t capacity,used;unsigned dropped;
    Cdx15Text(char *p,size_t n):out(p),capacity(n),used(0),dropped(0){if(n)out[0]=0;}
    bool line(const char *format,...) __attribute__((format(printf,2,3))) {
        char row[90]={};va_list args;va_start(args,format);int n=vsnprintf(row,sizeof(row),format,args);va_end(args);
        if(n<0 || n>88 || !n || row[n-1]!='\n' || (size_t)n+used+40>=capacity){++dropped;return false;}
        memcpy(out+used,row,(size_t)n);used+=(size_t)n;out[used]=0;return true;
    }
    bool lines(const char *text){bool ok=true;while(*text){const char *end=text;while(*end && *end!='\n')++end;
        size_t n=(size_t)(end-text);char row[90]={};
        if(n>87){++dropped;ok=false;}else{memcpy(row,text,n);row[n]='\n';ok=line("%s",row)&&ok;}
        text=*end?end+1:end;}return ok;
    }
    void footer(unsigned omit,bool clipped){
        if(used>=capacity)return;
        int n=snprintf(out+used,capacity-used,"omit=%u drop=%u clip=%u\n",omit,dropped,(unsigned)clipped);
        if(n>0)used+=(size_t)n<capacity-used?(size_t)n:capacity-used-1;
    }
};

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Appended after Stage14.1 definitions. No fake services or user-client vptr edits.
static IOSimpleLock *cdx15_lock;
static cdx15::State cdx15_state={};
// A serialized snapshot avoids putting the bounded event ring on the kernel stack.
static cdx15::State cdx15_snapshot_state={};static unsigned cdx15_snapshot_busy;
static unsigned cdx15_enabled;
static IOMemoryMap *cdx15_mapping; // one deliberate retained reference until reboot
static uint32_t cdx15_width,cdx15_height;static uint64_t cdx15_stride;
static unsigned cdx15_map_changed;static bool cdx15_target_valid;
static Cdx14Samples cdx15_target={};static uint64_t cdx15_target_sequence;
extern "C" size_t cdx15_daemon_summary(char *,size_t);
static uint64_t cdx15_now(){return mach_absolute_time();}
static bool cdx15_on(){return __atomic_load_n(&cdx15_enabled,__ATOMIC_ACQUIRE)!=0;}
// SPDX-License-Identifier: BSD-2-Clause-Patent
// Same diagnostic lock as Stage15. No new private object fields or queue reads.
struct Cdx16VsyncState {
    uint32_t startAttempts,armAttempts,startReason,armReason,startFlags,armFlags,hz;
};
static Cdx16VsyncState cdx16_vsync={};
static uint64_t cdx16_epoch;
extern "C" void cdx16_vsync_observed(unsigned phase,unsigned reason,unsigned flags,unsigned hz) {
    if(!cdx15_on())return;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    if(phase==0){cdx15::inc(cdx15_state,cdx16_vsync.startAttempts);cdx16_vsync.startReason=reason;cdx16_vsync.startFlags=flags;}
    else {cdx15::inc(cdx15_state,cdx16_vsync.armAttempts);cdx16_vsync.armReason=reason;cdx16_vsync.armFlags=flags;}
    cdx16_vsync.hz=hz;IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}

extern "C" void cdx15_mapping_observed(IOMemoryMap *mapping,uint32_t w,uint32_t h,uint64_t stride) {
    unsigned enabled=(option("luming-display-frame-probe")==1 || option("luming-display-snapshot")==1)?1U:0U;
    PE_parse_boot_argn("luming-display-trace",&enabled,sizeof(enabled));if(enabled!=1)return;
    if(cdx15_mapping){if(cdx15_mapping!=mapping)__atomic_store_n(&cdx15_map_changed,1,__ATOMIC_RELEASE);return;}
    IOSimpleLock *lock=IOSimpleLockAlloc();if(!lock)return;
    mapping->retain();cdx15_mapping=mapping;cdx15_width=w;cdx15_height=h;cdx15_stride=stride;cdx15_lock=lock;
    cdx16_epoch=mach_absolute_time();
    __atomic_store_n(&cdx15_enabled,1,__ATOMIC_RELEASE);
}
extern "C" void cdx15_client_open(task_t task,uint32_t type,IOUserClient *client,IOReturn status) {
    if(!cdx15_on())return;
    proc_t proc=task?(proc_t)get_bsdtask_info(task):nullptr;uint32_t pid=proc?(uint32_t)proc_pid(proc):0;
    char comm[17]={};if(pid)proc_name((int)pid,comm,sizeof(comm));
    uint64_t id=client?client->getRegistryEntryID():0,now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::open(cdx15_state,id,pid,comm,type,(uint32_t)status,now);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
// SPDX-License-Identifier: BSD-2-Clause-Patent
// Bounded observations only. Caller serializes access; no borrowed pointers retained.
namespace cdx17 {
struct Row {
    uint64_t client,first,last;
    uint32_t pid,key,kind,begun,ended,errors,status,inputs,outputs,hasPort;
    uint64_t scalar[3];uint32_t captured;
};
struct Active {uint64_t token,time;uint32_t row,kind;};
struct State {Row rows[64];Active active[32];uint64_t next;uint32_t used,drop;bool saturated;};
inline void inc(State &s,uint32_t &v){if(v==UINT32_MAX)s.saturated=true;else ++v;}
inline Active *find(State &s,uint64_t token,unsigned kind){
    if(token)for(auto &a:s.active)if(a.token==token && a.kind==kind)return &a;return nullptr;
}
inline uint64_t begin(State &s,uint64_t token,uint64_t client,uint32_t pid,
    uint32_t key,unsigned kind,bool port,uint64_t now){
    if(!client || !token)return 0;
    if(find(s,token,kind)){inc(s,s.drop);return 0;}
    Active *slot=nullptr;for(auto &a:s.active)if(!a.token){slot=&a;break;}
    if(!slot){inc(s,s.drop);return 0;}
    unsigned i=0;for(;i<s.used;++i)if(s.rows[i].client==client && s.rows[i].key==key && s.rows[i].kind==kind)break;
    if(i==s.used){if(s.used==64){inc(s,s.drop);return 0;}++s.used;
        s.rows[i]={};s.rows[i].client=client;s.rows[i].pid=pid;s.rows[i].key=key;s.rows[i].kind=kind;s.rows[i].first=now;}
    auto &r=s.rows[i];inc(s,r.begun);r.last=now;r.hasPort=port?1U:0U;
    *slot={token,now,i,kind};return token;
}
inline void arguments(State &s,uint64_t token,uint32_t inputs,uint32_t outputs,
    const uint64_t *values,unsigned count){
    auto *a=find(s,token,0);if(!a)return;auto &r=s.rows[a->row];
    r.inputs=inputs;r.outputs=outputs;r.captured=0;
    if(r.key!=6 && r.key!=72)return;
    if(values)for(unsigned i=0;i<count && i<3;++i){r.scalar[i]=values[i];++r.captured;}
}
inline void end(State &s,uint64_t token,unsigned kind,uint32_t status,uint64_t now){
    if(!token)return;auto *a=find(s,token,kind);if(!a){inc(s,s.drop);return;}
    auto &r=s.rows[a->row];inc(s,r.ended);if(status)inc(s,r.errors);r.status=status;r.last=now;*a={};
}
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
static cdx17::State cdx17_state={},cdx17_snapshot_state={};
extern "C" void cdx17_ipc_arguments(uint64_t token,const IOExternalMethodArguments *args){
    if(!cdx15_on() || !token || !args)return;
    // Only 0..3 scalar values of these kernel-marshalled arguments are read.
    // Lookup first, so unrelated clients never cause argument reads.
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    auto *a=cdx17::find(cdx17_state,token,0);
    if(a){unsigned key=cdx17_state.rows[a->row].key;
        unsigned n=((key==6 || key==72) && args->scalarInput)?args->scalarInputCount:0;
        if(n>3)n=3;
        cdx17::arguments(cdx17_state,token,args->scalarInputCount,args->scalarOutputCount,args->scalarInput,n);}
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" uint64_t cdx17_port_begin(void *object,uint32_t type,unsigned wide,unsigned hasPort){
    if(!cdx15_on() || !object)return 0;
    uint64_t id=static_cast<IOUserClient *>(object)->getRegistryEntryID(),now=cdx15_now(),token=0;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    if(auto *c=cdx15::client(cdx15_state,id)){
        if(cdx17_state.next==UINT64_MAX)cdx17_state.saturated=true;
        else token=cdx17::begin(cdx17_state,++cdx17_state.next,id,c->pid,type,wide?2U:1U,hasPort!=0,now);}
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return token;
}
extern "C" void cdx17_port_end(uint64_t token,unsigned wide,uint32_t status){
    if(!cdx15_on() || !token)return;uint64_t now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx17::end(cdx17_state,token,wide?2U:1U,status,now);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Value-only, bounded records. The adapter owns serialization.
struct Cdx18View {uint32_t valid,completed,current,queued;};
namespace cdx18 {
struct Wait {uint64_t token,client;uint32_t pid,id,flags,timeout,status,done;
    Cdx18View pre,post;};
struct Completion {uint64_t token;uint32_t id,raw32c,done;Cdx18View pre,post;};
struct State {Wait waits[16];Completion completions[8];uint64_t next;
    uint32_t nw,nc,lost,unmatched;bool saturated;};
inline void inc(State &s,uint32_t &v){if(v==UINT32_MAX)s.saturated=true;else ++v;}
inline uint64_t next(State &s){if(s.next==UINT64_MAX){s.saturated=true;inc(s,s.lost);return 0;}return ++s.next;}
inline uint64_t waitBegin(State &s,uint64_t client,uint32_t pid,uint32_t id,
    uint32_t flags,uint32_t timeout,const Cdx18View &pre){
    if(s.nw==16){inc(s,s.lost);return 0;}uint64_t token=next(s);if(!token)return 0;
    auto &r=s.waits[s.nw++];r={};r.token=token;r.client=client;r.pid=pid;
    r.id=id;r.flags=flags;r.timeout=timeout;r.pre=pre;return token;
}
inline void waitEnd(State &s,uint64_t token,uint32_t status,const Cdx18View &post){
    if(!token)return;for(auto &r:s.waits)if(r.token==token && !r.done){r.status=status;r.post=post;r.done=1;return;}
    inc(s,s.unmatched);
}
inline uint64_t doneBegin(State &s,uint32_t id,uint32_t raw32c,const Cdx18View &pre){
    if(s.nc==8){inc(s,s.lost);return 0;}uint64_t token=next(s);if(!token)return 0;
    auto &r=s.completions[s.nc++];r={};r.token=token;r.id=id;r.raw32c=raw32c;r.pre=pre;return token;
}
inline void doneEnd(State &s,uint64_t token,const Cdx18View &post){
    if(!token)return;for(auto &r:s.completions)if(r.token==token && !r.done){r.post=post;r.done=1;return;}
    inc(s,s.unmatched);
}
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
static cdx18::State cdx18_state={},cdx18_snapshot_state={};
extern "C" uint64_t cdx18_wait_begin(IOUserClient *client,uint32_t id,uint32_t flags,
    uint32_t timeout,const Cdx18View *pre){
    if(!cdx15_on() || !pre)return 0;
    uint64_t entry=client?client->getRegistryEntryID():0,token=0;uint32_t pid=0;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    if(auto *c=cdx15::client(cdx15_state,entry))pid=c->pid;
    token=cdx18::waitBegin(cdx18_state,entry,pid,id,flags,timeout,*pre);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return token;
}
extern "C" void cdx18_wait_end(uint64_t token,uint32_t status,const Cdx18View *post){
    if(!cdx15_on() || !token || !post)return;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx18::waitEnd(cdx18_state,token,status,*post);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" uint64_t cdx18_done_begin(uint32_t id,uint32_t raw32c,const Cdx18View *pre){
    if(!cdx15_on() || !pre)return 0;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    uint64_t token=cdx18::doneBegin(cdx18_state,id,raw32c,*pre);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return token;
}
extern "C" void cdx18_done_end(uint64_t token,const Cdx18View *post){
    if(!cdx15_on() || !token || !post)return;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx18::doneEnd(cdx18_state,token,*post);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}

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

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Bounded joins over validated COPIED kcdata; no live pointers or kernel locks.
namespace cdx21 {
using cdx19::u32;using cdx19::u64;using cdx19::Thread;
struct Identity {uint64_t tid,unique;uint32_t pid,state;char comm[32];};
struct Owner {uint64_t tid,firstWaiter;Identity id;Thread thread;uint32_t matches,found,source;};
struct Turn {uint64_t waiter,context,flags;int32_t label;uint32_t version;};
struct Label {int32_t id;uint32_t flags,domain;char name[64];};
struct Relations {
    Identity index[1024];Owner owners[24];
    uint32_t count,overflow,n,omitted,passes,valid,error,depthLimited;
    Turn turns[256];Label labels[64];uint32_t nt,nl,turnOverflow,labelOverflow;
};
// The same integer means a TID for an unfair lock, a local name for receive,
// and sometimes a PID for send. Never join an untyped owner.
inline const char *kind(const Thread &t){
    if(!t.waitinfo)return "absent";
    if(t.owner>=~uint64_t(0)-7)return "sentinel";
    if(!t.owner)return "unknown";
    if(t.kind==1 || t.kind==10 || t.kind==18)return "tid";
    if(t.kind==2)return "portname";
    if(t.kind==4)return "pid";
    return "opaque";
}
inline bool request(Relations &r,const Thread &t,uint32_t source=1){
    if(strcmp(kind(t),"tid"))return false;
    for(unsigned i=0;i<r.n;++i)if(r.owners[i].tid==t.owner){r.owners[i].source|=source;return false;}
    if(r.n==24){++r.omitted;return false;}
    auto &o=r.owners[r.n++];o.tid=t.owner;o.firstWaiter=t.tid;o.source=source;return true;
}
inline Owner *find(Relations &r,uint64_t tid){
    for(unsigned i=0;i<r.n;++i)if(r.owners[i].tid==tid)return &r.owners[i];return nullptr;
}
// Structural validation is supplied by cdx19::parse before this decoder runs.
// Still check every length/count read here, including skipped array elements.
inline bool scan(const void *buffer,size_t length,Relations &r,bool indexing){
    const auto *b=static_cast<const unsigned char *>(buffer);size_t at=0;
    Identity id={};Thread thread={};bool task=false,have=false,inside=false;int label=-1;bool labelScope=false;
    while(at<length){
        if(length-at<16)return false;
        uint32_t type=u32(b+at),size=u32(b+at+4);uint64_t flags=u64(b+at+8);
        if(size>length-at-16)return false;
        const auto *d=b+at+16;at+=16+size;
        if(type==0x13){if(size<4)return false;auto c=u32(d);
            if(c==0x903){task=false;id={};}if(c==0x904){have=false;inside=true;thread={};}
            if(c==0x934){label=-1;labelScope=true;}continue;}
        if(type==0x14){
            if(inside && have){
                id.tid=thread.tid;id.state=thread.state;
                if(indexing){if(r.count<1024)r.index[r.count++]=id;else ++r.overflow;}
                else if(auto *o=find(r,thread.tid)){
                    ++o->matches;if(o->matches==1){o->id=id;o->thread=thread;o->found=1;}
                    else o->found=0; // never pick one of duplicate TIDs
                }
            }
            inside=false;have=false;labelScope=false;label=-1;continue;
        }
        if(type==0x905){if(size<120)return false;id={};id.unique=u64(d);id.pid=u32(d+84);
            memcpy(id.comm,d+88,31);id.comm[31]=0;task=true;continue;}
        if(type==0x906){if(size<104 || !task || !inside)return false;
            thread.tid=u64(d);thread.wait=u64(d+8);thread.continuation=u64(d+16);
            thread.flags=u64(d+64);thread.state=u32(d+88);have=true;continue;}
        if(indexing && type==0x935 && labelScope){
            if(size<5)return false;
            if(r.nl==64){++r.labelOverflow;continue;}
            label=int(r.nl++);auto &l=r.labels[label];int16_t v;uint16_t f;
            memcpy(&v,d,2);memcpy(&f,d+2,2);l.id=v;l.flags=f;l.domain=d[4];continue;
        }
        if(indexing && type==0x936 && labelScope && label>=0){
            unsigned j=0;for(;j<size && j<63 && d[j];++j)r.labels[label].name[j]=char(d[j]);
            r.labels[label].name[j]=0;continue;
        }
        if(type!=0x11 && !(type>=0x20 && type<=0x2f))continue;
        uint32_t elem=uint32_t(flags>>32),count=uint32_t(flags);size_t step=0,bytes=0;
        if(type==0x11){
            if(elem==0x90b || elem==0x90d)step=16;else if(elem==0x914 || elem==0x916)step=8;else continue;
            if(count>size/step || size-size_t(count)*step>=16)return false;
        }else{
            unsigned pad=type&15;if(pad>size)return false;bytes=size-pad;
            if(!count){if(bytes)return false;continue;}
            if(bytes%count)return false;step=bytes/count;if(!step)return false;
        }
        if(!indexing && inside && have && find(r,thread.tid) &&
           (elem==0x90b || elem==0x90d || elem==0x914 || elem==0x916)){
            size_t need=(elem==0x90b || elem==0x90d)?16:8;if(step!=need)return false;
            bool k=elem==0x90b || elem==0x914;unsigned limit=k?4:32,n=count<limit?count:limit;
            for(unsigned j=0;j<n;++j)(k?thread.k:thread.u)[j]=u64(d+size_t(j)*step);
            if(k)thread.nk=count;else thread.nu=count;
        }
        if(!indexing && elem==0x91d){
            if(step!=25 && step!=31)return false;
            for(unsigned j=0;j<count;++j){const auto *w=d+size_t(j)*step;
                if(auto *o=find(r,u64(w+8))){auto &t=o->thread;
                    t.waitinfo=1;t.owner=u64(w);t.context=u64(w+16);t.kind=w[24];t.waitbytes=uint32_t(step);
                    if(step==31){int16_t label;memcpy(&label,w+25,2);t.portlabel=label;t.waitflags=u32(w+27);}
                }
            }
        }
        if(indexing && elem==0x929){
            if(step!=26 && step!=28)return false;
            for(unsigned j=0;j<count;++j){const auto *w=d+size_t(j)*step;
                if(r.nt==256){++r.turnOverflow;continue;}
                auto &t=r.turns[r.nt++];t.waiter=u64(w);t.context=u64(w+8);t.flags=u64(w+18);
                t.version=uint32_t(step);t.label=0;
                if(step==28){int16_t l;memcpy(&l,w+26,2);t.label=l;}
            }
        }
    }
    return at==length;
}
inline bool turnRequest(Relations &r,uint64_t waiter){
    for(unsigned i=0;i<r.nt;++i){const auto &t=r.turns[i];
        if(t.waiter==waiter && (t.flags&8) && !(t.flags&(1|2|4|16|32))){
            Thread synthetic={};synthetic.tid=waiter;synthetic.waitinfo=1;synthetic.kind=10;synthetic.owner=t.context;return request(r,synthetic,2);
        }
    }return false;
}
inline bool collect(const void *b,size_t n,const cdx19::Sample &s,Relations &r){
    // These stores target static storage. Aggregate assignment at -O0 can
    // materialize an 82KiB temporary on the small kernel thread stack.
    memset(&r,0,sizeof(r));if(!s.parsed){r.error=1;return false;}
    if(!scan(b,n,r,true)){r.error=2;return false;}
    // lsd waits first, followed by the other targets; capacity omissions explicit.
    const unsigned order[]={3,4,1,0,2};
    for(unsigned p:order){const auto &proc=s.processes[p];if(proc.matches!=1 || (p>=3 && s.lsdInstances>2))continue;
        for(unsigned i=0;i<proc.n;++i){request(r,proc.threads[i]);turnRequest(r,proc.threads[i].tid);}}
    for(unsigned depth=0;depth<3;++depth){
        unsigned before=r.n;
        for(unsigned i=0;i<r.n;++i){r.owners[i].matches=0;r.owners[i].found=0;r.owners[i].thread={};}
        if(!scan(b,n,r,false)){r.error=3;return false;}++r.passes;
        // Append only after completing this scan, so task order cannot affect it.
        for(unsigned i=0;i<before;++i)if(r.owners[i].found){request(r,r.owners[i].thread);turnRequest(r,r.owners[i].tid);}
        if(r.n==before){r.valid=1;return true;}
    }
    r.depthLimited=1;r.valid=1;return true;
}
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Exactly the kernel-consumer declaration in the pinned osfmk/kern/debug.h.
// Linked to the source-built kernel, never an address in the IPSW graphics kext.
extern "C" kern_return_t stack_snapshot_from_kernel(int,void *,uint32_t,uint64_t,uint64_t,uint32_t,unsigned *);
static cdx19::Sample cdx19_samples[2]={};
static cdx21::Relations cdx21_samples[2]={};
static uint32_t cdx21_saved[2]={};
static unsigned cdx19_busy,cdx19_taken;
static constexpr uint32_t cdx19_capacity=4U*1024U*1024U;
// KCData + UUID load info + trylock + no I/O stats + wait owners + no latency
// + skip Exclaves. No faulting, no compression, no task/thread suspension API.
static constexpr uint64_t cdx19_flags=0x10000ULL|0x2ULL|0x8ULL|0x100000ULL|
    0x800000ULL|0x1000000ULL|0x40000000ULL|0x400000000ULL;
extern "C" bool cdx19_capture_next(void){
    if(option("luming-display-stackshot")!=1)return false;
    unsigned expected=0;
    if(!__atomic_compare_exchange_n(&cdx19_busy,&expected,1,false,__ATOMIC_ACQUIRE,__ATOMIC_RELAXED))return false;
    unsigned index=cdx19_taken;
    if(index>=2){__atomic_store_n(&cdx19_busy,0,__ATOMIC_RELEASE);return false;}
    auto &s=cdx19_samples[index];memset(&s,0,sizeof(s));s.begin=mach_absolute_time();s.flags=cdx19_flags;
    // This runs only in the independent thread_call, BEFORE quiesce or any
    // diagnostic lock. Stackshot itself owns debugger rendezvous/serialization.
    if(ml_at_interrupt_context() || !ml_get_interrupts_enabled()){s.rc=0xffff0001U;}
    else if(void *buffer=IOMalloc(cdx19_capacity)){
        bzero(buffer,cdx19_capacity);unsigned used=0;
        s.rc=(uint32_t)stack_snapshot_from_kernel(-1,buffer,cdx19_capacity,cdx19_flags,0,0,&used);
        s.bytes=used;
        if(!s.rc && used && used<=cdx19_capacity){
            (void)cdx19::parse(buffer,used,s);
            (void)cdx21::collect(buffer,used,s,cdx21_samples[index]);
            if(activeLegacyDisplay){OSData *rel=OSData::withBytes(&cdx21_samples[index],sizeof(cdx21::Relations));
                if(rel){cdx21_saved[index]=activeLegacyDisplay->setProperty(index?"CDX21State1":"CDX21State0",rel)?1U:0U;rel->release();}}
            // Preserve original uncompressed kcdata even if our decoder fails.
            // Property failure is visible; it does not invalidate parsed rows.
            if(activeLegacyDisplay){OSData *data=OSData::withBytes(buffer,used);
                if(data){s.stored=activeLegacyDisplay->setProperty(index?"CDX19Raw1":"CDX19Raw0",data)?1U:0U;data->release();}}
        }else if(!s.rc){s.error=23;}
        IOFree(buffer,cdx19_capacity);
    }else {s.rc=0xffff0002U;}
    s.end=mach_absolute_time();
    if(activeLegacyDisplay){OSData *data=OSData::withBytes(&s,sizeof(s));
        if(data){activeLegacyDisplay->setProperty(index?"CDX19State1":"CDX19State0",data);data->release();}}
    cdx19_taken=index+1;__atomic_store_n(&cdx19_busy,0,__ATOMIC_RELEASE);
    return index==0;
}
// SPDX-License-Identifier: BSD-2-Clause-Patent
// One compact report for both copied samples. Full owners/labels stay in State.
static void cdx21_format(Cdx15Text &text,bool quiet,uint32_t copies,uint32_t retired){
    text.line("CDX21 q=%u cp=%u ret=%u export=0 jobs=?\n",unsigned(quiet),copies,retired);
    const char *names[]={"BB","SB","LD","L1","L2"};
    for(unsigned p=0;p<5;++p){const auto &a=cdx19_samples[0];const auto &b=cdx19_samples[1];
        const auto &x=a.processes[p];const auto &y=b.processes[p];
        if(!a.parsed || !b.parsed || !x.n || !y.n || x.matches!=1 || y.matches!=1 ||
           (p>=3 && (a.lsdInstances>2 || b.lsdInstances>2))){text.line("%s unavailable/ambiguous\n",names[p]);continue;}
        text.line("%s p=%u/%u w=%u/%u o=%llx/%llx\n",names[p],x.pid,y.pid,x.threads[0].kind,y.threads[0].kind,
            (unsigned long long)x.threads[0].owner,(unsigned long long)y.threads[0].owner);
    }
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];const auto &r=cdx21_samples[i];
        uint64_t nanos=0;if(s.begin>=cdx16_epoch)absolutetime_to_nanoseconds(s.begin-cdx16_epoch,&nanos);
        text.line("S%u ms=%llu ok=%u rel=%u save=%u ov=%u dep=%u\n",i,(unsigned long long)(nanos/1000000),s.parsed,r.valid,cdx21_saved[i],r.overflow,r.depthLimited);
        if(!s.parsed || !r.valid)continue;
        if(!r.n){text.line("O%u unavailable\n",i);continue;}
        unsigned focus=option("luming-display-stack-owner");if(focus>=r.n){text.line("O%u slot=unavailable\n",i);continue;}
        const auto &o=r.owners[focus];
        if(!o.found){text.line("O%u tid=%llx unavailable matches=%u\n",i,(unsigned long long)o.tid,o.matches);continue;}
        text.line("O%u p=%u t=%llx w=%u src=%u\n",i,o.id.pid,(unsigned long long)o.tid,o.thread.kind,o.source);
        unsigned f=option("luming-display-stack-frame");if(f>28)f=28;
        if(o.thread.nu<=f)text.line("U%u n=%u f=%u unavailable\n",i,o.thread.nu,f);
        else if(o.thread.nu==f+1)text.line("U%u n=%u f=%u %llx/end\n",i,o.thread.nu,f,(unsigned long long)o.thread.u[f]);
        else text.line("U%u n=%u f=%u %llx/%llx\n",i,o.thread.nu,f,(unsigned long long)o.thread.u[f],(unsigned long long)o.thread.u[f+1]);
    }
    unsigned omitted=0;
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];const auto &r=cdx21_samples[i];
        omitted+=r.omitted+r.overflow+r.turnOverflow+r.labelOverflow+(r.n?r.n-1:0);
        for(const auto &p:s.processes)if(p.total)omitted+=p.total-1;
    }
    text.footer(omitted,false);
}

// SPDX-License-Identifier: BSD-2-Clause-Patent
// Root selection follows a typed lsd wait; an owner slot is not an identity.
static const cdx19::Thread *cdx22_root(const cdx19::Process &p,unsigned ordinal){
    const unsigned kinds[]={18,10,1};
    for(unsigned k:kinds)for(unsigned j=0;j<p.n;++j){const auto &t=p.threads[j];
        if(t.kind!=k || strcmp(cdx21::kind(t),"tid"))continue;
        if(!ordinal)return &t;--ordinal;
    }
    return nullptr;
}
static const cdx21::Owner *cdx22_follow(cdx21::Relations &r,const cdx19::Thread &root,
                                    unsigned hop,const char **why){
    uint64_t seen[24]={};unsigned n=0;const cdx19::Thread *waiter=&root;
    for(unsigned depth=0;depth<=hop;++depth){
        if(strcmp(cdx21::kind(*waiter),"tid")){*why="next-not-tid";return nullptr;}
        for(unsigned j=0;j<n;++j)if(seen[j]==waiter->owner){*why="cycle";return nullptr;}
        if(n==24){*why="limit";return nullptr;}seen[n++]=waiter->owner;
        const auto *o=cdx21::find(r,waiter->owner);
        if(!o){*why="not-retained";return nullptr;}
        if(!o->found || o->matches!=1){*why=o->matches>1?"ambiguous":"not-found";return nullptr;}
        if(depth==hop)return o;
        waiter=&o->thread;
    }*why="unavailable";return nullptr;
}
static void cdx22_frames(Cdx15Text &text,unsigned i,const cdx19::Thread &t,unsigned frame){
    // Retain original raw counts, print only initialized copied entries.
    if(!t.nk)text.line("K%u n=0 c=%llx unavailable\n",i,(unsigned long long)t.continuation);
    else if(t.nk==1)text.line("K%u keep=1 c=%llx %llx/end\n",i,(unsigned long long)t.continuation,(unsigned long long)t.k[0]);
    else text.line("K%u keep=2 c=%llx %llx/%llx\n",i,(unsigned long long)t.continuation,(unsigned long long)t.k[0],(unsigned long long)t.k[1]);
    if(t.nu<=frame)text.line("U%u n=%u f=%u unavailable\n",i,t.nu,frame);
    else if(t.nu==frame+1)text.line("U%u n=%u f=%u %llx/end\n",i,t.nu,frame,(unsigned long long)t.u[frame]);
    else text.line("U%u n=%u f=%u %llx/%llx\n",i,t.nu,frame,(unsigned long long)t.u[frame],(unsigned long long)t.u[frame+1]);
}
static void cdx22_format(Cdx15Text &text,bool quiet,uint32_t copies,uint32_t retired){
    unsigned instance=option("luming-display-stack-step");if(instance>1)instance=0;
    unsigned ordinal=option("luming-display-stack-thread");if(ordinal>7)ordinal=0;
    unsigned hop=option("luming-display-stack-owner");if(hop>23)hop=23;
    unsigned frame=option("luming-display-stack-frame");if(frame>28)frame=28;
    text.line("CDX22 q=%u cp=%u ret=%u ls=%u r=%u h=%u\n",unsigned(quiet),copies,retired,instance+1,ordinal,hop);
    unsigned omitted=0;
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];auto &r=cdx21_samples[i];
        uint64_t ns=0;if(s.begin>=cdx16_epoch)absolutetime_to_nanoseconds(s.begin-cdx16_epoch,&ns);
        text.line("S%u ms=%llu v=%u/%u x=%u d=%u\n",i,(unsigned long long)(ns/1000000),s.parsed,r.valid,r.overflow,r.depthLimited);
        if(!s.parsed || !r.valid){text.line("R%u snapshot-unavailable\n",i);continue;}
        const auto &p=s.processes[3+instance];
        if(s.lsdInstances>2 || p.matches!=1 || !p.n){text.line("R%u lsd-unavailable/ambiguous\n",i);continue;}
        const auto *root=cdx22_root(p,ordinal);
        if(!root){text.line("R%u no-typed-root kept=%u total=%u\n",i,p.n,p.total);continue;}
        text.line("R%u p=%u t=%llx w=%u o=%llx\n",i,p.pid,(unsigned long long)root->tid,root->kind,(unsigned long long)root->owner);
        const char *why="unavailable";const auto *o=cdx22_follow(r,*root,hop,&why);
        if(!o){text.line("O%u %s\n",i,why);continue;}
        text.line("O%u p=%u t=%llx w=%u o=%llx\n",i,o->id.pid,(unsigned long long)o->tid,o->thread.kind,(unsigned long long)o->thread.owner);
        char comm[9]={};for(unsigned j=0;j<8 && o->id.comm[j];++j)comm[j]=o->id.comm[j];
        text.line("N%u %s u=%llx s=%u\n",i,comm,(unsigned long long)o->id.unique,o->source);
        cdx22_frames(text,i,o->thread,frame);
        omitted+=r.n?r.n-1:0;if(p.total)omitted+=p.total-1;
    }
    text.footer(omitted,false);
}

static void cdx19_format(Cdx15Text &text,bool quiet,uint32_t copies,uint32_t retired){
    unsigned page=option("luming-display-stack-page");if(page==6){cdx22_format(text,quiet,copies,retired);return;}if(page==5){cdx21_format(text,quiet,copies,retired);return;}if(page>4)page=0;
    unsigned selected=option("luming-display-stack-thread");if(selected>7)selected=0;
    unsigned first=option("luming-display-stack-frame");if(first>28)first=28;
    unsigned step=option("luming-display-stack-step");if(step>28)step=28;
    text.line("CDX19 rev=22 pg=%u th=%u quiet=%u cp=%u ret=%u\n",page,selected,(unsigned)quiet,copies,retired);
    text.line("k=unslid w=unslid-or-perm sc=unavailable nofault\n");
    if(page>=3)text.line("target=lsd instance=%u domain=unknown\n",page-2);
    unsigned missing=0;
    for(unsigned i=0;i<2;++i){const auto &s=cdx19_samples[i];
        unsigned frame=first+(i?step:0);if(frame>28)frame=28;
        uint64_t nanos=0;if(s.begin>=cdx16_epoch)absolutetime_to_nanoseconds(s.begin-cdx16_epoch,&nanos);
        text.line("S%u ms=%llu rc=%x b=%u ok=%u err=%u raw=%u\n",i,
            (unsigned long long)(nanos/1000000),s.rc,s.bytes,s.parsed,s.error,s.stored);
        if(i>=cdx19_taken || !s.parsed){text.line("P%u stack=unavailable\n",i);continue;}
        const auto &p=s.processes[page];
        if(page>=3 && s.lsdInstances>2){text.line("P%u lsd-overflow=%u unavailable\n",i,s.lsdInstances-2);continue;}
        if(!p.seen){text.line("P%u process=not-found\n",i);continue;}
        if(p.matches>1){text.line("P%u ambiguous names=%u pid=%u/%u\n",i,p.matches,p.pid,p.otherpid);continue;}
        text.line("P%u p=%u n=%u r=%u w=%u ui=%u\n",i,p.pid,p.total,p.run,p.wait,p.unint);
        if(selected>=p.n){text.line("T%u thread=unavailable\n",i);continue;}
        // One selected thread on screen per sample; all eight retained in State.
        // Preserve the distinction between wait-info absent and type zero.
        const auto &t=p.threads[selected];missing+=p.total-1;
        text.line("T%u id=%llx st=%x fl=%llx wt=%u/%u\n",i,(unsigned long long)t.tid,t.state,
            (unsigned long long)t.flags,t.waitinfo,t.kind);
        // Kernel frames remain in State; give screen space to four user LRs.
        text.line("K%u c=%llx n=%u\n",i,(unsigned long long)t.continuation,t.nk);
        if(t.nu>frame)text.line("U%u n=%u f=%u %llx/%llx/%llx/%llx\n",i,t.nu,frame,
            (unsigned long long)t.u[frame],(unsigned long long)t.u[frame+1],
            (unsigned long long)t.u[frame+2],(unsigned long long)t.u[frame+3]);
        else text.line("U%u stack=unavailable\n",i);
        if(!t.waitinfo)text.line("W%u unavailable w=%llx\n",i,(unsigned long long)t.wait);
        else if(t.waitbytes==31)text.line("W%u t=%u f=%x l=%d owner=%llx cx=%llx\n",i,t.kind,
            t.waitflags,(int)t.portlabel,(unsigned long long)t.owner,(unsigned long long)t.context);
        else text.line("W%u t=%u f=? l=? owner=%llx cx=%llx\n",i,t.kind,
            (unsigned long long)t.owner,(unsigned long long)t.context);
    }
    const auto &s=cdx19_samples[cdx19_taken==2?1:0];const auto &p=s.processes[page];
    const unsigned char *uuid=p.cacheValid?p.uuid:s.uuid;uint64_t slide=p.cacheValid?p.cacheSlide:s.cacheSlide;
    bool valid=s.parsed && (p.cacheValid || s.cacheValid);char hex[33]={};
    for(unsigned i=0;i<16;++i){const char digits[]="0123456789abcdef";hex[2*i]=digits[uuid[i]>>4];hex[2*i+1]=digits[uuid[i]&15];}
    text.line("cache=%u sl=%llx uuid=%s\n",(unsigned)valid,(unsigned long long)slide,hex);
    text.footer(missing,false);
}

extern "C" uint64_t cdx15_ipc_begin(void *object,uint32_t selector) {
    if(!cdx15_on() || !object)return 0;
    IOUserClient *client=static_cast<IOUserClient *>(object);
    uint64_t id=client->getRegistryEntryID(),now=cdx15_now(),thread=(uintptr_t)current_thread(),token=0;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    if(auto *c=cdx15::client(cdx15_state,id)){
        token=cdx15::begin(cdx15_state,id,thread,selector,now);
        if(token)cdx17::begin(cdx17_state,token,id,c->pid,selector,0,false,now);
    }
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return token;
}
extern "C" void cdx15_ipc_end(uint64_t token,uint32_t status) {
    if(!cdx15_on() || !token)return;uint64_t now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx17::end(cdx17_state,token,0,status,now);
    cdx15::end(cdx15_state,token,status,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_validation(const void *request,bool accepted,uint32_t reason) {
    if(!cdx15_on())return;uint64_t now=cdx15_now(),thread=(uintptr_t)current_thread();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::validate(cdx15_state,(uintptr_t)request,thread,accepted,reason,now);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_head(const void *request) {
    if(!cdx15_on())return;uint64_t now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::head(cdx15_state,(uintptr_t)request,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_copy(const void *request,uint32_t status) {
    if(!cdx15_on())return;uint64_t now=cdx15_now();
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::copied(cdx15_state,(uintptr_t)request,status,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" uint64_t cdx15_retire_begin(const void *request) {
    if(!cdx15_on())return 0;IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    uint64_t generation=cdx15::retireBegin(cdx15_state,(uintptr_t)request);
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);return generation;
}
extern "C" void cdx15_retire_end(const void *request,uint64_t generation) {
    if(!cdx15_on())return;uint64_t now=cdx15_now();IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::retireEnd(cdx15_state,(uintptr_t)request,generation,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_gate(uint32_t bits) {
    if(!cdx15_on())return;IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::gate(cdx15_state,bits);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_vsync(unsigned event,unsigned hz) {
    if(!cdx15_on())return;uint64_t now=cdx15_now();IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15::vsync(cdx15_state,event,hz,now);IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
extern "C" void cdx15_target_observed(void) {
    if(!cdx15_on() || __atomic_load_n(&cdx15_map_changed,__ATOMIC_ACQUIRE))return;
    Cdx14Samples sample={};
    bool valid=cdx14_samples(reinterpret_cast<const volatile void *>(cdx15_mapping->getVirtualAddress()),
        cdx15_mapping->getLength(),cdx15_stride,cdx15_width,cdx15_height,&sample);
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    cdx15_target_valid=valid;if(valid){cdx15_target=sample;++cdx15_target_sequence;}
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
}
static unsigned cdx15_cap(uint64_t value,unsigned limit,bool &clipped){if(value>limit){clipped=true;return limit;}return (unsigned)value;}
static unsigned cdx15_ms(uint64_t ticks,bool &clipped){
    if(!ticks)return 0;
    if(ticks<cdx16_epoch){clipped=true;return 0;}
    uint64_t ns=0;absolutetime_to_nanoseconds(ticks-cdx16_epoch,&ns);return cdx15_cap(ns/1000000,999999,clipped);
}
static int cdx15_service(const char *name,char (&cls)[17]) {
    cls[0]=0;OSDictionary *matching=IOService::serviceMatching(name);if(!matching)return -1;
    IOService *service=IOService::copyMatchingService(matching);matching->release();
    if(!service)return 0;
    cdx15::name(cls,service->getMetaClass()->getClassName());service->release();return 1;
}
extern "C" void cdx15_snapshot(char *out,size_t capacity,bool quiet) {
    Cdx15Text text(out,capacity);bool clipped=false;
    if(!cdx15_on()){text.line("CDX15 trace=unavailable\n");text.footer(0,false);return;}
    unsigned expected=0;
    if(!__atomic_compare_exchange_n(&cdx15_snapshot_busy,&expected,1,false,__ATOMIC_ACQUIRE,__ATOMIC_RELAXED)){
        text.line("CDX15 snapshot=busy\n");text.footer(0,false);return;
    }
    struct Lease {~Lease(){__atomic_store_n(&cdx15_snapshot_busy,0,__ATOMIC_RELEASE);}} lease;
    cdx15::State &state=cdx15_snapshot_state;Cdx16VsyncState pacing;Cdx14Samples last;bool targetValid;uint64_t seq;
    IOInterruptState irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);
    state=cdx15_state;pacing=cdx16_vsync;last=cdx15_target;targetValid=cdx15_target_valid;seq=cdx15_target_sequence;
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
    bool mapValid=!__atomic_load_n(&cdx15_map_changed,__ATOMIC_ACQUIRE);
    Cdx14Samples late={};bool lateValid=quiet && targetValid && mapValid && cdx15_mapping &&
        cdx14_samples(reinterpret_cast<const volatile void *>(cdx15_mapping->getVirtualAddress()),cdx15_mapping->getLength(),
            cdx15_stride,cdx15_width,cdx15_height,&late);
    char wd[17]={},aks[17]={},alt[17]={};int watchdog=cdx15_service("IOWatchdog",wd);
    int keyStore=cdx15_service("AppleKeyStore",aks),alternate=cdx15_service("AppleARMWatchdogTimer",alt);
    char daemon[352]={};cdx15_daemon_summary(daemon,sizeof(daemon));
    // All full counters, timestamps, clients and bounded events remain available as data.
    if(activeLegacyDisplay){OSData *data=OSData::withBytes(&state,sizeof(state));
        if(data){activeLegacyDisplay->setProperty("CDX15TraceState",data);data->release();}}
    if(option("luming-display-stackshot")==1){
        cdx19_format(text,quiet,state.copy,state.ret);return;
    }
    if(option("luming-display-wait-probe")==1){
        cdx18::State &s=cdx18_snapshot_state;
        irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);s=cdx18_state;
        IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
        if(activeLegacyDisplay){OSData *data=OSData::withBytes(&s,sizeof(s));
            if(data){activeLegacyDisplay->setProperty("CDX18WaitState",data);data->release();}}
        text.line("CDX18 quiet=%u cp=%u ret=%u waits=%u done=%u\n",(unsigned)quiet,state.copy,state.ret,s.nw,s.nc);
        text.line("lost=%u unmatched=%u seq=%llx boundary-samples\n",s.lost,s.unmatched,(unsigned long long)s.next);
        unsigned shown=0,total=2*s.nw+s.nc;
        // Completion rows first: values came from a live request before the
        // original completion; post contains only the provider object's words.
        for(unsigned i=0;i<s.nc;++i){const auto &r=s.completions[i];
            if(text.line("D%llx i=%x x=%x d=%u v=%u/%u c=%x/%x\n",
                (unsigned long long)r.token,r.id,r.raw32c,r.done,r.pre.valid,r.post.valid,r.pre.completed,r.post.completed))++shown;
        }
        for(unsigned i=0;i<s.nw;++i){const auto &r=s.waits[i];
            if(text.line("W%llx p%u i=%x f=%x t=%x r=%x d=%u\n",
                (unsigned long long)r.token,r.pid,r.id,r.flags,r.timeout,r.status,r.done))++shown;
            if(text.line("W%llx v=%u/%u c=%x/%x h=%u/%u q=%u/%u\n",(unsigned long long)r.token,r.pre.valid,r.post.valid,
                r.pre.completed,r.post.completed,r.pre.current,r.post.current,r.pre.queued,r.post.queued))++shown;
        }
        text.footer(total-shown,clipped||s.saturated||state.saturated);return;
    }

    if(option("luming-display-ipc-page")!=2){
// SPDX-License-Identifier: BSD-2-Clause-Patent
// Same quiesce/late-sample boundary as Stage16. Dedicated IPC page, <=660B.
    cdx17::State &calls=cdx17_snapshot_state;
    irq=IOSimpleLockLockDisableInterrupt(cdx15_lock);calls=cdx17_state;
    IOSimpleLockUnlockEnableInterrupt(cdx15_lock,irq);
    if(activeLegacyDisplay){OSData *data=OSData::withBytes(&calls,sizeof(calls));
        if(data){activeLegacyDisplay->setProperty("CDX17IPCState",data);data->release();}}
    unsigned page=option("luming-display-ipc-page");
    text.line("CDX17 pg=%u quiet=%u cp=%u ret=%u\n",page,(unsigned)quiet,state.copy,state.ret);
    text.line("ipc=%u end=%u err=%u loss=%u vst=%u ar=%u vs=%u\n",state.ipc,state.ipcEnd,state.ipcError,
        calls.drop,pacing.startReason,pacing.armReason,state.vsync);
    unsigned pending=0,ports=0;for(const auto &a:calls.active)if(a.token)++pending;
    for(unsigned i=0;i<calls.used;++i)if(calls.rows[i].kind)ports+=calls.rows[i].begun;
    text.line("pending=%u portRPC=%u rows=%u\n",pending,ports,calls.used);
    // n=entered,d=returned,f=nonzero returns,r=last return; P/Q=32/64-bit port RPC.
    unsigned shown=0,total=0;
    if(!page){
        for(unsigned i=0;i<calls.used;++i){const auto &r=calls.rows[i];++total;
            if(text.line("p%u %c%u n%u d%u f%u r%x b%u\n",r.pid,r.kind==1?'P':r.kind==2?'Q':'s',
                r.key,r.begun,r.ended,r.errors,r.status,r.hasPort))++shown;}
    }else{
        for(unsigned i=0;i<calls.used;++i){const auto &r=calls.rows[i];
            if(!r.kind && (r.key==6 || r.key==72)){++total;
                if(text.line("p%u s%u in%u out%u got%u\n",r.pid,r.key,r.inputs,r.outputs,r.captured))++shown;
                text.line("a=%llx/%llx/%llx\n",(unsigned long long)r.scalar[0],
                    (unsigned long long)r.scalar[1],(unsigned long long)r.scalar[2]);}}
        for(const auto &a:calls.active)if(a.token){const auto &r=calls.rows[a.row];++total;
            unsigned age=cdx15_ms(mach_absolute_time(),clipped)-cdx15_ms(a.time,clipped);
            if(text.line("pending p%u k%u s%u ms%u\n",r.pid,r.kind,r.key,age))++shown;}
    }
    text.footer(total-shown,clipped||calls.saturated||state.saturated);
    return;

    }
    text.line("CDX16 quiet=%u gate=%x age=%u\n",(unsigned)quiet,state.gate,cdx15_ms(mach_absolute_time(),clipped));
    text.line("sub=? ipc=%u val=%u q=%u cp=%u ret=%u rej=%u\n",cdx15_cap(state.ipc,65535,clipped),
        cdx15_cap(state.val,65535,clipped),cdx15_cap(state.head,65535,clipped),cdx15_cap(state.copy,65535,clipped),
        cdx15_cap(state.ret,65535,clipped),cdx15_cap(state.reject,65535,clipped));
    text.line("F=?/%u/%u/%u/%u\n",cdx15_ms(state.first[1],clipped),cdx15_ms(state.first[2],clipped),
        cdx15_ms(state.first[3],clipped),cdx15_ms(state.first[4],clipped));
    text.line("L=?/%u/%u/%u/%u\n",cdx15_ms(state.last[1],clipped),cdx15_ms(state.last[2],clipped),
        cdx15_ms(state.last[3],clipped),cdx15_ms(state.last[4],clipped));
    text.line("vs=%u last=%u sub=? arm=%u late=%u\n",cdx15_cap(state.vsync,65535,clipped),
        cdx15_ms(state.lastVsync,clipped),(unsigned)state.armed,cdx15_cap(state.late,65535,clipped));
    text.line("vst=%u sa=%u ar=%u aa=%u sf=%x af=%x hz=%u\n",pacing.startReason,
        cdx15_cap(pacing.startAttempts,65535,clipped),pacing.armReason,cdx15_cap(pacing.armAttempts,65535,clipped),
        pacing.startFlags,pacing.armFlags,pacing.hz);
    if(activeLegacyDisplay){OSData *data=OSData::withBytes(&pacing,sizeof(pacing));
        if(data){activeLegacyDisplay->setProperty("CDX16VsyncState",data);data->release();}}
    char tail[640]={};Cdx15Text rest(tail,sizeof(tail));
    if(lateValid){rest.line("late=%llx last=%llx eq=%u\n",(unsigned long long)late.hash,
        (unsigned long long)last.hash,(unsigned)!cdx14_sample_diff(late,last));
        rest.line("latepx=%08x lastpx=%08x f=%u\n",late.pixels[0],last.pixels[0],cdx15_cap(seq,65535,clipped));}
    else rest.line("late=skip quiet=%u valid=%u map=%u\n",(unsigned)quiet,(unsigned)targetValid,(unsigned)mapValid);
    rest.line("wd=%d:%.16s aks=%d:%.16s\n",watchdog,wd,keyStore,aks);
    rest.line("wdAlt=%d:%.16s\n",alternate,alt);rest.lines(daemon);
    unsigned shown=0,total=0;
    for(const auto &c:state.clients)if(c.serial)++total;
    for(const auto &c:state.clients)if(c.serial && shown<4){
        char row[88]={};int n=snprintf(row,sizeof(row),"cli p=%u t=%x rc=%x n=%u %.16s\n",c.pid,c.type,c.status,
            cdx15_cap(c.validated,65535,clipped),c.name);
        if(n>0 && n<88 && text.used+(size_t)n+rest.used+90<capacity){text.line("%s",row);++shown;}
    }
    text.line("unk=%u linked=%u lost=%u\n",cdx15_cap(state.unknown,65535,clipped),cdx15_cap(state.linked,65535,clipped),
        cdx15_cap(state.drop,65535,clipped));text.lines(tail);
    text.dropped+=rest.dropped;text.footer(total-shown,clipped||state.saturated);
}
