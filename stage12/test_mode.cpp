#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
static uint64_t fixture[8];
static int copy_error,copy_calls;
extern "C" int copyin(uint64_t address,void *destination,size_t length) {
    assert(address==0x1008 && length==64); ++copy_calls;
    if(copy_error)return copy_error;
    memcpy(destination,fixture,length);return 0;
}
#include "ModeSnapshot.h"
int main() {
    fixture[0]=1220;fixture[1]=2712;fixture[2]=2;
    fixture[3]=0;fixture[4]=0x404e000000000000ULL; // raw IEEE double 60.0
    fixture[5]=0;fixture[6]=0;fixture[7]=0;
    char out[1024]="old panic";
    cdx12_capture_mode(26,1);assert(copy_calls==0);
    cdx12_capture_mode(26,0x1000);
    cdx12_append_mode_summary(26,out,sizeof(out));
    assert(strstr(out,"got=1 err=0 busy=0"));
    assert(strstr(out,"w=1220 h=2712 pref=2 rot=0"));
    assert(strstr(out,"rateBits=404e000000000000"));puts(out);
    // Reject failed copies without exposing values from a previous PID/read.
    copy_error=14;cdx12_capture_mode(77,0x1000);out[0]=0;
    cdx12_append_mode_summary(77,out,sizeof(out));
    assert(strstr(out,"got=0 err=14") && strstr(out,"w=0 h=0"));
    out[0]=0;cdx12_append_mode_summary(26,out,sizeof(out));
    assert(strstr(out,"got=0 err=-1"));
    cdx12_lock=1;out[0]=0;cdx12_append_mode_summary(77,out,sizeof(out));
    assert(strstr(out,"got=0 err=-1 busy=1"));cdx12_lock=0;
    char bad[8];memset(bad,'x',8);cdx12_append_mode_summary(77,bad,8);assert(!bad[7]);
    char tiny[2]={0,1};cdx12_append_mode_summary(77,tiny,2);assert(!tiny[1]);
    puts("PASS: exact 64-byte copy, error/PID isolation, raw float bits, contention, bounded output");
}
