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
static thread_call_t cdx14_snapshot_call;
static void cdx14_snapshot_callback(thread_call_param_t,thread_call_param_t) {
    char daemon[512]={},exceptions[512]={};cdx14_daemon_summary(daemon,sizeof(daemon));
    cdx14_exception_summary(exceptions,sizeof(exceptions));
    cdx14_console_snapshot(cdx14_frame.console);
    panic("CDX14 diagnostic snapshot (intentional)\n"
        "f=%llu sampled=%u blank=%u valid=%u src=%llx dst=%llx\n"
        "mismatch=%u mutate=%u between=%u pixels=%x/%x grid36=%x/%x\n"
        "VT own=%u enabled=%u disabled=%u blocked=%u drawn=%u\n"
        "validate=%u result=%u copy=%u rc=%x bytes=%llu retire=%u vsync=%u\n%s%s",
        (unsigned long long)cdx14_frame.sequence,cdx14_frame.sampled,cdx14_frame.blankCount,cdx14_frame.valid,
        (unsigned long long)cdx14_frame.srcHash,(unsigned long long)cdx14_frame.dstAfter,
        cdx14_frame.copyMismatch,cdx14_frame.sourceChanged,cdx14_frame.betweenMismatch,
        cdx14_frame.srcFirst,cdx14_frame.dstFirst,cdx14_frame.srcGrid36,cdx14_frame.dstGrid36,
        cdx14_frame.console[0],cdx14_frame.console[1],cdx14_frame.console[2],cdx14_frame.console[3],cdx14_frame.console[4],
        native_legacy_swap_validation_calls,native_legacy_swap_validation_result,native_legacy_transfer_calls,
        (unsigned)native_legacy_transfer_status,(unsigned long long)native_legacy_transfer_bytes,
        native_legacy_retirement_calls,native_legacy_vsync_count,daemon,exceptions);
}
extern "C" void cdx14_after_release(void) {
    if(option("luming-display-vt-latch")==1)cdx14_console_commit();
    // Opt-in, independent delayed snapshot survives a stalled display work loop.
    if(option("luming-display-snapshot")==1 && !cdx14_snapshot_call) {
        cdx14_snapshot_call=thread_call_allocate(cdx14_snapshot_callback,nullptr);
        if(cdx14_snapshot_call) {
            uint64_t deadline;clock_interval_to_deadline(15,NSEC_PER_SEC,&deadline);
            thread_call_enter_delayed(cdx14_snapshot_call,deadline);
        }
    }
}
