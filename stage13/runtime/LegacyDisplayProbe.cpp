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
    if(option("luming-display-console-handoff")!=1)return true;
    if(__atomic_load_n(&consoleOwnership,__ATOMIC_ACQUIRE)==2)return true;
    unsigned empty=0;
    if(!__atomic_compare_exchange_n(&consoleOwnership,&empty,1,false,
        __ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE))return false;
    // Public platform console lifecycle; never write the console's private
    // state or video vtable. The panic path can still reacquire the screen.
    PE_initialize_console(nullptr,kPEReleaseScreen);
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
    return cdx13_publish_ui_scale(width,height);
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
void native_legacy_swap_validation_observed(bool accepted,unsigned reason,const void *,const void *) {
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
void native_legacy_transfer_observed(IOReturn status,const void *,uint64_t bytes) {
    native_legacy_transfer_calls=native_legacy_transfer_calls+1;native_legacy_transfer_status=status;native_legacy_transfer_bytes=bytes;
    if(native_legacy_transfer_calls<=8)
        IOLog("CDX_DISP copy status=%x bytes=%llu\n",(unsigned)status,(unsigned long long)bytes);
}
void native_legacy_retirement_observed(IOService *) {native_legacy_retirement_calls=native_legacy_retirement_calls+1;}
void native_legacy_vsync_observed(unsigned event,unsigned) {
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
