#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#include <atomic>
#include <thread>
#include <chrono>
static unsigned sleeps;
static std::atomic<bool> releaseWriter{false};
static bool releaseOnSleep;
static void IOSleep(unsigned) {
    ++sleeps;if(releaseOnSleep && sleeps==2)releaseWriter=true;
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
}
#include "ScanoutQuiesce.h"
struct Lease {
    bool held=cdx14p1_scanout_enter();
    ~Lease(){if(held)cdx14p1_scanout_leave();}
};
static void early_return(){Lease l;assert(l.held);}
int main(){
    early_return();assert(!cdx14p1_writers);
    std::atomic<bool> entered{false};releaseOnSleep=true;
    std::thread worker([&]{Lease l;assert(l.held);entered=true;while(!releaseWriter.load())std::this_thread::yield();});
    while(!entered.load())std::this_thread::yield();
    assert(cdx14p1_quiesce());worker.join();
    assert(!cdx14p1_writers && sleeps>=2 && !cdx14p1_scanout_enter());
    __atomic_store_n(&cdx14p1_frozen,0,__ATOMIC_SEQ_CST);releaseOnSleep=false;sleeps=0;
    assert(cdx14p1_scanout_enter());assert(!cdx14p1_quiesce());assert(sleeps==100);
    assert(cdx14p1_writers==1);cdx14p1_scanout_leave();assert(!cdx14p1_writers);
    puts("Stage14.1 quiesce: in-flight drain, RAII return, freeze refusal, bounded timeout PASS");
}
