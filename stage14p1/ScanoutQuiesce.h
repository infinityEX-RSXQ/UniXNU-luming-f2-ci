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
