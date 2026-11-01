// SPDX-License-Identifier: BSD-2-Clause-Patent
//
// Minimal kernel-side display provider bootstrap for UniXNU (SM8735 / iPadOS 17.7.11 21H461).
//
// Trimmed from the sheng reference package/MobileDisplayProviderProbe.cpp:
//   * no sheng board hooks: no kits/sheng, no IOPM/GPU/HID/touch includes, no
//     board-specific addresses other than the three fixed IOMobileFramebuffer
//     bindings that live in the archive (original-bindings.S), not here;
//   * keeps the probe entry point, the deferred own-constructor call, the
//     OSMetaClass::preModLoad/postModLoad registration and the volatile
//     observation variables a debugger / serial log reads back afterwards;
//   * every failure path records a stage and returns instead of panicking.
//
// Call site (already present in patches/xnu/offline-component-load-probes.patch,
// inside native_mobile_graphics_client_probe(), i.e. after the original
// IOMobileGraphicsFamily kext has registered its own classes):
//
//     #if defined(XNU_NATIVE_MOBILE_DISPLAY) && XNU_NATIVE_MOBILE_DISPLAY
//         extern void native_mobile_display_provider_probe(void);
//         native_mobile_display_provider_probe();
//     #endif
//
// Build contract (scripts/build-native-mobile-display.py):
//   - compiled with the IOPlatformExpert.cpo.json replay line of the XNU tree;
//   - NATIVE_MOBILE_DISPLAY_DEFER_INIT=1 links against the .late.o archive whose
//     __DATA,__mod_init_func was removed and whose own constructor was globalized
//     to NATIVE_MOBILE_DISPLAY_INIT_SYMBOL, so the probe can run it in order;
//   - NATIVE_MOBILE_DISPLAY_DEFER_INIT=0 keeps __mod_init_func (fallback mode).

#include <IOKit/IOService.h>
#include <IOKit/IOUserClient.h>
#include <IOKit/IOLib.h>
#include <libkern/c++/OSMetaClass.h>
#include <libkern/c++/OSSymbol.h>
#include <pexpert/pexpert.h>
#include <mach/kmod.h>

// The kernel's own kmod_info (libkern/c++/OSKext.cpp).  It is a definition of the
// source kernel we link into, not an original-kext import, so it always resolves.
extern "C" kmod_info_t g_kernel_kmod_info;

// clang emits the file's C++ static constructor as __GLOBAL__sub_I_<basename>.
// The builder globalizes exactly that symbol and passes its detected name here
// with -DNATIVE_MOBILE_DISPLAY_INIT_SYMBOL=... (see INTEGRATION.md, init order).
#ifndef NATIVE_MOBILE_DISPLAY_INIT_SYMBOL
#define NATIVE_MOBILE_DISPLAY_INIT_SYMBOL "__GLOBAL__sub_I_NativeMobileDisplay.cpp"
#endif
extern "C" void native_mobile_display_static_init(void)
    __asm__(NATIVE_MOBILE_DISPLAY_INIT_SYMBOL);

extern "C" IOService *native_mobile_display_create(void);

#ifndef NATIVE_MOBILE_DISPLAY_DEFER_INIT
#define NATIVE_MOBILE_DISPLAY_DEFER_INIT 1
#endif

#ifndef NATIVE_MOBILE_DISPLAY_PROBE_LOG
#define NATIVE_MOBILE_DISPLAY_PROBE_LOG 1
#endif

extern "C" {
// All of these survive in the kernel image after the probe returns: attach a
// debugger, read them back, or read the one-line serial summary below.
volatile uint32_t native_mobile_provider_stage;           // 0 never entered .. 5 queried
volatile uint32_t native_mobile_provider_done;            // re-entry guard
volatile int      native_mobile_provider_meta_status = -1;
volatile int      native_mobile_provider_query_status = -1;
volatile uint64_t native_mobile_provider_object;
volatile uint64_t native_mobile_provider_client;
volatile uint64_t native_mobile_provider_dimensions[2];
volatile uint64_t native_mobile_provider_expected[2];
volatile uint32_t native_mobile_provider_parent_match;    // provider->metaCast("IOMobileFramebuffer")
volatile uint32_t native_mobile_provider_released;
volatile uint64_t native_mobile_provider_parent_meta;     // original family metaclass, looked up by name
volatile uint64_t native_mobile_provider_own_meta;        // our metaclass, looked up by name
volatile uint32_t native_mobile_provider_super_match;     // own->getSuperClass() == parent
volatile uint32_t native_mobile_provider_client_init;
volatile uint32_t native_mobile_provider_client_attached;
volatile uint32_t native_mobile_provider_client_started;

void native_mobile_display_provider_probe(void);
// Not static on purpose: a debugger sets a breakpoint on
// _native_mobile_display_provider_checkpoint to read the variables below.
__attribute__((noinline)) void native_mobile_display_provider_checkpoint(void);
}

// Keep the compiler from folding the observation stores away.
__attribute__((noinline)) void
native_mobile_display_provider_checkpoint(void)
{
	__asm__ volatile("" ::: "memory");
}

