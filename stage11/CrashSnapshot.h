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
