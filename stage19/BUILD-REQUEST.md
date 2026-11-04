# Stage22: typed lsd owner chain, 2026-11-04

Diagnostic candidate. Local host/ARM checks pass; macOS link/hardware pending.
Stage21 observed an lsd SleepWithInheritor -> SpringBoard -> kernel mutex edge
in one sample. Owner array slots changed identity; never join by slot number.

Relations21.h now joins verified TID owners for kinds 1 (mutex), 10 (user lock),
18 (sleep with inheritor). Pin lock_mtx.c and locks.c plus seven previous files.
Source bit 1 = direct typed TID wait; bit 2 = THREAD-flagged turnstile inheritor.
Receive names, send PIDs, opaque values/sentinels are never cast to owner TIDs.
Duplicate TID matches suppress identity. No live private task/thread pointer reads.

Page6 selects a typed root from eight retained ranked threads of one lsd instance,
ordered by kinds 18,10,1. Follow direct TID edges independently in each sample.
Stop on non-TID, ambiguity, absent identity, cycle or retention limit. No turnstile
fallback on page6. Relations keep 1024 identity entries, 24 owners, three passes.
Owners outside retained identity index can still be located by copied-data scan.
Depth-limited new requests stay unavailable. This is not an exhaustive graph.

Rows: CDX22 header; S0/1 timestamp/parse/relations/overflow/depth; R0/1 root pid,
TID/kind/owner; O0/1 owner pid/TID/next wait; N0/1 comm prefix (8 chars), task
unique ID/provenance; K0/1 continuation and first two kernel LRs; U0/1 user LRs.
Kernel stack may be absent after continuation stack discard: report unavailable.
No suspend, forced fault-in, unlock, fake completion, forced vsync, daemon BRK
bypass or database changes. Backend/generator/display ABI remain unchanged.

Two captures remain 15 seconds apart before console quiesce. CDX19Raw0/1,
CDX19State0/1, CDX21State0/1 are RAM-only. No working export or launchd job-state
channel. Property saved is not artifact downloaded; no exit record is not health.

## Carrier options, inner and outer
Preserve accepted CPU-present, refresh, handoff and diagnostic carrier settings.

```text
luming-display-snapshot=1
luming-display-stackshot=1
luming-display-stack-page=6
luming-display-stack-step=0
luming-display-stack-thread=0
luming-display-stack-owner=0
luming-display-stack-frame=0
```

step=0/1 chooses lsd instance, not domain. thread=0..7 chooses typed root ordinal.
owner=0..23 chooses the nth owner along this root's typed chain (0 = direct owner,
1 = its holder); frame=0..28 chooses a two-LR user window. Compare identities
across samples, not root rank or slot number. Other options require carrier repack,
not rebuild. Page5/detailed0..4 preserved; detailed rev22; outer intentional panic
remains CDX19. Page6 must say CDX22. This is an intentional observation endpoint.

## Build and qualification
Accepted parent 1ff0191689395552bb047ec5dde2a34be73fc203 (Stage18r2).
UniXNU 33da81310819b86d3ea62cb704f156c56407764a, 21H461, Intel macOS/Xcode16.4.
Archive prefix stage19/ and script names are compatibility names. Integrate on
accepted Stage18 inputs, not an already integrated Stage21 tree.

```sh
python3 device/stage19/integrate_ci19.py --repo device
python3 device/stage19/integrate_ci19.py --repo device --apply
```

Local: check19.py, preflight_ci19.py, test_linked19.py, pack19.py. Checks cover
18->1 typed chain in reverse task order, duplicates/sentinels/missing identities,
cycles, overflow, bounded passes, root/hop selection, unavailable frames, maximum
width page, prior Stage15-18 regressions, ARM64 GPR-only and stack-frame ceiling.
These checks do not constitute full kernel linking or runtime success.

CI retains prior gates, nine exact XNU pins, unchanged backend/generator/ABI and
exact linked API call gate. Require CDX22 plus old markers. Return full build,
prelink, kernel/install/source reports with run/commit. One dispatch, no automatic
retry or CI device action. Verify all downloaded assets, workflow/source hashes,
original cache ABI and panic window before packing. Flash qualified super and
accepted temporary control boot. Userdata needs current restoration requirement.