void
native_mobile_display_provider_probe(void)
{
	// preModLoad() asserts that no other mod load is in flight, and postModLoad()
	// panics on a duplicate class registration: never run this twice.
	if (native_mobile_provider_done) {
		return;
	}
	native_mobile_provider_done = 1;
	native_mobile_provider_stage = 1;

	// 1. The original parent must already be registered.  If it is not, the
	//    IOMobileGraphicsFamily kext has not initialised yet (or is missing from
	//    the prelink roots): record it and leave without touching it.
	const OSSymbol *parentName = OSSymbol::withCStringNoCopy("IOMobileFramebuffer");
	const OSMetaClass *parentMeta = parentName
	    ? OSMetaClass::getMetaClassWithName(parentName) : nullptr;
	native_mobile_provider_parent_meta = (uintptr_t)parentMeta;
	if (!parentMeta) {
		native_mobile_display_provider_checkpoint();
		return;
	}

	// 2. Register our own metaclasses under the kernel's own kmod identity, exactly
	//    as OSRuntime does for statically linked code, then run our deferred
	//    constructor (late.o has __DATA,__mod_init_func removed).
	void *handle = OSMetaClass::preModLoad(g_kernel_kmod_info.name);
	if (!handle) {
		native_mobile_display_provider_checkpoint();
		return;
	}
#if NATIVE_MOBILE_DISPLAY_DEFER_INIT
	native_mobile_display_static_init();
#endif
	native_mobile_provider_meta_status = OSMetaClass::postModLoad(handle);
	if (native_mobile_provider_meta_status) {
		native_mobile_display_provider_checkpoint();
		return;
	}
	native_mobile_provider_stage = 2;

	// 3. Runtime check of the vendored ABI: our metaclass must descend from the
	//    original family metaclass.  A mismatch means the fixed bindings do not
	//    belong to this kernelcache; refuse before creating an object.
	const OSSymbol *ownName = OSSymbol::withCStringNoCopy("NativeMobileDisplay");
	const OSMetaClass *ownMeta = ownName
	    ? OSMetaClass::getMetaClassWithName(ownName) : nullptr;
	native_mobile_provider_own_meta = (uintptr_t)ownMeta;
	native_mobile_provider_super_match =
	    (ownMeta && ownMeta->getSuperClass() == parentMeta) ? 1 : 0;
	if (!native_mobile_provider_super_match) {
		native_mobile_display_provider_checkpoint();
		return;
	}

	// 4. Create the provider instance.
	native_mobile_provider_stage = 3;
	IOService *provider = native_mobile_display_create();
	native_mobile_provider_object = (uintptr_t)provider;
	if (!provider) {
		native_mobile_display_provider_checkpoint();
		return;
	}
	native_mobile_provider_parent_match =
	    provider->metaCast("IOMobileFramebuffer") != nullptr;

	PE_Video video = {};
	PE_current_console(&video);
	native_mobile_provider_expected[0] = video.v_width;
	native_mobile_provider_expected[1] = video.v_height;

	// 5. Ask the genuine original user client for the dimensions (selector 8).
	//    This is the only display operation this provider claims to support.
	OSObject *object = OSMetaClass::allocClassWithName("IOMobileFramebufferUserClient");
	IOUserClient *client = OSDynamicCast(IOUserClient, object);
	if (!client) {
		if (object) {
			object->release();
		}
		provider->release();
		native_mobile_provider_released = 1;
		native_mobile_display_provider_checkpoint();
		return;
	}
	native_mobile_provider_client = (uintptr_t)client;
	native_mobile_provider_client_init = client->init() ? 1 : 0;
	if (native_mobile_provider_client_init) {
		native_mobile_provider_client_attached = client->attach(provider) ? 1 : 0;
		if (native_mobile_provider_client_attached) {
			native_mobile_provider_client_started = client->start(provider) ? 1 : 0;
		}
	}
	if (native_mobile_provider_client_started) {
		uint64_t values[2] = { ~(uint64_t)0, ~(uint64_t)0 };
		IOExternalMethodArguments arguments = {};
		arguments.selector = 8;
		arguments.scalarOutput = values;
		arguments.scalarOutputCount = 2;
		native_mobile_provider_query_status =
		    client->externalMethod(8, &arguments, nullptr, nullptr, nullptr);
		native_mobile_provider_dimensions[0] = values[0];
		native_mobile_provider_dimensions[1] = values[1];
		native_mobile_provider_stage = 5;
	}

	if (native_mobile_provider_client_started) {
		client->stop(provider);
	}
	if (native_mobile_provider_client_attached) {
		client->detach(provider);
	}
	client->release();
	provider->release();
	native_mobile_provider_released = 1;

#if NATIVE_MOBILE_DISPLAY_PROBE_LOG
	kprintf("NativeMobileDisplay: stage=%u meta=%d super=%u init=%u attach=%u start=%u "
	    "query=%x dims=%ux%u expected=%ux%u\n",
	    (unsigned)native_mobile_provider_stage,
	    (int)native_mobile_provider_meta_status,
	    (unsigned)native_mobile_provider_super_match,
	    (unsigned)native_mobile_provider_client_init,
	    (unsigned)native_mobile_provider_client_attached,
	    (unsigned)native_mobile_provider_client_started,
	    (unsigned)native_mobile_provider_query_status,
	    (unsigned)native_mobile_provider_dimensions[0],
	    (unsigned)native_mobile_provider_dimensions[1],
	    (unsigned)native_mobile_provider_expected[0],
	    (unsigned)native_mobile_provider_expected[1]);
#endif
	native_mobile_display_provider_checkpoint();
}
