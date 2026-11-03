# Stage21: copied stackshot owner relations, 2026-11-04

Local implementation and checks pass. Full macOS kernel link and device validation
are pending. This is a diagnostic candidate, not a desktop/display fix.

## Purpose and bounded scope

Stage20 photographed lsd worker TID 0x2b0 waiting on an unfair-lock owner 0x255.
These IDs are evidence from that boot only. Stage21 finds actual owners in each
new copied snapshot instead of hardcoding 0x255 or treating an IPC name as a TID.

The existing two system snapshots are retained, 15 seconds apart after each
capture completes. Capture occurs before display quiesce and diagnostic locks.
The original successful kcdata is saved in CDX19Raw0/1; original target state is
saved in CDX19State0/1. New copied relations are saved in CDX21State0/1.
All properties are RAM only. No working extraction transport is supplied:
export=0 is deliberate, and reboot loses this data. save=1 means property write
succeeded, not that an artifact was downloaded or that its relations are valid.

Relations21.h creates a 1,024-entry global thread identity index, 24 owner slots,
up to 256 turnstiles and 64 port labels. A separate bounded scan can locate owners
beyond the retained index; index overflow is reported. Each owner records task
unique ID, pid/comm/TID, wait fields, first waiter, provenance, up to 32 user LRs
and 4 kernel LRs. At most three dependency-expansion passes occur. New unresolved
requests at the limit remain unavailable, with dep=1. This is not deadlock proof.

Root waits are selected from up to 8 ranked threads per target, lsd slots first,
then SpringBoard, backboardd and launchd. Other target threads remain in raw kcdata.
More than two lsd instances suppress the ambiguous lsd interpretation. Instance
slots follow task order; they are not launchd domains or identities across boots.

Only UserLock owner values and explicitly THREAD-flagged turnstile contexts are
joined as TIDs. Owner.source is a bit mask: 1 = ulock owner, 2 = turnstile THREAD.
Deduplicated sources combine as 3. Duplicate TID matches suppress attribution.
PortReceive owner is a local name, PortSend can be a receiver PID, transit values
are opaque. These are preserved, never cast to owner TIDs. Special sentinels and
workqueue/locked/task turnstile contexts are not joined. Labels are retained with
their source domain and name; no remote receiver is inferred when not provided.

No launchd job-state channel is available; jobs=? means unavailable, not failed.
No thread is unlocked, no reply/completed ID is fabricated, and no database is
deleted. Display/backend ABI and subscription semantics remain the accepted ones.

## First runtime page

Retain Stage20's accepted CPU-present, refresh, console handoff, p26 and snapshot
carrier settings in both inner and outer representations. Set additionally:

```text
luming-display-snapshot=1
luming-display-stackshot=1
luming-display-stack-page=5
luming-display-stack-owner=0
luming-display-stack-frame=0
luming-display-stack-step=0
```

Page 5 prints CDX21, five target main-prioritized wait summaries, both sample
timestamps/parse/relations/save/overflow/depth statuses, and selected owner
pid/TID/wait-kind/source plus two user LRs. Each target row contains sample0/1
pids, numeric wait kinds, and hexadecimal owner values. Numeric wait kind meanings
are as above. Same thread rank does not establish same TID or task unique ID.

owner=0..23 selects a slot in each snapshot; compare printed TIDs, not slot number.
Missing frame or slot explicitly prints unavailable; a final single LR ends /end.
frame=0..28 selects a two-LR window. Full retained owner stacks remain in State.
Page 5 ignores stack-thread and stack-step. Pages 0..4 remain compatible detailed
target views (BB/SB/launchd/lsd1/lsd2) and retain stack-thread/frame/step selection.
Selecting those pages needs only a carrier repack, not a new kernel.

The outer intentional panic still says CDX19, for integration compatibility;
page5 body must say CDX21. Old detailed pages must show rev=21. It is an intentional
observation endpoint. A missing exit record never establishes daemon health.

The 820-byte page passes max-width test data without dropped rows, <=88 chars per
line. Omitted target threads, other owner slots, index/turnstile/label overflow are
reported in the footer. The screen is a subset: it does not show every waiter,
all owner dependencies, all raw arrays or all service labels simultaneously.

## Build integration and checks

Use accepted Stage18 r2 device commit 1ff0191689395552bb047ec5dde2a34be73fc203 as
the parent. Pin UniXNU 33da81310819b86d3ea62cb704f156c56407764a, 21H461, Intel
macOS and Xcode 16.4. Archive prefix device/stage19 and script names remain for
the existing CI chain: this package replaces that final diagnostic layer.
Do not run the Stage19 integration script over an already integrated Stage20 tree.

Copy archive stage19/ into the accepted device checkout, then from its parent:

```sh
python3 device/stage19/integrate_ci19.py --repo device
python3 device/stage19/integrate_ci19.py --repo device --apply
```

The installers verify Stage18 source input pins and seven fixed XNU source files
before materializing Stage21. runtime/ is a reference only: do not overwrite the
Stage10 inputs with it before running the ordered installers. CI must retain all
old source/ABI gates, direct source-API call qualification, and CDX21 marker checks.
Use a new branch and set both workflow ref and device_ref to it. One dispatch,
no automatic retries or device actions from the CI job.

Host checks: malformed/truncated model tests, typed owner/sentinel/task-order/
duplicate/missing/overflow/cycle/depth/turnstile/label tests, page capacity and
missing-frame tests, prior Stage15-18 regressions, ARM64 GPR-only compilation,
local stack-frame ceiling, 11 workflow Python blocks, and linked-call negative
fixtures. An oversized aggregate initializer was replaced by direct memset to
static state; local max function stack is recorded in validation.json.
These are not a full macOS link or hardware result. Existing skeleton baseline
remains 142 pass / 7 missing / 4 warn / 1 pre-existing missing-workflow error.

Return complete kernel/build/prelink and stage19 source/install/kernel reports,
plus preserved earlier gate reports, commit and run URL. Qualify the downloaded
kernel against the exact original cache before super packing. Check inner/outer
options, new kernel hash and archive contents. Flash only a qualified matching
image and accepted temporary control boot, using the existing device procedure.
Do not overwrite userdata merely because it existed in an earlier test: verify
the current installed Android/iOS state and intended userdata image first.

Acceptance for this round is a typed, symbolizable owner relation with matching
sample/task identity, or an explicit unavailable result. It is not a promise
that a certain number of later builds will produce the desktop.
