# Stage19.3 - SpringBoard IPC stack diagnostics, 2026-11-03

Stage19.2 photo09:54: sample0 API succeeded but parser failed with error12.
Sample1 SpringBoard pid26 main tid0x126 waits on a Mach port. Continuation
fffffff00726222c is ipc_mqueue_receive_continue in the actual f4a2d2fd kernel.
wait_type2 means port receive. owner1e03 is a receiver port NAME, not server PID.
User LRs 1cb780b58/1cb7841b0 are IPC stub/wrapper. Higher callers and specialreply
flag were not shown. No particular failed service or GPU/vsync wait is proven.

Changes only owned diagnostics installed over accepted Stage18r2 baseline
1ff0191689395552bb047ec5dde2a34be73fc203, using existing Stage19 CI integration.
Backend/generator, 358-slot ABI, original selectors/wait/completion unchanged.
No fake service or successful return is added. This is not a desktop fix.

- Separate tasks sharing a comm name mark that name slot ambiguous, print PIDs
  and count, and never show its thread or merge tasks. Other slots still parse.
  Repeated task_snapshot records in ONE scope remain malformed (error24).
- Retain four kernel and eight user LRs with original counts. Print continuation
  and four user LRs; kernel frames remain in State. No live task traversal.
- Decode v2 wait_flags / signed portlabel_id at pinned offsets27/25. For v1
  25-byte record print f=? l=?; never pretend those fields were available.
  f&1 means specialreply; a label ID is not a decoded service name.
- luming-display-stack-frame=0 prints LRs0..3; =4 prints LRs4..7. Page0 BB,
  page1 SB, page2 launchd; thread ranks0..7. Summary begins CDX19 rev=3.
  Still <=820 bytes, <=88 columns, explicit omission/drop footer, raw only RAM.
- Same default-off two source-kernel captures before quiesce, 15s apart.

Host checks: same-comm task ambiguity, duplicate record in one scope, v1/v2
flags and signed labels, eight-user/four-kernel bounds, frame paging, ambiguity
suppression, Stage15-18 regressions, ARM64 GPR-only compilation and linked call
positive/negative tests. Full Mac build and hardware result remain pending.

First test: qualified Stage19.2 config, page1/thread0/frame0, diagnostic native
panic_on_crash_disabled=1 window. Preserve initproc panic; watchdog is not fixed.
No userdata flash unless Android has overwritten it. Independently qualify the
CI artifacts, private hash chain, ABI/API and J2/FAT/config before flashing.
