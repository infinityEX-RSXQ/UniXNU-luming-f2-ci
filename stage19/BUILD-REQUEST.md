# Stage19.4: identify the synchronous XPC caller, 2026-11-03

Stage19.3 photo10:54 has two parsed SpringBoard pid27 main-thread snapshots,
15s apart, both at ipc_mqueue_receive_continue, wait_type2 and SPECIALREPLY flag1.
User frames4..7 are libdispatch, xpc_connection_send_message_with_reply_sync+0x100,
Foundation trampoline and -[NSXPCConnection _sendInvocation:orArguments:count:
methodSignature:selector:withProxy:]+0x7e8. No service/method identity or desktop
root cause established; receiver name1e03 is NOT a PID. No GPU/vsync attribution.

Retain32 user LRs, original count preserved, kernel bound remains4. Display4 per
sample. Optional luming-display-stack-frame (0..28) and luming-display-stack-step
(0..28) select sample0 offset=frame and sample1=min(frame+step,28). Defaultstep0
retains identical windows. First candidate: page1/thread0/frame8/step4, to see
LR8..11 in S0 and LR12..15 in S1. Distinct sample offsets always printed.

Owned diagnostics only, original API/ABI/display/selectors unchanged. No live
thread access or suspension, fake success, watchdog fix or GPU implementation.
Same-name ambiguity/old waitinfo handling retained. Defaultoff and two samples
before quiesce remain. Frame count/short input/bounds/step overflow/line budget
and Stage15-18 regressions are host gates. Exact Intel link and qualification
required before super + temporary control boot. No userdata overwrite.
