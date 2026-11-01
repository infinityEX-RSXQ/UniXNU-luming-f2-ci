#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "CrashSnapshot.h"
extern "C" {
volatile uint32_t native_legacy_stage=10, native_legacy_failure;
volatile uint32_t native_legacy_registration_calls=1, native_legacy_client_calls=1;
volatile int native_legacy_client_status=0;
volatile uint32_t native_legacy_swap_validation_calls, native_legacy_swap_validation_result;
volatile uint32_t native_legacy_swap_validation_reason, native_legacy_transfer_calls;
volatile int native_legacy_transfer_status=-1;
volatile uint32_t native_legacy_retirement_calls, native_legacy_vsync_count;
}
int main() {
    char out[640];
    assert(!cdx11_crash_summary(26,"launchd","old",out,sizeof(out)));
    cdx11_capture_exception(26,"other",6,1,0x123,0,1);
    cdx11_crash_summary(26,"SpringBoard","old",out,sizeof(out));
    assert(strstr(out,"match=0"));
    // A restarted SpringBoard above the PID filter is still retained.
    cdx11_capture_exception(812,"SpringBoard",6,1,0x19f3df2ecULL,0,1);
    cdx11_capture_exception(812,"SpringBoard",10,0xdead,0xbeef,1,0);
    cdx11_crash_summary(812,"SpringBoard","SpringBoard[812] exited",out,sizeof(out));
    assert(strstr(out,"match=1 busy=0 n=1"));
    assert(strstr(out,"last e=6 off=1 sl=0 c0=1 c1=19f3df2ec"));
    assert(strstr(out,"reg=1 cl=1 rc=0") && strstr(out,"val=0 ok=0 why=0 cp=0 rc=ffffffff"));
    puts(out);
    cdx11_capture_exception(812,"SpringBoard",1,2,0xfeed,0x4000,0);
    cdx11_crash_summary(812,"SpringBoard","old",out,sizeof(out));
    assert(strstr(out,"first e=6 c0=1 c1=19f3df2ec"));
    assert(strstr(out,"last e=1 off=0 sl=4000 c0=2 c1=feed"));
    // Contention never spins and is explicit; no stale exception is shown.
    cdx11_lock=1;
    cdx11_capture_exception(812,"SpringBoard",6,1,0x999,0,1);
    cdx11_crash_summary(812,"SpringBoard","old",out,sizeof(out));
    assert(strstr(out,"match=0 busy=1 n=0 drop=1"));
    cdx11_lock=0;
    cdx11_crash_summary(813,"SpringBoard","old",out,sizeof(out));
    assert(strstr(out,"match=0"));
    cdx11_capture_exception(813,"SpringBoard",6,1,0xaaa,0,1);
    cdx11_crash_summary(813,"SpringBoard","old",out,sizeof(out));
    assert(strstr(out,"n=1") && strstr(out,"first e=6 c0=1 c1=aaa"));
    // Missing exception data is always labelled rather than treated as c1=0.
    char tiny[8]; memset(tiny,'X',sizeof(tiny));
    assert(cdx11_crash_summary(813,"SpringBoard","long-prefix",tiny,sizeof(tiny)));
    assert(tiny[7]==0);
    puts("PASS: name/PID isolation, secondary notification, first/last, contention and bounded formatting");
}
