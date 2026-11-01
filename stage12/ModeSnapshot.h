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
