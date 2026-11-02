# Stage17 — display IPC observation

Base: successful Stage16 CI run 41387339589, device commit e9e2476180b289d6702afc875e3cad38a6331959.
Install after all existing Stage10–16 installers:

```
python3 stage17/install_stage17.py --device . --apply
```

The installer pins the Stage16 probe/backend and Stage15 core patch. It adds a separate, later source patch to `iokit/Kernel/IOUserClient.cpp`. Existing prelinked dispatch, return values, ipcEnter/ipcExit and scheduling remain unchanged. No object vptr replacement, new hardware claims, original instruction patch or fabricated service.

CI: branch stage17-ipc-cdx-20261102. First run 41392987254 compiled the kernel but failed in the post-build checker due to a Python variable-shadowing error. Second run 41395331565 passed the previous checks but correctly failed the new linked-call guard: the new source patch had not been added to the explicit XNU patch series. Both are rejected test candidates. The final installer pins and updates that series, with an explicit host test and linked-code checks. Take the accepted run/commit and full-kernel status from the separate delivery report, not the host-only validation JSON.

## What is measured

- Only user clients previously opened through our provider are observed. PID is the client owner's task PID; a transferred connection's current caller identity is not asserted.
- Per-client sparse counters persist across the Stage15 event ring wrapping: selector, entries, returns, nonzero returns and last returned status. At most 64 rows/32 active calls; loss and saturation are explicit.
- Source XNU's 32-bit and 64-bit notification-port RPCs are observed before ipcEnter and after ipcExit. No prelinked registerNotificationPort/externalMethod replacement. No port kernel pointer is printed; `b` means the last supplied port was non-null, not that registration succeeded.
- Selector 6 and 72 capture only the first 0..3 kernel-marshalled scalar input values, plus input/output counts. No structure/pointer dereference, retained args pointer or claimed scalar semantics.
- A pending call entered the wrapper but has not reached the after-ipcExit hook. It could be waiting on the IPC lock, in the method or otherwise suspended. This alone does not prove a GPU wait.
- Scalar values are from the last begun call, last status is from the last returned call; concurrent calls need not be the same one. Read only the `got` elements; uncaptured trailing array slots have no meaning.

## Snapshot pages

Default `luming-display-ipc-page=0` (no argument required):

```
CDX17 pg=0 quiet=1 cp=... ret=...
ipc=... end=... err=... loss=... vst=... ar=... vs=...
pending=... portRPC=... rows=...
p58 s6 n... d... f... r... b0
p58 P5 n... d... f... r... b1
omit=... drop=... clip=...
```

`s` is an external selector; `P`/`Q` are 32/64-bit port RPC notification types.
`n`=begun, `d`=returned, `f`=nonzero-return count, `r`=last returned status in hex.
Zero `portRPC` means no such RPC observed on known clients, **not** no async selector registration.

Page 1 prints selector 6/72 counts and up to three input scalars plus pending row/age.
Page 2 preserves the complete Stage16 summary and pacing property. All pages retain the existing deliberate delayed panic; `<700B` panic payload and `<=88` characters per line. On pages 0/1, `CDX17IPCState` retains the full bounded record table; `CDX15TraceState` is also published. Stage16 pacing reasons/counters are read from the same unchanged observation state.

## Local validation

`check17.py` preserves and reruns Stage15/16 model/adapter tests, and adds known-client filtering, independent method/port tokens, error/success returns, pending calls, bounded scalar buffers, null input, table/full-active loss, saturated counters and text limits. It also applies the generated core patch after Stage15, strips only observer additions and compares the entire original XNU source for unchanged locks/dispatch/returns. ARM64 interface fixture is GPR-only. This is not a substitute for macOS full-kernel CI or hardware tests.

CI must preserve the previous regression checks, follow the Stage16→17 source-hash chain and run `ci_check17.py`. Independent acceptance uses `qualify_stage17_kernel.py`: source hashes, original ABI/358 entries, original kernelcache identity and ordered direct observer calls in all three linked XNU wrappers. Do not accept a kernel on strings alone.

Repack only the two kernel members of verified Stage16 super, keeping the existing p26/cpu-present/snapshot/control-boot configuration. Do not modify boot slots or Android partitions. Hardware validation is a separate step after full CI and image integrity checks.
