# Stage18 — original wait / completion correlation

2026-11-02. Source diagnosis, not a desktop-rendering fix. Base: accepted Stage17
run 41402982992, commit 0c83eed41012d3bbd2a8e05fca5101bdb6f5a6be.

Original kernelcache SHA256:
`f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7`.
All offsets below are [measured] from that original, independently disassembled
in `original-wait-guards.json`; raw addresses explicitly convert by -0x1000000
at prelink. No original instruction or user-client vptr is modified.

## Why this experiment

Selector 6 is 3 scalar inputs / 0 outputs in the original dispatch table.
Observed `1 / 80000000 / 0` means swap ID 1, mode 0, nonblocking, timeout 0.
Busy can be the correct result. Prior counters cannot pair last arguments and
last return, nor tell whether the original completed ID advanced.

The sole newly owned virtual entry is slot 176, ABI:
`IOReturn(self, IOUserClient*, uint32_t id, uint32_t flags, uint32_t timeout)`.
The override always calls the exact original parent through a typed C alias, returns its actual status,
and retains the same arguments. Off by default. The 358-entry layout and 0x18a0
base extent remain guarded. The generated header's expected new SHA is recorded
in `expected-abi.json`; this is a qualified prototype, not a replacement binary.

2026-11-03 revision: full Intel CI run 41540053855 compiled the driver but rejected
the new import set. Reproduced locally: `-fapple-kext` emits a qualified parent
virtual call through the original base vtable, not the named C++ method symbol.
The initial extra method binding was therefore unused. This revision explicitly
binds `_cdx18_original_wait` to slot176's unchanged function and
`_cdx18_original_complete` to slot295's unchanged function. The latter is used
only for recorded completions; the existing path remains for other completions.
Both aliases are independently byte-guarded and checked in the final report and
linked call sequences. The original import equality check is retained, with
missing/unused names in its failure message. A new ARM64 `-fapple-kext -mkernel`
fixture catches the direct-alias distinction before full CI.

## Runtime

Add `luming-display-wait-probe=1` to both matching inner and outer boot configs.
Keep Stage17 controls, including CPU present, refresh=60, p26 and snapshot/handoff.
The existing outer panic banner still says CDX17; its body must begin **CDX18**.
Without the new argument, the existing Stage17 pages remain selectable.

Each wait has a unique token; overlapping calls complete their own record.
Capacity: 16 waits, 8 completions, no overwrite; lost/unmatched/saturation explicit.
Known client identity supplies PID; PID 0 is unknown. No guessed current_proc.
Snapshots are boundary samples before/after the original function, **not** the
exact branch-decision sampling instant. Diagnostic reads can affect timing.

Provider fields, read only while the family's work-loop gate is held:
completed ID at +0x16bc; current/queue head pointer presence at +0x1560/+0x1568.
Before original completion, read live request ID +0x314 and raw word +0x32c.
After original completion, never dereference the request. Raw +0x32c is unnamed;
do not treat it as an error code or write it to force completion.
The added spinlock protects value records only: no IOKit calls/runAction inside.

## Short-line legend

```text
CDX18 quiet=1 cp=2 ret=2 waits=3 done=2
lost=0 unmatched=0 seq=5 boundary-samples
D1 i=1 x=0 d=1 v=1/1 c=0/1
W2 p58 i=1 f=80000000 t=0 r=e00002d5 d=1
W2 v=1/1 c=2/2 h=0/0 q=0/0
omit=0 drop=0 clip=0
```

Example values above are illustrative, **not device evidence**.
Tokens, i(request ID), x(raw32c), f(flags), t(timeout), r(return), c(completed IDs)
are hexadecimal. PID and counts are decimal. d=1 means the observed call returned;
v=1/1 means both samples valid; h/q are only current/queued pointer presence.
v=0 means unavailable; zero fields then carry no state claim.
Two W lines match by token. Missing rows are counted; complete bounded tables are
also published as `CDX18WaitState`. Total body <660 bytes, lines <=88 bytes.

## Acceptance and interpretation

Host checks rerun Stage15–17 adapters and test paired overlap, unknown owners,
overflow, output limits, no post-completion request reads, disabled passthrough,
gate reads, ARM64 GPR-only code. These are interface/model tests, not full XNU.
Full CI must preserve prior regression checks, match final source hashes and
exact generated ABI, check all original bytes, and independently verify linked
wait begin -> original parent -> end and completion begin -> parent -> end.

- Completion post ID equals request ID and corresponding wait succeeds: that
  handshake works; collect user-state stacks/readiness next.
- Completion post ID does not advance: inspect the original branch/state with
  the paired raw request word; do not write the completed ID directly.
- Polling an old ID returns Busy: not enough evidence for a protocol change.
- No selector72 observed: do not synthesize subscriptions or force a timer.

Current source/host status is `validation.json`. Full CI result and actual test
image hashes belong in the separate delivery evidence. No claim of UI success
or of hardware execution follows from source/host checks alone.
