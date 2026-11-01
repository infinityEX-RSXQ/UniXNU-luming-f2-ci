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
